from loguru import logger
import sys

logger.remove()
_console_sink = sys.stderr if getattr(sys, "stderr", None) else (sys.stdout if getattr(sys, "stdout", None) else None)
if _console_sink is not None:
    logger.add(_console_sink, level="INFO")
logger.add("application.log", level="INFO")
