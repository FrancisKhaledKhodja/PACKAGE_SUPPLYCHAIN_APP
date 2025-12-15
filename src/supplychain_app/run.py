import os
import threading
import time
import webbrowser


def run_frontend() -> None:
    import http.server
    import socketserver

    from supplychain_app.core.paths import get_web_dir

    web_dir = get_web_dir()
    os.chdir(web_dir)

    handler = http.server.SimpleHTTPRequestHandler
    with socketserver.TCPServer(("127.0.0.1", 8000), handler) as httpd:
        httpd.serve_forever()


def run_api() -> None:
    from supplychain_app.app import app

    app.run(host="127.0.0.1", port=5001, debug=False, use_reloader=False)


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


if __name__ == "__main__":
    main()
