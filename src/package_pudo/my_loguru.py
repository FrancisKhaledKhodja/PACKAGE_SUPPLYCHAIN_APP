from loguru import logger
import sys
import os

try:
    from supplychain_app.constants import path_supply_chain_app
except Exception:
    path_supply_chain_app = None

logger.remove()
_console_sink = sys.stderr if getattr(sys, "stderr", None) else (sys.stdout if getattr(sys, "stdout", None) else None)
if _console_sink is not None:
    logger.add(_console_sink, level="INFO")

_default_log_path = "application.log"
if path_supply_chain_app:
    try:
        log_dir = os.path.join(path_supply_chain_app, "logs")
        os.makedirs(log_dir, exist_ok=True)
        _default_log_path = os.path.join(log_dir, "application.log")
    except Exception:
        _default_log_path = "application.log"

os.environ.setdefault("SCAPP_LOG_PATH", _default_log_path)
logger.add(os.environ.get("SCAPP_LOG_PATH", _default_log_path), level="INFO")
