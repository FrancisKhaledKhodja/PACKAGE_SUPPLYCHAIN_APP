from flask import jsonify

from . import bp
from supplychain_app.data.pudo_service import (
    get_helios_production_summary_for_item,
    get_helios_active_sites_for_item,
    get_coords_for_ig,
    get_helios_active_items_for_site,
    get_helios_parent_child_items_for_site,
)


@bp.get("/<code>")
def helios_for_item(code: str):
    """Return Helios park summary and active sites for a given item code.

    Response schema:
      {
        "code": "...",
        "quantity_active": float,
        "active_sites": int,
        "sites": [ { ... } ]
      }
    """
    code = (code or "").strip()
    if not code:
        return jsonify({"error": "code is required"}), 400

    summary = get_helios_production_summary_for_item(code)
    sites = get_helios_active_sites_for_item(code)
    return jsonify({
        "code": summary.get("code", code),
        "quantity_active": summary.get("quantity_active", 0.0),
        "active_sites": summary.get("active_sites", 0),
        "sites": sites or [],
    })


@bp.get("/site/<code_ig>")
def helios_for_site(code_ig: str):
    code = (code_ig or "").strip().upper()
    if not code:
        return jsonify({"error": "code_ig is required"}), 400

    coords = get_coords_for_ig(code)
    if not coords:
        return jsonify({"error": "unknown code_ig"}), 404

    items = get_helios_active_items_for_site(code)
    tree = get_helios_parent_child_items_for_site(code)
    qty_total = 0.0
    try:
        qty_total = float(sum(float((it.get("quantity_active") or 0) or 0) for it in (items or [])))
    except Exception:
        qty_total = 0.0

    return jsonify({
        "code_ig": code,
        "site": coords,
        "quantity_active": qty_total,
        "active_items": len(items or []),
        "items": items or [],
        "parent_col": tree.get("parent_col"),
        "parents": tree.get("parents") or [],
        "children_by_parent": tree.get("children_by_parent") or {},
    }), 200

