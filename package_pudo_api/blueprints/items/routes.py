import os
import polars as pl

from flask import request, jsonify

from . import bp
from ...services.items_service import search_items_df, get_item_full, get_stats_exit
from package_pudo_api.items import Nomenclatures
from package_pudo_api.constants import path_datan, folder_name_app, path_output

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
