import os
import sys
import traceback
from datetime import datetime

def _early_log_path() -> str:
    base_dir = os.path.dirname(getattr(sys, "executable", "")) or os.getcwd()
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    return os.path.join(base_dir, f"early_boot_{ts}.log")

if __name__ == "__main__":
    early_path = _early_log_path()
    try:
        with open(early_path, "a", encoding="utf-8") as f:
            f.write(f"=== Early boot start {datetime.now().isoformat()} ===\n")
            f.flush()

        from supplychain_app.run import bootstrap

        bootstrap()
    except Exception:
        try:
            with open(early_path, "a", encoding="utf-8") as f:
                f.write("\n=== Unhandled exception during early boot ===\n")
                traceback.print_exc(file=f)
                f.flush()
        except Exception:
            pass
        raise
