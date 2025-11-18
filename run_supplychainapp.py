import sys
import os
import threading
import time
import webbrowser
from pathlib import Path



def get_root_dir():
    # En mode exe PyInstaller, les fichiers sont sous sys._MEIPASS
    if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
        return Path(sys._MEIPASS)
    # En mode normal (python run_supplychainapp.py)
    return Path(__file__).parent

def run_frontend():
    import http.server
    import socketserver

    root = get_root_dir()
    frontend_dir = root / "package_pudo_frontend"
    os.chdir(frontend_dir)

    handler = http.server.SimpleHTTPRequestHandler
    with socketserver.TCPServer(("127.0.0.1", 8000), handler) as httpd:
        httpd.serve_forever()


def run_api():
    """Lance l'API Flask de package_pudo_api sur 127.0.0.1:5001."""
    from package_pudo_api.app import app

    # host/port cohérents avec ce que le frontend utilise (API_BASE_URL)
    # IMPORTANT: pas de debug/reloader dans un thread secondaire
    app.run(host="127.0.0.1", port=5001, debug=False, use_reloader=False)


def main():
    # Démarrer l'API et le frontend en parallèle
    t_api = threading.Thread(target=run_api, daemon=True)
    t_front = threading.Thread(target=run_frontend, daemon=True)
    t_api.start()
    t_front.start()

    # Laisser quelques secondes pour que les serveurs démarrent
    time.sleep(3)

    # Ouvrir le navigateur sur la page d'accueil
    try:
        webbrowser.open("http://127.0.0.1:8000/")
    except Exception:
        pass

    # Empêcher le script principal de se terminer tant que les threads tournent
    try:
        t_api.join()
        t_front.join()
    except KeyboardInterrupt:
        # Permettre de fermer proprement avec Ctrl+C en mode script
        pass


if __name__ == "__main__":
    main()
