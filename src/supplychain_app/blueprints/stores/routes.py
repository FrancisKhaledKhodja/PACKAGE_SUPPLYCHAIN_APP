import os
import tempfile

import polars as pl
from flask import request, jsonify, send_file
from . import bp
from supplychain_app.services.pudo_service import get_nearby_stores
from supplychain_app.services.geocoding import get_latitude_and_longitude
from supplychain_app.data.pudo_service import (
    get_stock_map_for_item,
    get_coords_for_ig,
    get_pudo_coords,
    get_stock_map_for_all_stores_by_type,
)
from supplychain_app.constants import path_datan, folder_name_app

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
    address = (body.get("address") or "").strip()
    code_ig = (body.get("code_ig") or "").strip()
    radius = float(body.get("radius_km", body.get("radius", 10)))
    types = body.get("store_types")

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

    # Si store_types est une liste vide, l'intention est "aucun type de magasin" ⇒ 0 résultat
    if isinstance(types, list) and not types:
        return jsonify({
            "rows": [],
            "geocoded_address": geocoded_address,
            "center_lat": float(lat),
            "center_lon": float(lon),
        }), 200

    df = get_nearby_stores(float(lat), float(lon), radius, types)
    rows = [r for r in df.iter_rows(named=True)] if df is not None else []
    return jsonify({
        "rows": rows,
        "geocoded_address": geocoded_address,
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

    address = (body.get("address") or "").strip()
    code_ig = (body.get("code_ig") or "").strip()

    pr_principal_code = (body.get("pr_principal") or "").strip() or None
    pr_hn_code = (body.get("pr_hors_normes") or body.get("pr_hors_norme") or "").strip() or None

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

    # Cas 1 : aucun code article fourni ⇒ mode "magasins par type de dépôt" uniquement
    if not code_article:
        rows = get_stock_map_for_all_stores_by_type(
            ref_lat=ref_lat,
            ref_lon=ref_lon,
            type_de_depot_filters=type_de_depot_filters or None,
        )

        return jsonify({
            "rows": rows,
            "center_lat": float(ref_lat) if ref_lat is not None else None,
            "center_lon": float(ref_lon) if ref_lon is not None else None,
            "center_label": center_label,
            # Pas de PR principal / hors normes dans ce mode
            "pr_principal_lat": None,
            "pr_principal_lon": None,
            "pr_hn_lat": None,
            "pr_hn_lon": None,
            "pr_principal_label": None,
            "pr_hn_label": None,
        }), 200

    # Cas 2 : code article fourni ⇒ comportement historique (tous les filtres possibles)
    rows = get_stock_map_for_item(
        code_article,
        ref_lat=ref_lat,
        ref_lon=ref_lon,
        pr_principal_code=pr_principal_code,
        pr_hn_code=pr_hn_code,
        type_de_depot_filters=type_de_depot_filters or None,
        code_qualite_filters=code_qualite_filters or None,
        flag_stock_d_m_filters=flag_stock_d_m_filters or None,
        hors_transit_only=hors_transit_only,
    )
    pr_principal_lat = pr_principal_lon = None
    pr_principal_label = None
    pr_hn_lat = pr_hn_lon = None
    pr_hn_label = None

    if pr_principal_code:
        info = get_pudo_coords(pr_principal_code)
        if info:
            pr_principal_lat = info.get("latitude")
            pr_principal_lon = info.get("longitude")
            enseigne = info.get("enseigne") or ""
            adr = info.get("adresse_postale") or ""
            parts = [p for p in [enseigne, adr] if p]
            if parts:
                pr_principal_label = " - ".join(parts)

    if pr_hn_code:
        info_hn = get_pudo_coords(pr_hn_code)
        if info_hn:
            pr_hn_lat = info_hn.get("latitude")
            pr_hn_lon = info_hn.get("longitude")
            enseigne_hn = info_hn.get("enseigne") or ""
            adr_hn = info_hn.get("adresse_postale") or ""
            parts_hn = [p for p in [enseigne_hn, adr_hn] if p]
            if parts_hn:
                pr_hn_label = " - ".join(parts_hn)

    return jsonify({
        "rows": rows,
        "center_lat": float(ref_lat) if ref_lat is not None else None,
        "center_lon": float(ref_lon) if ref_lon is not None else None,
        "center_label": center_label,
        "pr_principal_lat": float(pr_principal_lat) if pr_principal_lat is not None else None,
        "pr_principal_lon": float(pr_principal_lon) if pr_principal_lon is not None else None,
        "pr_hn_lat": float(pr_hn_lat) if pr_hn_lat is not None else None,
        "pr_hn_lon": float(pr_hn_lon) if pr_hn_lon is not None else None,
        "pr_principal_label": pr_principal_label,
        "pr_hn_label": pr_hn_label,
    }), 200


@bp.post("/stock-map/export")
def stores_stock_map_export():
    """Exporte un extrait détaillé du stock (stock_final.parquet) pour les codes article
    et filtres saisis sur l'écran "Localisation du stock".

    - Filtre sur code_article (un ou plusieurs, séparés par ";")
    - Filtres optionnels : type_de_depot, code_qualite, flag_stock_d_m, hors_transit_only
    - Si aucun résultat, renvoie une erreur 400 "no_results" et aucun fichier n'est généré.
    """
    body = request.get_json(silent=True) or {}

    raw_code = (body.get("code_article") or "").strip()
    codes = [c.strip().upper() for c in raw_code.split(";") if c and c.strip()]

    # Permettre aussi un tableau explicite de codes
    if not codes and isinstance(body.get("codes"), list):
        codes = [str(c or "").strip().upper() for c in body["codes"] if str(c or "").strip()]

    if not codes:
        return jsonify({"error": "code_article is required"}), 400

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

    stock_parquet = os.path.join(path_datan, folder_name_app, "stock_final.parquet")
    if not os.path.exists(stock_parquet):
        return jsonify({"error": "not_found"}), 404

    try:
        df = pl.read_parquet(stock_parquet)
    except Exception:
        return jsonify({"error": "read_failed"}), 500

    # Filtre sur les codes article et les quantités strictement positives
    df = df.filter(pl.col("code_article").is_in(codes))
    if "qte_stock" in df.columns:
        df = df.filter(pl.col("qte_stock") > 0)

    # Filtres optionnels fournis par l'appelant
    if type_de_depot_filters and "type_de_depot" in df.columns:
        df = df.filter(pl.col("type_de_depot").is_in(type_de_depot_filters))
    if code_qualite_filters and "code_qualite" in df.columns:
        df = df.filter(pl.col("code_qualite").is_in(code_qualite_filters))
    if flag_stock_d_m_filters and "flag_stock_d_m" in df.columns:
        df = df.filter(pl.col("flag_stock_d_m").is_in(flag_stock_d_m_filters))

    # Filtre HORS TRANSIT : exclure les emplacements se terminant par "-T"
    if hors_transit_only:
        emp_cols = [c for c in df.columns if "emplacement" in c.lower()]
        if emp_cols:
            emp_col = emp_cols[0]
            df = (
                df.with_columns(
                    pl.col(emp_col).cast(pl.Utf8).alias("__emplacement_tmp__")
                )
                .filter(~pl.col("__emplacement_tmp__").str.ends_with("-T"))
                .drop("__emplacement_tmp__")
            )

    if df.is_empty():
        return jsonify({"error": "no_results"}), 400

    # Export CSV (ouvrable dans Excel) dans un fichier temporaire
    tmp = tempfile.NamedTemporaryFile(suffix=".csv", delete=False)
    tmp_path = tmp.name
    tmp.close()

    try:
        df.write_csv(tmp_path, separator=";")
    except Exception:
        return jsonify({"error": "export_failed"}), 500

    filename = "localisation_stock.csv"
    return send_file(
        tmp_path,
        as_attachment=True,
        download_name=filename,
        mimetype="text/csv; charset=utf-8",
    )

