from loguru import logger
import sys
import os

try:
    from supplychain_app.constants import path_supply_chain_app
except Exception:
    path_supply_chain_app = None

logger.remove()
_is_frozen = bool(getattr(sys, "frozen", False))
_console_sink = (
    getattr(sys, "__stderr__", None)
    or getattr(sys, "stderr", None)
    or getattr(sys, "__stdout__", None)
    or getattr(sys, "stdout", None)
)
_console_ok = (
    (not _is_frozen)
    and _console_sink is not None
    and hasattr(_console_sink, "write")
    and not bool(getattr(_console_sink, "closed", False))
)
if _console_ok:
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
