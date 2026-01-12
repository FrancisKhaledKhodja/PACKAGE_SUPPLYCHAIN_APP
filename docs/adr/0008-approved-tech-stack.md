# ADR 0008 — Technologies autorisées (stack maîtrisé)

## Statut

Accepté

## Contexte

SupplyChainApp est un outil local (Windows) destiné à des usages métiers. L'objectif est de conserver un socle technique simple à maintenir, en limitant la dépendance à des technologies non maîtrisées.

## Décision

### 1) Technologies autorisées par défaut

Le projet doit se limiter aux technologies suivantes :

- **Backend / scripts** : Python
- **Dataframes** : Pandas, Polars
- **Frontend** : HTML, CSS, JavaScript

Technologies explicitement autorisées (exceptions validées) :

- **API / serveur** : Flask, flask-cors
- **HTTP client** : requests
- **Logging** : loguru
- **Parquet** : pyarrow
- **Excel** : openpyxl, xlsxwriter, fastexcel
- **Windows** : pywin32
- **Packaging** : pyinstaller
- **Cartographie (frontend)** : Leaflet
- **Dataviz (frontend)** : D3.js
- **Normalisation de texte** : unidecode

### 2) Règle d'introduction d'une nouvelle technologie

Toute nouvelle technologie (framework frontend, librairie JS, librairie Python, runtime externe, etc.) doit :

- être explicitement justifiée (besoin métier/technique clair),
- être validée avant intégration,
- être ajoutée/mentionnée dans cette ADR (ou une ADR dédiée si nécessaire).

### 3) Tolérance / exception pour l'existant

Certaines dépendances sont déjà présentes dans le codebase ou nécessaires à l'exécution actuelle (ex : serveur HTTP/API, packaging, parsing HTML, cartographie). Elles restent tolérées tant qu'elles ne complexifient pas inutilement le projet.

## Conséquences

- **Positives**
  - Maintenance simplifiée.
  - Évolutions plus rapides (moins de dispersion technique).
  - Réduction du risque de dette technique liée à des technos non maîtrisées.

- **Négatives / Risques**
  - Certaines fonctionnalités pourraient être plus coûteuses à implémenter sans framework dédié.
  - Nécessite une discipline de revue lors de l'ajout de dépendances.

- **Alternatives considérées**
  - Autoriser librement de nouvelles technos : rejeté (risque de dérive du stack et de complexité).
