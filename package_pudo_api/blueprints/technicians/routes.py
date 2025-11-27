from flask import request, jsonify

from . import bp
from package_pudo_api.services.pudo_service import (
    get_store_contacts,
    get_store_types,
    get_store_details,
    list_technician_pudo_assignments,
    get_pr_overrides_for_store,
    save_pr_overrides_for_store,
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
