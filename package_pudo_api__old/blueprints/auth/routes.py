import os
import shutil
import glob

from flask import request, jsonify, session, send_from_directory
from . import bp
from package_pudo_api.data.pudo_etl import get_stock_summary, get_stock_details, get_stock_final_details
from package_pudo_api.constants import path_photos_local, path_photos_network

@bp.post("/login")
def login():
    body = request.get_json(silent=True) or {}
    login = body.get("login")
    password = body.get("password")

    if login:
        session["proxy_login"] = login
    if password:
        session["proxy_password"] = password

    return jsonify({"ok": True, "login": login}), 200


@bp.get("/me")
def me():
    """Retourne le login actuellement stocké en session (si présent)."""
    login = session.get("proxy_login")
    return jsonify({"login": login}), 200


def ensure_article_photos(code_article: str) -> None:
    pattern_local = os.path.join(path_photos_local, f"*{code_article}*.webp")
    if glob.glob(pattern_local):
        return

    os.makedirs(path_photos_local, exist_ok=True)
    pattern_network = os.path.join(path_photos_network, f"*{code_article}*.webp")
    for src in glob.glob(pattern_network):
        try:
            shutil.copy2(src, path_photos_local)
        except OSError:
            pass


@bp.get("/photos/<code_article>")
def list_article_photos(code_article):
    ensure_article_photos(code_article)
    pattern_local = os.path.join(path_photos_local, f"*{code_article}*.webp")
    files = [os.path.basename(p) for p in glob.glob(pattern_local)]
    return jsonify({"code_article": code_article, "files": files})


@bp.get("/photos/stats")
def photos_stats():
    pattern_network = os.path.join(path_photos_network, "*.webp")
    pattern_local = os.path.join(path_photos_local, "*.webp")

    network_files = glob.glob(pattern_network)
    local_files = glob.glob(pattern_local)

    set_network = {os.path.basename(p) for p in network_files}
    set_local = {os.path.basename(p) for p in local_files}

    local_matching_network = len(set_network & set_local)

    return jsonify({
        "total_network_files": len(network_files),
        "total_local_files": len(local_files),
        "local_matching_network": local_matching_network,
    }), 200


@bp.get("/photos/raw/<filename>")
def serve_article_photo(filename):
    # Sert un fichier image depuis le répertoire local des photos
    return send_from_directory(path_photos_local, filename)


@bp.post("/photos/sync")
def sync_all_photos():
    os.makedirs(path_photos_local, exist_ok=True)

    pattern_network = os.path.join(path_photos_network, "*.webp")
    network_files = glob.glob(pattern_network)

    copied = 0
    existing = 0

    for src in network_files:
        base = os.path.basename(src)
        dst = os.path.join(path_photos_local, base)
        if os.path.exists(dst):
            existing += 1
            continue
        try:
            shutil.copy2(src, dst)
            copied += 1
        except OSError:
            # on ignore les erreurs individuelles
            pass

    return jsonify({
        "copied": copied,
        "already_present": existing,
        "total_network_files": len(network_files),
    }), 200


@bp.get("/stock/<code_article>")
def stock_summary(code_article):
    ensure_article_photos(code_article)
    try:
        df = get_stock_summary(code_article)
    except FileNotFoundError:
        return jsonify({"error": "stock parquet not found"}), 500

    if df.height == 0:
        return jsonify({"code_article": code_article, "rows": []}), 200

    rows = df.to_dicts()
    return jsonify({"code_article": code_article, "rows": rows}), 200


@bp.get("/stock/<code_article>/ultra-details")
def stock_ultra_details(code_article):
    ensure_article_photos(code_article)
    """Retourne un état de stock ultra détaillé basé sur stock_final.parquet."""
    try:
        df = get_stock_final_details(code_article)
    except FileNotFoundError:
        return jsonify({"error": "stock_final parquet not found"}), 500

    if df.height == 0:
        return jsonify({"code_article": code_article, "rows": []}), 200

    rows = df.to_dicts()
    return jsonify({"code_article": code_article, "rows": rows}), 200


@bp.get("/stock/<code_article>/details")
def stock_details(code_article):
    ensure_article_photos(code_article)
    try:
        df = get_stock_details(code_article)
    except FileNotFoundError:
        return jsonify({"error": "stock parquet not found"}), 500

    if df.height == 0:
        return jsonify({"code_article": code_article, "rows": []}), 200

    rows = df.to_dicts()
    return jsonify({"code_article": code_article, "rows": rows}), 200
