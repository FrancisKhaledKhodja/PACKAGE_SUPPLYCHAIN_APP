import os
import sys
import traceback
from datetime import datetime
import threading
import time
import webbrowser
import socket


FRONTEND_HOST = "127.0.0.1"
FRONTEND_DEFAULT_PORT = 8000
_frontend_port: int | None = None
_frontend_port_ready = threading.Event()
_frontend_httpd = None
_api_httpd = None
_shutdown_lock = threading.Lock()
_shutdown_started = False


def run_frontend() -> None:
    try:
        import http.server
        import socketserver
        import urllib.request

        from supplychain_app.core.paths import get_web_dir

        web_dir = get_web_dir()
        os.chdir(web_dir)

        class NoCacheHandler(http.server.SimpleHTTPRequestHandler):
            def end_headers(self):
                self.send_header("Cache-Control", "no-store, no-cache, must-revalidate, max-age=0")
                self.send_header("Pragma", "no-cache")
                self.send_header("Expires", "0")
                return super().end_headers()

        handler = NoCacheHandler

        class ReusableTCPServer(socketserver.ThreadingTCPServer):
            allow_reuse_address = True
            daemon_threads = True

        def probe_http(port: int) -> bool:
            try:
                url = f"http://{FRONTEND_HOST}:{port}/"
                req = urllib.request.Request(url, method="GET")
                with urllib.request.urlopen(req, timeout=0.4) as r:
                    return 200 <= int(getattr(r, "status", 200)) < 500
            except Exception:
                return False

        def pick_port(start: int, max_tries: int = 20) -> int:
            for p in range(start, start + max_tries):
                try:
                    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                        s.bind((FRONTEND_HOST, p))
                    return p
                except OSError:
                    continue
            return start

        global _frontend_port
        _frontend_port = pick_port(FRONTEND_DEFAULT_PORT)
        _frontend_port_ready.set()

        global _frontend_httpd
        with ReusableTCPServer((FRONTEND_HOST, _frontend_port), handler) as httpd:
            _frontend_httpd = httpd
            httpd.serve_forever()
    except Exception:
        traceback.print_exc(file=sys.stderr)
        try:
            sys.stderr.flush()
        except Exception:
            pass


def run_api() -> None:
    try:
        from werkzeug.serving import make_server
        from supplychain_app.app import app

        global _api_httpd
        _api_httpd = make_server("127.0.0.1", 5001, app, threaded=True)
        _api_httpd.serve_forever()
    except Exception:
        traceback.print_exc(file=sys.stderr)
        try:
            sys.stderr.flush()
        except Exception:
            pass


def _shutdown_all() -> None:
    global _shutdown_started
    with _shutdown_lock:
        if _shutdown_started:
            return
        _shutdown_started = True

    def do():
        try:
            if _api_httpd is not None:
                try:
                    _api_httpd.shutdown()
                except Exception:
                    pass
        finally:
            try:
                if _frontend_httpd is not None:
                    try:
                        _frontend_httpd.shutdown()
                    except Exception:
                        pass
            finally:
                os._exit(0)

    threading.Thread(target=do, daemon=True).start()


def main() -> None:
    from supplychain_app.constants import path_supply_chain_app
    from supplychain_app.app import app

    photos_dir = os.path.join(path_supply_chain_app, "photos")
    os.makedirs(photos_dir, exist_ok=True)

    t_api = threading.Thread(target=run_api, daemon=True)
    t_front = threading.Thread(target=run_frontend, daemon=True)

    app.config["SCAPP_EXIT_CALLBACK"] = _shutdown_all
    t_api.start()
    t_front.start()

    _frontend_port_ready.wait(timeout=3)
    port = _frontend_port or FRONTEND_DEFAULT_PORT

    # Wait until API is reachable to avoid frontend login failing due to race condition
    try:
        import urllib.request

        api_url = "http://127.0.0.1:5001/api/health"
        deadline = time.time() + 6.0
        while time.time() < deadline:
            try:
                with urllib.request.urlopen(api_url, timeout=0.4) as r:
                    if 200 <= int(getattr(r, "status", 200)) < 500:
                        break
            except Exception:
                pass
            time.sleep(0.2)
    except Exception:
        pass

    time.sleep(0.5)

    try:
        webbrowser.open(f"http://{FRONTEND_HOST}:{port}/")
    except Exception:
        pass

    def watchdog():
        while True:
            try:
                last = float(app.config.get("SCAPP_LAST_PING_TS") or 0.0)
            except Exception:
                last = 0.0
            if last and (time.time() - last) > 45:
                _shutdown_all()
                return
            time.sleep(5)

    threading.Thread(target=watchdog, daemon=True).start()

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
