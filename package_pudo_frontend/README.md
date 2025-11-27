# Frontend

Static HTML/CSS/JS frontend served by a simple HTTP server.

The Flask API is available on `http://127.0.0.1:5001/api/*` and is consumed via AJAX from these pages.

In development, the frontend is served automatically by `run_supplychainapp.py` using `http.server` on `http://127.0.0.1:8000/`.

Entry points:

- `index.html` / `base.html`-style layout
- `items.html` (recherche articles / info article)
- `stock.html`, `stock_detailed.html` (stocks agrégés et détaillés)
- `helios.html` (parc installé)
- `stores.html` (magasins & points relais)
- `downloads.html` (téléchargements)
