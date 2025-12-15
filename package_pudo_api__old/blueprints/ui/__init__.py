import os
from flask import Blueprint

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
TEMPLATES_DIR = os.path.join(BASE_DIR, "frontend", "templates")
STATIC_DIR = os.path.join(BASE_DIR, "frontend", "static")

bp = Blueprint("ui", __name__, template_folder=TEMPLATES_DIR, static_folder=STATIC_DIR)

from . import routes  # noqa
