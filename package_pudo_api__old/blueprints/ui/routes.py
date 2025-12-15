from flask import render_template, request, jsonify, session
from . import bp

@bp.get("/")
def home_page():
    return render_template("base.html")

@bp.get("/items")
def items_page():
    return render_template("items.html")

@bp.get("/downloads")
def downloads_page():
    return render_template("downloads.html")


@bp.post("/set-proxy-credentials")
def set_proxy_credentials():
    body = request.get_json(silent=True) or {}
    login = body.get("login")
    password = body.get("password")

    if not login or not password:
        return jsonify({"error": "login and password are required"}), 400

    session["proxy_login"] = login
    session["proxy_password"] = password
    return jsonify({"status": "ok"}), 200
