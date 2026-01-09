import sys
from pathlib import Path


def get_project_root_dir() -> Path:
    if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
        return Path(sys._MEIPASS)

    # When running from a dev workspace, prefer the current working directory (or its parents)
    # if it contains the expected web assets. This avoids serving a stale copy when the package
    # is imported from site-packages.
    try:
        cwd = Path.cwd().resolve()
        for p in (cwd, *cwd.parents):
            web = p / "web"
            expected = [
                web / "article_request.html",
                web / "home.html",
                web / "treatments.html",
            ]
            if all(c.exists() for c in expected):
                return p
    except Exception:
        pass

    return Path(__file__).resolve().parents[3]


def get_web_dir() -> Path:
    root = get_project_root_dir()
    web_dir = root / "web"
    return web_dir
