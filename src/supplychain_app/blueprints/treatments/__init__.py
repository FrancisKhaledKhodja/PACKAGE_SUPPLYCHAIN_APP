from flask import Blueprint

bp = Blueprint("treatments", __name__)

from . import routes  # noqa: E402,F401
