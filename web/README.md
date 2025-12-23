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
- `technician.html`, `technician_admin.html` (consultation magasin technicien + PR, distance/durée)
- `technician_assignments.html` (affectations technicien ↔ PR, distance/durée)
- `downloads.html` (téléchargements)
- `ol_mode_degrade.html` (ordre de livraison en mode dégradé pour les techniciens, génération d'e-mails DAHER / LM2S)

Technicians / PR:

- The pages use `GET /api/technicians/<code_magasin>/distances_pr` to display drive distance (meters → km) and duration (seconds → minutes).

URL parameters (deep links):

- `items.html?code=<CODE_ARTICLE>`: opens and focuses an item code.
- `items.html?q=<TEXTE_LIBRE>`: pre-fills the search and auto-runs.
- `items.html?ref_fab=<REFERENCE_FABRICANT>`: pre-fills the search with a manufacturer reference and auto-runs.
