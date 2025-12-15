import sys
from pathlib import Path


def get_project_root_dir() -> Path:
    if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
        return Path(sys._MEIPASS)
    return Path(__file__).resolve().parents[3]


def get_web_dir() -> Path:
    root = get_project_root_dir()
    web_dir = root / "web"
    return web_dir
