from flask import Flask
from .config import Config
from .extensions import cors
from .blueprints.auth import bp as auth_bp
from .blueprints.items import bp as items_bp
from .blueprints.pudo import bp as pudo_bp
from .blueprints.downloads import bp as downloads_bp
from .blueprints.stores import bp as stores_bp
from .blueprints.technicians import bp as technicians_bp
from .blueprints.helios import bp as helios_bp
from .blueprints.assistant import bp as assistant_bp
from .blueprints.consommables import bp as consommables_bp
import importlib.metadata
import threading
import time
import os
import sys
import re
from supplychain_app.data.pudo_etl import update_data, get_last_update_summary


def create_app(config_object: type[Config] = Config) -> Flask:
    app = Flask(__name__)
    app.config.from_object(config_object)

    # Extensions
    origins = app.config.get("CORS_ORIGINS", "*")
    if isinstance(origins, str) and "," in origins:
        origins = [o.strip() for o in origins.split(",") if o.strip()]
    cors.init_app(
        app,
        resources={r"/api/*": {"origins": origins}},
        supports_credentials=True,
    )

    # Blueprints
    app.register_blueprint(auth_bp, url_prefix="/api/auth")
    app.register_blueprint(items_bp, url_prefix="/api/items")
    app.register_blueprint(pudo_bp, url_prefix="/api/pudo")
    app.register_blueprint(downloads_bp, url_prefix="/api/downloads")
    app.register_blueprint(stores_bp, url_prefix="/api/stores")
    app.register_blueprint(technicians_bp, url_prefix="/api/technicians")
    app.register_blueprint(helios_bp, url_prefix="/api/helios")
    app.register_blueprint(assistant_bp, url_prefix="/api/assistant")
    app.register_blueprint(consommables_bp, url_prefix="/api/consommables")

    @app.get("/api/health")
    def health():
        return {"status": "ok"}

    @app.get("/api/updates/status")
    def updates_status():
        return get_last_update_summary()

    @app.get("/api/app/info")
    def app_info():
        is_frozen = bool(getattr(sys, "frozen", False))
        force_show_llm_rag = os.environ.get("SCAPP_FORCE_SHOW_LLM_RAG", "0").lower() in ("1", "true", "yes")
        hide_llm_rag_env = os.environ.get("SCAPP_HIDE_LLM_RAG", "0").lower() in ("1", "true", "yes")
        hide_llm_rag = hide_llm_rag_env or (is_frozen and not force_show_llm_rag)

        version = ""
        if is_frozen:
            try:
                exe_name = os.path.splitext(os.path.basename(sys.executable or ""))[0]
                m = re.search(r"v(?P<ver>\d+(?:\.\d+)*)", exe_name, flags=re.IGNORECASE)
                if m:
                    version = (m.group("ver") or "").strip()
            except Exception:
                version = ""

        if not version:
            version = (os.environ.get("SCAPP_VERSION") or "").strip()
        if not version:
            try:
                version = importlib.metadata.version("supplychain-app")
            except Exception:
                version = "dev"
        return {
            "is_frozen": is_frozen,
            "version": version,
            "hide_llm_rag": hide_llm_rag,
            "force_show_llm_rag": force_show_llm_rag,
            "hide_llm_rag_env": hide_llm_rag_env,
        }

    def _background_update_loop():
        while True:
            try:
                update_data()
            except Exception:
                pass
            time.sleep(1800)

    if not app.debug or os.environ.get("WERKZEUG_RUN_MAIN") == "true":
        t = threading.Thread(target=_background_update_loop, daemon=True)
        t.start()

    return app

