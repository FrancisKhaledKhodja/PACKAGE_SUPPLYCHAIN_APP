from flask import Blueprint

bp = Blueprint("pudo", __name__)

from . import routes  # noqa
