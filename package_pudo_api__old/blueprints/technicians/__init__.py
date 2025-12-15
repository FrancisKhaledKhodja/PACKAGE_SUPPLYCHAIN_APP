from flask import Blueprint

bp = Blueprint("technicians", __name__)

from . import routes  # noqa
