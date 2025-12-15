from flask import jsonify

from . import bp
from supplychain_app.data.pudo_service import (
    get_helios_production_summary_for_item,
    get_helios_active_sites_for_item,
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

