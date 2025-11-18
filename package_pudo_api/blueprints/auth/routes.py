from flask import request, jsonify, session
from . import bp
from package_pudo_api.data.pudo_etl import get_stock_summary, get_stock_details

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


@bp.get("/stock/<code_article>")
def stock_summary(code_article):
    try:
        df = get_stock_summary(code_article)
    except FileNotFoundError:
        return jsonify({"error": "stock parquet not found"}), 500

    if df.height == 0:
        return jsonify({"code_article": code_article, "rows": []}), 200

    rows = df.to_dicts()
    return jsonify({"code_article": code_article, "rows": rows}), 200


@bp.get("/stock/<code_article>/details")
def stock_details(code_article):
    try:
        df = get_stock_details(code_article)
    except FileNotFoundError:
        return jsonify({"error": "stock parquet not found"}), 500

    if df.height == 0:
        return jsonify({"code_article": code_article, "rows": []}), 200

    rows = df.to_dicts()
    return jsonify({"code_article": code_article, "rows": rows}), 200
