from flask import request, jsonify
from . import bp
from package_pudo_api.services.pudo_service import get_nearby_stores
from package_pudo_api.services.geocoding import get_latitude_and_longitude
from package_pudo_api.data.pudo_service import get_stock_map_for_item, get_coords_for_ig

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


@bp.get("/stock-map/<code_article>")
def stores_stock_map(code_article: str):
    code = (code_article or "").strip()
    if not code:
        return jsonify({"error": "code_article is required"}), 400

    rows = get_stock_map_for_item(code)
    return jsonify({"rows": rows}), 200


@bp.post("/stock-map")
def stores_stock_map_with_ref():
    body = request.get_json(silent=True) or {}
    code_article = (body.get("code_article") or "").strip()
    if not code_article:
        return jsonify({"error": "code_article is required"}), 400

    address = (body.get("address") or "").strip()
    code_ig = (body.get("code_ig") or "").strip()

    # Filtres optionnels sur le stock
    type_de_depot_filters = body.get("type_de_depot") or body.get("type_de_depot_filters") or []
    code_qualite_filters = body.get("code_qualite") or body.get("code_qualite_filters") or []
    flag_stock_d_m_filters = body.get("flag_stock_d_m") or body.get("flag_stock_d_m_filters") or []

    if not isinstance(type_de_depot_filters, list):
        type_de_depot_filters = []
    if not isinstance(code_qualite_filters, list):
        code_qualite_filters = []
    if not isinstance(flag_stock_d_m_filters, list):
        flag_stock_d_m_filters = []

    hors_transit_only = bool(body.get("hors_transit_only"))

    ref_lat = None
    ref_lon = None
    center_label = None

    # Priorité à l'adresse si renseignée
    if address:
        coords = get_latitude_and_longitude(address)
        if not coords:
            return jsonify({"error": "could not geocode address"}), 400
        ref_lat = coords.get("latitude")
        ref_lon = coords.get("longitude")
        center_label = coords.get("address") or address
    elif code_ig:
        coords = get_coords_for_ig(code_ig)
        if not coords:
            return jsonify({"error": "unknown code_ig"}), 400
        ref_lat = coords.get("latitude")
        ref_lon = coords.get("longitude")
        center_label = coords.get("postal_address") or coords.get("address") or code_ig

    rows = get_stock_map_for_item(
        code_article,
        ref_lat=ref_lat,
        ref_lon=ref_lon,
        type_de_depot_filters=type_de_depot_filters or None,
        code_qualite_filters=code_qualite_filters or None,
        flag_stock_d_m_filters=flag_stock_d_m_filters or None,
        hors_transit_only=hors_transit_only,
    )
    return jsonify({
        "rows": rows,
        "center_lat": float(ref_lat) if ref_lat is not None else None,
        "center_lon": float(ref_lon) if ref_lon is not None else None,
        "center_label": center_label,
    }), 200
