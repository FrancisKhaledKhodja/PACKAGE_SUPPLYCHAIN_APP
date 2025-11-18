from flask import request, jsonify
from . import bp
from package_pudo_api.services.pudo_service import get_nearby_stores
from package_pudo_api.services.geocoding import get_latitude_and_longitude

@bp.post("/nearby")
def stores_nearby():
    body = request.get_json(silent=True) or {}
    lat = float(body.get("lat"))
    lon = float(body.get("lon"))
    radius = float(body.get("radius", 10))
    types = body.get("store_types")
    df = get_nearby_stores(lat, lon, radius, types)
    rows = [r for r in df.iter_rows(named=True)] if df is not None else []
    return jsonify({"rows": rows})


@bp.post("/nearby-address")
def stores_nearby_address():
    body = request.get_json(silent=True) or {}
    address = body.get("address")
    radius = float(body.get("radius_km", body.get("radius", 10)))
    types = body.get("store_types")

    if not address:
        return jsonify({"error": "address is required"}), 400

    coords = get_latitude_and_longitude(address)
    lat = coords.get("latitude") if coords else None
    lon = coords.get("longitude") if coords else None
    if lat is None or lon is None:
        return jsonify({"error": "could not geocode address"}), 400

    df = get_nearby_stores(float(lat), float(lon), radius, types)
    rows = [r for r in df.iter_rows(named=True)] if df is not None else []
    return jsonify({
        "rows": rows,
        "geocoded_address": coords.get("address"),
        "center_lat": float(lat),
        "center_lon": float(lon),
    }), 200
