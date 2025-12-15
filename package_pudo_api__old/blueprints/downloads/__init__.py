from flask import Blueprint

bp = Blueprint("downloads", __name__)

from . import routes  # noqa
