import os
import sys
import traceback
from datetime import datetime
import threading
import time
import webbrowser


def run_frontend() -> None:
    try:
        import http.server
        import socketserver

        from supplychain_app.core.paths import get_web_dir

        web_dir = get_web_dir()
        os.chdir(web_dir)

        handler = http.server.SimpleHTTPRequestHandler
        with socketserver.TCPServer(("127.0.0.1", 8000), handler) as httpd:
            httpd.serve_forever()
    except Exception:
        traceback.print_exc(file=sys.stderr)
        try:
            sys.stderr.flush()
        except Exception:
            pass


def run_api() -> None:
    try:
        from supplychain_app.app import app

        app.run(host="127.0.0.1", port=5001, debug=False, use_reloader=False)
    except Exception:
        traceback.print_exc(file=sys.stderr)
        try:
            sys.stderr.flush()
        except Exception:
            pass


def main() -> None:
    from supplychain_app.constants import path_supply_chain_app

    photos_dir = os.path.join(path_supply_chain_app, "photos")
    os.makedirs(photos_dir, exist_ok=True)

    t_api = threading.Thread(target=run_api, daemon=True)
    t_front = threading.Thread(target=run_frontend, daemon=True)
    t_api.start()
    t_front.start()

    time.sleep(3)

    try:
        webbrowser.open("http://127.0.0.1:8000/")
    except Exception:
        pass

    try:
        t_api.join()
        t_front.join()
    except KeyboardInterrupt:
        pass


def bootstrap() -> None:
    is_frozen = bool(getattr(sys, "frozen", False))
    crash_path = None
    if is_frozen:
        try:
            from supplychain_app.constants import path_supply_chain_app

            log_dir = os.path.join(path_supply_chain_app, "logs")
        except Exception:
            log_dir = os.path.dirname(sys.executable)

        try:
            os.makedirs(log_dir, exist_ok=True)
        except Exception:
            log_dir = os.path.dirname(sys.executable)

        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        crash_path = os.path.join(log_dir, f"exe_crash_{ts}.log")
        try:
            f = open(crash_path, "a", encoding="utf-8")
            sys.stdout = f
            sys.stderr = f
            f.write(f"=== SupplyChainApp EXE start {datetime.now().isoformat()} ===\n")
            f.flush()
        except Exception:
            crash_path = None

    try:
        main()
    except Exception:
        if is_frozen and crash_path:
            try:
                sys.stderr.write("\n=== Unhandled exception ===\n")
                traceback.print_exc(file=sys.stderr)
                sys.stderr.flush()
            except Exception:
                pass
        raise


if __name__ == "__main__":
    bootstrap()
