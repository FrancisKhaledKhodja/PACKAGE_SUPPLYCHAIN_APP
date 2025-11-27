from flask import request, jsonify
from . import bp
from package_pudo_api.services.pudo_service import get_available_pudo, get_pudo_directory
from package_pudo_api.services.geocoding import get_latitude_and_longitude
from package_pudo_api.data.pudo_etl import get_update_status, update_data


@bp.post("/search")
def pudo_search():
    body = request.get_json(silent=True) or {}
    lat = float(body.get("lat"))
    lon = float(body.get("lon"))
    radius = float(body.get("radius", 10))
    enseignes = body.get("enseignes")
    df = get_available_pudo(lat, lon, radius, enseignes)
    rows = [r for r in df.iter_rows(named=True)] if df is not None else []
    return jsonify({"rows": rows})


@bp.post("/nearby-address")
def pudo_nearby_address():
    body = request.get_json(silent=True) or {}
    address = body.get("address")
    radius = float(body.get("radius_km", body.get("radius", 10)))
    enseignes = body.get("enseignes")

    if not address:
        return jsonify({"error": "address is required"}), 400

    coords = get_latitude_and_longitude(address)
    lat = coords.get("latitude") if coords else None
    lon = coords.get("longitude") if coords else None
    if lat is None or lon is None:
        return jsonify({"error": "could not geocode address"}), 400

    df = get_available_pudo(float(lat), float(lon), radius, enseignes)
    rows = [r for r in df.iter_rows(named=True)] if df is not None else []
    return jsonify({"rows": rows, "geocoded_address": coords.get("address")}), 200


@bp.get("/directory")
def pudo_directory_api():
    """
    Retourne l'annuaire des points relais pour l'administration PR.
    """
    rows = get_pudo_directory()
    return jsonify({"rows": rows})


@bp.get("/update-status")
def pudo_update_status_api():
    status = get_update_status()

    def _fmt(ts):
        import datetime
        if ts is None:
            return None
        try:
            return datetime.datetime.fromtimestamp(ts).isoformat()
        except Exception:
            return None

    for it in status:
        it["src_mtime_iso"] = _fmt(it.get("src_mtime"))
        it["dst_mtime_iso"] = _fmt(it.get("dst_mtime"))

    return jsonify({
        "items": status,
        "any_update": any(i.get("needs_update") for i in status),
    })


@bp.post("/update")
def pudo_update_api():
    try:
        result = update_data()
        return jsonify(result), 200
    except Exception as e:
        return jsonify({"error": f"{e.__class__.__name__}: {e}"}), 500
