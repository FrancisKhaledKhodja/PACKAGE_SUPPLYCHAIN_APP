from flask import Blueprint

bp = Blueprint("consommables", __name__)

from . import routes  # noqa
