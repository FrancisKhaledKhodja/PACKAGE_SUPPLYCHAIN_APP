from flask import request, jsonify

from . import bp
from package_pudo_api.services.pudo_service import (
    get_store_contacts,
    get_store_types,
    get_store_details,
    list_technician_pudo_assignments,
    get_pr_overrides_for_store,
    save_pr_overrides_for_store,
    get_ol_technicians,
    get_pudo_postal_address,
    get_ol_igs,
    get_ol_stores,
    search_ol_igs,
)


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
                        "enseigne": r.get("enseigne"),
                        "adresse_postale": r.get("adresse_postale"),
                        "type_de_depot": r.get("type_de_depot"),
                        "technicien": r.get("technicien"),
                        "statut": r.get("statut"),
                        "categorie": r.get("categorie"),
                        "prestataire": r.get("prestataire"),
                    }
                    break
    except Exception:
        pr_details = {"principal": None, "backup": None, "hors_normes": None}

    return jsonify({"details": details, "pr_details": pr_details})


@bp.get("/assignments")
def technician_assignments_api():
    """Return list of technician ↔ PUDO assignments, with optional filters.

    Query params:
      - q: free text search on technicien / code magasin / code PR / ville
      - pr: exact code_point_relais filter
      - store: exact code_magasin filter
      - status: filter on statut (substring, case-insensitive)
    """
    rows = list_technician_pudo_assignments() or []

    q = (request.args.get("q") or "").strip().lower()
    pr_code = (request.args.get("pr") or "").strip().lower()
    store_code = (request.args.get("store") or "").strip().lower()
    status = (request.args.get("status") or "").strip().lower()

    def matches(row: dict) -> bool:
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
    """Liste des techniciens éligibles pour l'OL mode dégradé.

    Les données proviennent de stores.parquet, filtrées sur les
    types de dépôt REO / EMBARQUE / EXPERT.
    """
    rows = get_ol_technicians() or []
    return jsonify({"technicians": rows})


@bp.get("/ol_pudo_address/<code_pr>")
def ol_pudo_address(code_pr: str):
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
    """Liste des codes IG disponibles pour l'OL mode dégradé."""
    rows = get_ol_igs() or []
    return jsonify({"igs": rows})


@bp.get("/ol_igs_search")
def ol_igs_search():
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
    """Liste des magasins NATIONAL / LOCAL utilisables pour l'expédition OL."""
    rows = get_ol_stores() or []
    return jsonify({"stores": rows})
