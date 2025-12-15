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
import threading
import time
import os
import sys
from supplychain_app.data.pudo_etl import update_data, get_last_update_summary


def create_app(config_object: type[Config] = Config) -> Flask:
    app = Flask(__name__)
    app.config.from_object(config_object)

    # Extensions
    cors.init_app(
        app,
        resources={r"/api/*": {"origins": app.config.get("CORS_ORIGINS", "*")}},
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

    @app.get("/api/health")
    def health():
        return {"status": "ok"}

    @app.get("/api/updates/status")
    def updates_status():
        return get_last_update_summary()

    @app.get("/api/app/info")
    def app_info():
        is_frozen = bool(getattr(sys, "frozen", False))
        return {
            "is_frozen": is_frozen,
            "hide_llm_rag": is_frozen,
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

