from flask import Blueprint

bp = Blueprint("assistant", __name__)

from . import routes  # noqa: E402,F401
