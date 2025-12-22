import os
import polars as pl
import unicodedata

from flask import request, jsonify

from . import bp
from ...services.items_service import search_items_df, get_item_full, get_stats_exit, get_stats_exit_monthly
from supplychain_app.items import Nomenclatures
from supplychain_app.constants import path_datan, folder_name_app, path_output
from supplychain_app.data.pudo_service import get_equivalents_for


@bp.get("/meta/feuilles_du_catalogue")
def list_feuilles_du_catalogue():
    """Retourne les valeurs distinctes de feuille_du_catalogue (pour alimenter les listes déroulantes)."""
    parquet_path = os.path.join(path_datan, folder_name_app, "items.parquet")
    if not os.path.exists(parquet_path):
        return jsonify({"values": []})

    try:
        df = pl.read_parquet(parquet_path, columns=["feuille_du_catalogue"])
        if "feuille_du_catalogue" not in df.columns:
            return jsonify({"values": []})
        values = (
            df.select(pl.col("feuille_du_catalogue").cast(pl.Utf8))
            .drop_nulls()
            .unique()
            .to_series()
            .to_list()
        )
        values = [str(v).strip() for v in values if str(v).strip()]
        values = sorted(set(values), key=lambda s: s.upper())
        return jsonify({"values": values})
    except Exception:
        return jsonify({"values": []})


@bp.get("/meta/fabricants")
def list_fabricants():
    """Retourne les valeurs distinctes de nom_fabricant depuis manufacturers.parquet."""
    parquet_path = os.path.join(path_datan, folder_name_app, "manufacturers.parquet")
    if not os.path.exists(parquet_path):
        parquet_path = os.path.join(path_datan, folder_name_app, "manufacturer.parquet")
        if not os.path.exists(parquet_path):
            return jsonify({"values": []})

    try:
        df = pl.read_parquet(parquet_path, columns=["nom_fabricant"])
        if "nom_fabricant" not in df.columns:
            return jsonify({"values": []})
        values = (
            df.select(pl.col("nom_fabricant").cast(pl.Utf8))
            .drop_nulls()
            .unique()
            .to_series()
            .to_list()
        )
        values = [str(v).strip() for v in values if str(v).strip()]
        values = sorted(set(values), key=lambda s: s.upper())
        return jsonify({"values": values})
    except Exception:
        return jsonify({"values": []})


def _norm_txt(v: str) -> str:
    s = (v or "").strip()
    if not s:
        return ""
    try:
        s = unicodedata.normalize("NFKD", s)
        s = "".join(ch for ch in s if not unicodedata.combining(ch))
    except Exception:
        pass
    # normaliser les espaces (NBSP, tabulations, multiples)
    try:
        s = s.replace("\u00A0", " ")
        s = " ".join(s.split())
    except Exception:
        pass
    return s.upper()


def _norm_expr(col_name: str) -> pl.Expr:
    """Normalisation côté Polars (alignée avec _norm_txt) pour comparaison robuste."""
    # Remarque : on réduit les espaces multiples, y compris NBSP.
    return (
        pl.col(col_name)
        .cast(pl.Utf8, strict=False)
        .str.replace_all("\u00A0", " ")
        .str.replace_all(r"\s+", " ")
        .str.strip_chars()
        .str.to_uppercase()
    )


@bp.get("/pim/check_reference_fabricant")
def pim_check_reference_fabricant():
    """Vérifie si une référence fabricant existe déjà dans le parquet manufacturers (PIM).

    Query params:
      - reference: référence fabricant saisie (obligatoire)
      - fabricant: nom du fabricant/fournisseur (optionnel)

    Retour:
      { exists: bool, matches: int, samples: [..] }
    """
    debug = str(request.args.get("debug", "")).strip() in {"1", "true", "True", "yes", "YES"}
    strict_fabricant = str(request.args.get("strict_fabricant", "")).strip() in {"1", "true", "True", "yes", "YES"}

    ref = _norm_txt(request.args.get("reference", ""))
    fabricant = _norm_txt(request.args.get("fabricant", ""))
    if not ref:
        payload = {"exists": False, "matches": 0, "samples": []}
        if debug:
            payload.update(
                {
                    "debug": True,
                    "reason": "empty_reference",
                }
            )
        return jsonify(payload)

    parquet_path = os.path.join(path_datan, folder_name_app, "manufacturer.parquet")
    if not os.path.exists(parquet_path):
        parquet_path = os.path.join(path_datan, folder_name_app, "manufacturers.parquet")
        if not os.path.exists(parquet_path):
            payload = {"exists": False, "matches": 0, "samples": []}
            if debug:
                payload.update(
                    {
                        "debug": True,
                        "reason": "parquet_not_found",
                        "tried": [
                            os.path.join(path_datan, folder_name_app, "manufacturer.parquet"),
                            os.path.join(path_datan, folder_name_app, "manufacturers.parquet"),
                        ],
                    }
                )
            return jsonify(payload)

    try:
        df = pl.read_parquet(parquet_path)
    except Exception as e:
        payload = {"exists": False, "matches": 0, "samples": []}
        if debug:
            payload.update(
                {
                    "debug": True,
                    "reason": "parquet_read_error",
                    "parquet_path": parquet_path,
                    "error": str(e),
                }
            )
        return jsonify(payload)

    if df.is_empty():
        payload = {"exists": False, "matches": 0, "samples": []}
        if debug:
            payload.update(
                {
                    "debug": True,
                    "reason": "parquet_empty",
                    "parquet_path": parquet_path,
                }
            )
        return jsonify(payload)

    ref_candidates = [
        "reference_article_fabricant",
        "reference_fabricant",
        "ref_fabricant",
        "reference",
        "ref",
        "ref_fournisseur",
        "reference_fournisseur",
    ]
    fab_candidates = [
        "fabricant",
        "nom_fournisseur",
        "fournisseur",
        "manufacturer",
    ]

    # 1) colonnes candidates explicites
    ref_cols = [c for c in ref_candidates if c in df.columns]
    # 2) fallback : colonnes contenant ref/reference dans le nom
    if not ref_cols:
        ref_cols = [
            c for c in df.columns
            if ("ref" in c.lower() or "reference" in c.lower())
        ]
    # 3) fallback ultime : toutes les colonnes texte
    if not ref_cols:
        try:
            ref_cols = [c for c, t in df.schema.items() if t == pl.Utf8]
        except Exception:
            ref_cols = []
    if not ref_cols:
        payload = {"exists": False, "matches": 0, "samples": []}
        if debug:
            payload.update(
                {
                    "debug": True,
                    "reason": "no_reference_columns",
                    "parquet_path": parquet_path,
                    "columns": df.columns,
                }
            )
        return jsonify(payload)
    fab_cols = [c for c in fab_candidates if c in df.columns]

    try:
        cond_ref = None
        for c in ref_cols:
            ccond = _norm_expr(c) == ref
            cond_ref = ccond if cond_ref is None else (cond_ref | ccond)

        cond = cond_ref
        # Par défaut, ne pas filtrer par fabricant: c'est trop fragile et provoque des faux négatifs.
        # Activer le filtre seulement si strict_fabricant=1.
        if strict_fabricant and fabricant and fab_cols:
            cond_fab = None
            for c in fab_cols:
                ccond = _norm_expr(c) == fabricant
                cond_fab = ccond if cond_fab is None else (cond_fab | ccond)
            cond = cond_ref & cond_fab

        sub = df.filter(cond)
        n = int(sub.height)
        samples = []
        if n:
            wanted_cols = [c for c in [*fab_cols[:1], *ref_cols[:1], "code_article", "code_article_tdf", "code"] if c in sub.columns]
            if not wanted_cols:
                wanted_cols = sub.columns[:6]
            samples = [r for r in sub.select(wanted_cols).head(5).iter_rows(named=True)]

        payload = {"exists": bool(n), "matches": n, "samples": samples}
        if debug:
            payload.update(
                {
                    "debug": True,
                    "parquet_path": parquet_path,
                    "reference_norm": ref,
                    "fabricant_norm": fabricant,
                    "strict_fabricant": strict_fabricant,
                    "ref_cols_used": ref_cols,
                    "fab_cols_used": fab_cols,
                    "df_height": int(df.height),
                }
            )
        return jsonify(payload)
    except Exception as e:
        payload = {"exists": False, "matches": 0, "samples": []}
        if debug:
            payload.update(
                {
                    "debug": True,
                    "reason": "filter_error",
                    "parquet_path": parquet_path,
                    "reference_norm": ref,
                    "fabricant_norm": fabricant,
                    "strict_fabricant": strict_fabricant,
                    "error": str(e),
                }
            )
        return jsonify(payload)

@bp.post("/search")
def items_search():
    body = request.get_json(silent=True) or {}
    q = (body.get("q") or "").strip()
    filters = body.get("filters") or {}
    limit = int(body.get("limit") or 300)
    df = search_items_df(q, filters, limit)
    return jsonify({
        "columns": (df.columns if df is not None else []),
        "rows": ([r for r in df.iter_rows(named=True)] if df is not None else []),
    })


@bp.get("/<code>/nomenclature")
def item_nomenclature(code: str):
    """Return item BOM tree and ASCII representation for a given article code.

    Construction alignée sur package_supply_chain.api.api_tree_nomenclature_items.
    """
    code = (code or "").strip()
    if not code:
        return jsonify({"error": "code is required"}), 400

    # 1) Charger les données items + nomenclatures depuis le dernier dossier d'output
    try:
        # même logique que dans package_supply_chain.api.api_tree_nomenclature_items
        last_folder = os.listdir(os.path.join(path_output))[-1]
        base = os.path.join(path_output, last_folder)
        items_path = os.path.join(base, "items.parquet")
        nom = Nomenclatures(base, "nomenclatures.parquet")
    except Exception:
        # fallback: ancien comportement basé sur path_datan
        try:
            base = path_datan / folder_name_app
            items_path = base / "items.parquet"
            nom = Nomenclatures(str(base), "nomenclatures.parquet")
        except Exception:
            return jsonify({"code": code, "tree": {}, "ascii": ""})

    try:
        df_items = pl.read_parquet(items_path)
        dico_items = {row["code_article"]: row for row in df_items.iter_rows(named=True)}
    except Exception:
        dico_items = {}

    try:
        tree = nom.get_item_tree(code)
    except Exception:
        tree = {}

    # 2) Transformer l'arbre en ASCII avec la même logique que tree_to_ascii
    ascii_lines: list[str] = []
    try:
        def _tree_to_ascii(node, dico_items_local, depth=0, branch_prefixs=None, is_last=True):
            if not node or "code_article" not in node:
                return []
            if branch_prefixs is None:
                branch_prefixs = []
            lines = []
            prefix = ""
            for p in branch_prefixs[:-1]:
                prefix += ("|    " if p else "     ")
            if depth > 0:
                prefix += ("└───" if is_last else "├───")
            code_art = str(node.get("code_article", "")).strip()
            qte = node.get("quantite")
            if code_art in dico_items_local:
                row = dico_items_local[code_art]
                lib_art = row.get("libelle_court_article")
                type_art = row.get("type_article")
                statut_art = row.get("statut_abrege_article")
                criticite = row.get("criticite_pim")
            else:
                lib_art, type_art, statut_art, criticite = "?", "?", "?", "?"
            items_info = f"{code_art} | {lib_art} | {type_art} | {statut_art} | {criticite} | {qte}"
            lines.append(prefix + items_info)
            children = [c for c in (node.get("code_article_fils") or []) if c]
            for i, child in enumerate(children):
                is_last_child = (i == len(children) - 1)
                new_branch_prefixs = branch_prefixs + [(not is_last_child)]
                lines.extend(_tree_to_ascii(child, dico_items_local, depth + 1, new_branch_prefixs, is_last_child))
            return lines

        ascii_lines = _tree_to_ascii(tree, dico_items)
    except Exception:
        ascii_lines = []

    return jsonify({
        "code": code,
        "tree": tree,
        "ascii": "\n".join(ascii_lines) if ascii_lines else "",
    })

@bp.get("/<code>/details")
def item_details(code: str):
    details = get_item_full(code)
    return jsonify(details)

@bp.get("/<code>/stats-exit")
def item_stats_exit(code: str):
    type_exits = request.args.getlist("type_exit")
    if not type_exits:
        type_exits_arg: str | list[str] | None = None
    elif len(type_exits) == 1:
        type_exits_arg = type_exits[0]
    else:
        type_exits_arg = type_exits

    df = get_stats_exit(code, type_exits_arg)
    return jsonify({
        "columns": (df.columns if df is not None else []),
        "rows": ([r for r in df.iter_rows(named=True)] if df is not None else []),
    })


@bp.get("/<code>/stats-exit-monthly")
def item_stats_exit_monthly(code: str):
    type_exits = request.args.getlist("type_exit")
    if not type_exits:
        type_exits_arg: str | list[str] | None = None
    elif len(type_exits) == 1:
        type_exits_arg = type_exits[0]
    else:
        type_exits_arg = type_exits

    df = get_stats_exit_monthly(code, type_exits_arg)
    return jsonify({
        "columns": (df.columns if df is not None else []),
        "rows": ([r for r in df.iter_rows(named=True)] if df is not None else []),
    })

@bp.get("/<code>/categorie-sans-sortie")
def item_categorie_sans_sortie(code: str):
    code = (code or "").strip()
    if not code:
        return jsonify({"error": "code is required"}), 400

    parquet_path = os.path.join(path_datan, folder_name_app, "items_without_exit_final.parquet")
    if not os.path.exists(parquet_path):
        return jsonify({"error": "items_without_exit_final.parquet not found"}), 500

    try:
        df = pl.read_parquet(parquet_path)
    except Exception:
        return jsonify({"error": "unable to read items_without_exit_final.parquet"}), 500

    if "code_article" not in df.columns:
        return jsonify({"error": "code_article column missing in parquet"}), 500

    try:
        sub = df.filter(pl.col("code_article") == code)
    except Exception:
        sub = pl.DataFrame()

    if sub.height == 0:
        return jsonify({"error": "item not found", "code": code}), 404

    row = sub.row(0, named=True)
    value = row.get("categorie_sans_sortie") if "categorie_sans_sortie" in sub.columns else None

    return jsonify({
        "code_article": code,
        "categorie_sans_sortie": value,
    })


@bp.get("/<code>/network")
def item_network(code: str):
    """Retourne un graphe réseau de relations entre articles pour un code donné.

    - Nœud racine = code demandé
    - Arêtes de type "bom" issues de l'arbre de nomenclature (parent ↔ fils)
    - Arêtes de type "equiv" issues des équivalents d'article
    """

    base_code = (code or "").strip().upper()
    if not base_code:
        return jsonify({"error": "code is required"}), 400

    nodes: dict[str, dict] = {}
    edges: list[dict] = []

    def add_node(code_art: str, group: str = "item"):
        c = (code_art or "").strip().upper()
        if not c:
            return
        if c not in nodes:
            nodes[c] = {"id": c, "label": c, "group": group}

    def add_edge(src: str, dst: str, edge_type: str):
        s = (src or "").strip().upper()
        d = (dst or "").strip().upper()
        if not s or not d or s == d:
            return
        edges.append({"from": s, "to": d, "type": edge_type})

    # Nœud racine
    add_node(base_code, group="root")

    # 1) Arbre de nomenclature (BOM)
    tree = None
    try:
        # Réutiliser la logique de item_nomenclature via Nomenclatures
        try:
            last_folder = os.listdir(os.path.join(path_output))[-1]
            base = os.path.join(path_output, last_folder)
            nom = Nomenclatures(base, "nomenclatures.parquet")
        except Exception:
            base = path_datan / folder_name_app
            nom = Nomenclatures(str(base), "nomenclatures.parquet")

        tree = nom.get_item_tree(base_code)
    except Exception:
        tree = None

    def walk_bom(node, parent_code: str | None = None):
        if not node or "code_article" not in node:
            return
        code_art = str(node.get("code_article", "")).strip().upper()
        if not code_art:
            return
        add_node(code_art, group="item")
        if parent_code:
            add_edge(parent_code, code_art, "bom")
        children = [c for c in (node.get("code_article_fils") or []) if isinstance(c, dict)]
        for child in children:
            walk_bom(child, code_art)

    if tree:
        walk_bom(tree, None)

    # 2) Équivalents d'article
    try:
        eq_rows = get_equivalents_for(base_code) or []
    except Exception:
        eq_rows = []

    for row in eq_rows:
        if not isinstance(row, dict):
            continue
        # Chercher un champ contenant un code article différent du code de base
        eq_code = None
        for k, v in row.items():
            if v is None:
                continue
            key_l = str(k).lower()
            if "code" in key_l and "article" in key_l:
                cand = str(v).strip().upper()
                if cand and cand != base_code:
                    eq_code = cand
                    break
        if not eq_code:
            continue
        add_node(eq_code, group="equiv")
        add_edge(base_code, eq_code, "equiv")

    # Dédoublonner les arêtes (from, to, type)
    seen = set()
    unique_edges: list[dict] = []
    for e in edges:
        key = (e["from"], e["to"], e["type"])
        if key in seen:
            continue
        seen.add(key)
        unique_edges.append(e)

    return jsonify({
        "code": base_code,
        "nodes": list(nodes.values()),
        "edges": unique_edges,
    })

