from flask import Blueprint

try:
    from .routes import bp  # noqa: F401
except Exception:
    bp = Blueprint("assistant", __name__)
