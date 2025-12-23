import os

from flask import request, jsonify, session

from . import bp
from supplychain_app.services.pudo_service import (
    get_store_contacts,
    get_store_types,
    get_store_details,
    list_technician_pudo_assignments,
    get_distance_tech_pr_for_store,
    get_pr_overrides_for_store,
    save_pr_overrides_for_store,
    get_ol_technicians,
    get_pudo_postal_address,
    get_ol_igs,
    get_ol_stores,
    search_ol_igs,
)


def _ol_allowed_logins() -> set[str]:
    raw = (os.environ.get("SCAPP_OL_ALLOWED_LOGINS") or "").strip()
    if not raw:
        return set()
    return {
        x.strip().casefold()
        for x in raw.split(",")
        if x is not None and str(x).strip() != ""
    }


def _require_ol_access():
    allowed = _ol_allowed_logins()
    if not allowed:
        return None

    login = session.get("proxy_login")
    login_norm = str(login or "").strip().casefold()
    if not login_norm:
        return jsonify({"error": "forbidden", "reason": "login_required"}), 403
    if login_norm not in allowed:
        return jsonify({"error": "forbidden", "reason": "not_allowed"}), 403
    return None


@bp.get("/contacts")
def list_contacts():
    """Return store contacts for technician selection.

    Optional query params:
      - q: text search
      - types: repeated param for depot types
    """
    q = (request.args.get("q") or "").strip()
    types = request.args.getlist("types") or None
    contacts = get_store_contacts(query=q, depot_types=types)
    store_types = get_store_types()
    return jsonify({
        "contacts": contacts,
        "store_types": store_types,
    })


@bp.get("/<code>")
def technician_details(code: str):
    """Return details for a given store code (technician contact)."""
    code = (code or "").strip()
    if not code:
        return jsonify({"error": "code is required"}), 400
    details = get_store_details(code)
    if not details:
        return jsonify({"error": "not found"}), 404

    # Build PR details (principal / backup / hors_normes) from assignments
    pr_details = {"principal": None, "backup": None, "hors_normes": None}
    try:
        assignments = [r for r in list_technician_pudo_assignments() if str(r.get("code_magasin")) == str(details.get("code_magasin"))]
        for role in ["principal", "backup", "hors_normes"]:
            for r in assignments:
                if r.get("pr_role") == role:
                    pr_details[role] = {
                        "code_point_relais": r.get("code_point_relais"),
                        "code_point_relais_store": None,
                        "enseigne": r.get("enseigne"),
                        "adresse_postale": r.get("adresse_postale"),
                        "type_de_depot": r.get("type_de_depot"),
                        "technicien": r.get("technicien"),
                        "statut": r.get("statut"),
                        "categorie": r.get("categorie"),
                        "prestataire": r.get("prestataire"),
                        "periode_absence_a_utiliser": r.get("periode_absence_a_utiliser"),
                    }
                    break
    except Exception:
        pr_details = {"principal": None, "backup": None, "hors_normes": None}

    # Always expose the PR codes coming from stores.parquet (stores_final.parquet copy)
    # so the frontend can display them under each PUDO card.
    role_to_store_key = {
        "principal": "pr_principal",
        "backup": "pr_backup",
        "hors_normes": "pr_hors_normes",
    }
    for role, key in role_to_store_key.items():
        store_code_pr = details.get(key) or (details.get("pr_hors_norme") if role == "hors_normes" else None)
        if store_code_pr is None or str(store_code_pr).strip() == "":
            continue
        if pr_details.get(role) is None:
            pr_details[role] = {
                "code_point_relais": None,
                "code_point_relais_store": str(store_code_pr),
                "enseigne": None,
                "adresse_postale": None,
                "type_de_depot": None,
                "technicien": None,
                "statut": None,
                "categorie": None,
                "prestataire": None,
                "periode_absence_a_utiliser": None,
            }
        else:
            pr_details[role]["code_point_relais_store"] = str(store_code_pr)

    return jsonify({"details": details, "pr_details": pr_details})


@bp.get("/<code>/distances_pr")
def technician_distances_pr_api(code: str):
    """Retourne les distances/durées (voiture) entre un technicien et ses PR.

    Source : distance_tech_pr.parquet (copié dans Datan via l'update_data).

    Query params:
      - pr: filtre exact sur le code point relais
      - limit: limite le nombre de lignes (triées par distance si possible)
    """
    code = (code or "").strip()
    if not code:
        return jsonify({"error": "code is required"}), 400

    pr_code = (request.args.get("pr") or "").strip() or None
    limit = request.args.get("limit")

    df = get_distance_tech_pr_for_store(code_magasin=code, code_pr=pr_code, limit=limit)
    rows = [r for r in df.iter_rows(named=True)] if df is not None else []
    return jsonify({
        "code_magasin": code,
        "pr": pr_code,
        "rows": rows,
    })


@bp.get("/assignments")
def technician_assignments_api():
    """Return list of technician ↔ PUDO assignments, with optional filters.

    Query params:
      - q: free text search on technicien / code magasin / code PR / ville
      - pr: exact code_point_relais filter
      - store: exact code_magasin filter
      - status: filter on statut (substring, case-insensitive)
      - roles: repeated param to filter on pr_role
      - expand_store_roles: when true, returns all rows (all roles) for stores matching the filters
    """
    rows = list_technician_pudo_assignments() or []

    q = (request.args.get("q") or "").strip().lower()
    pr_code = (request.args.get("pr") or "").strip().lower()
    store_code = (request.args.get("store") or "").strip().lower()
    status = (request.args.get("status") or "").strip().lower()
    roles = [str(x).strip().lower() for x in (request.args.getlist("roles") or []) if str(x).strip()]
    expand_store_roles = str(request.args.get("expand_store_roles") or "").strip().lower() in {"1", "true", "yes", "y", "on"}

    def matches(row: dict) -> bool:
        if roles:
            if str(row.get("pr_role") or "").strip().lower() not in roles:
                return False
        if pr_code:
            if str(row.get("code_point_relais") or "").strip().lower() != pr_code:
                return False
        if store_code:
            if str(row.get("code_magasin") or "").strip().lower() != store_code:
                return False
        if status:
            st = str(row.get("statut") or "").strip().lower()
            if status not in st:
                return False
        if q:
            hay = " ".join([
                str(row.get("code_magasin") or ""),
                str(row.get("technicien") or ""),
                str(row.get("code_point_relais") or ""),
                str(row.get("enseigne") or ""),
                str(row.get("adresse_postale") or ""),
                str(row.get("type_de_depot") or ""),
            ]).lower()
            if q not in hay:
                return False
        return True

    filtered = [r for r in rows if matches(r)]

    if expand_store_roles:
        store_codes = {
            str(r.get("code_magasin") or "").strip().lower()
            for r in filtered
            if str(r.get("code_magasin") or "").strip()
        }
        if store_codes:
            filtered = [
                r for r in rows
                if str(r.get("code_magasin") or "").strip().lower() in store_codes
            ]
    return jsonify({"rows": filtered})


@bp.get("/<code>/pr_overrides")
def technician_pr_overrides_get(code: str):
    code = (code or "").strip()
    if not code:
        return jsonify({"error": "code is required"}), 400
    data = get_pr_overrides_for_store(code)
    return jsonify(data)


@bp.post("/<code>/pr_overrides")
def technician_pr_overrides_post(code: str):
    code = (code or "").strip()
    if not code:
        return jsonify({"error": "code is required"}), 400
    payload = request.get_json(silent=True) or {}
    data = save_pr_overrides_for_store(code, payload)
    if "error" in data:
        return jsonify(data), 400
    return jsonify(data)


@bp.get("/ol_technicians")
def ol_technicians_list():
    denied = _require_ol_access()
    if denied is not None:
        return denied
    """Liste des techniciens éligibles pour l'OL mode dégradé.

    Les données proviennent de stores.parquet, filtrées sur les
    types de dépôt REO / EMBARQUE / EXPERT.
    """
    rows = get_ol_technicians() or []
    return jsonify({"technicians": rows})


@bp.get("/ol_pudo_address/<code_pr>")
def ol_pudo_address(code_pr: str):
    denied = _require_ol_access()
    if denied is not None:
        return denied
    """Adresse postale du point relais choisi pour l'OL mode dégradé."""
    code_pr = (code_pr or "").strip()
    if not code_pr:
        return jsonify({"error": "code_pr is required"}), 400
    data = get_pudo_postal_address(code_pr)
    if not data:
        return jsonify({"error": "not found"}), 404
    return jsonify(data)


@bp.get("/ol_igs")
def ol_igs_list():
    denied = _require_ol_access()
    if denied is not None:
        return denied
    """Liste des codes IG disponibles pour l'OL mode dégradé."""
    rows = get_ol_igs() or []
    return jsonify({"igs": rows})


@bp.get("/ol_igs_search")
def ol_igs_search():
    denied = _require_ol_access()
    if denied is not None:
        return denied
    """Recherche filtrée de codes IG pour l'OL mode dégradé.

    Query params :
      - q : texte à rechercher dans le code IG ou le libellé long
      - limit : nombre maximum de résultats (défaut 50, max 500)
    """
    q = (request.args.get("q") or "").strip()
    try:
        limit = int(request.args.get("limit") or "50")
    except Exception:
        limit = 50
    rows = search_ol_igs(query=q, limit=limit) or []
    return jsonify({"igs": rows})


@bp.get("/ol_stores")
def ol_stores_list():
    denied = _require_ol_access()
    if denied is not None:
        return denied
    """Liste des magasins NATIONAL / LOCAL utilisables pour l'expédition OL."""
    rows = get_ol_stores() or []
    return jsonify({"stores": rows})

