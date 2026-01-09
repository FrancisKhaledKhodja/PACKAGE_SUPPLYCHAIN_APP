import os

from flask import request, jsonify
from . import bp
from supplychain_app.services.pudo_service import get_available_pudo, get_pudo_directory, reload_data as reload_services_data
from supplychain_app.services.geocoding import get_latitude_and_longitude
from supplychain_app.data.pudo_etl import get_update_status, update_data
from supplychain_app.data.pudo_service import reload_data as reload_data_data
from supplychain_app.data.pudo_service import get_coords_for_ig


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
    code_ig = (body.get("code_ig") or "").strip()
    radius = float(body.get("radius_km", body.get("radius", 10)))
    enseignes = body.get("enseignes")

    coords = None
    if address:
        coords = get_latitude_and_longitude(address)
    elif code_ig:
        coords = get_coords_for_ig(code_ig)
    else:
        return jsonify({"error": "address or code_ig is required"}), 400

    lat = coords.get("latitude") if coords else None
    lon = coords.get("longitude") if coords else None
    if lat is None or lon is None:
        return jsonify({"error": "could not resolve address/code_ig"}), 400

    geocoded_address = coords.get("address") or coords.get("postal_address")
    if not geocoded_address:
        geocoded_address = address or code_ig

    df = get_available_pudo(float(lat), float(lon), radius, enseignes)
    rows = [r for r in df.iter_rows(named=True)] if df is not None else []
    return jsonify({
        "rows": rows,
        "geocoded_address": geocoded_address,
        "center_lat": float(lat),
        "center_lon": float(lon),
    }), 200


@bp.get("/directory")
def pudo_directory_api():
    """
    Retourne l'annuaire des points relais pour l'administration PR.
    """
    rows = get_pudo_directory()
    return jsonify({"rows": rows})


@bp.get("/update-status")
def pudo_update_status_api():
    try:
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
    except Exception as e:
        return jsonify({
            "items": [],
            "any_update": False,
            "error": f"{e.__class__.__name__}: {e}",
        }), 503


@bp.post("/update")
def pudo_update_api():
    try:
        result = update_data()
        try:
            reload_services_data(force=True)
        except Exception:
            pass
        try:
            reload_data_data(force=True)
        except Exception:
            pass
        return jsonify(result), 200
    except Exception as e:
        return jsonify({"error": f"{e.__class__.__name__}: {e}"}), 500


@bp.get("/logs")
def pudo_logs_api():
    log_path = os.environ.get("SCAPP_LOG_PATH", "application.log")
    try:
        n = int(request.args.get("n", 200))
    except Exception:
        n = 200
    n = max(1, min(n, 2000))

    if not os.path.exists(log_path):
        return jsonify({"path": log_path, "lines": []}), 200

    try:
        with open(log_path, "rb") as f:
            f.seek(0, os.SEEK_END)
            size = f.tell()
            block = 4096
            data = b""
            while size > 0 and data.count(b"\n") <= n:
                step = block if size - block > 0 else size
                f.seek(-step, os.SEEK_CUR)
                data = f.read(step) + data
                f.seek(-step, os.SEEK_CUR)
                size -= step
        text = data.decode("utf-8", errors="replace")
        lines = text.splitlines()[-n:]
        return jsonify({"path": log_path, "lines": lines}), 200
    except Exception as e:
        return jsonify({"path": log_path, "lines": [], "error": f"{e.__class__.__name__}: {e}"}), 500

