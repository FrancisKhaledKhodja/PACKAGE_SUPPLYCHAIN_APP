# SupplyChainApp

Application Python pour la gestion SupplyChain (PUDO, stocks, Helios, statistiques de sorties, etc.).

Ce document résume :

- comment installer les dépendances du projet,
- comment lancer l'application en mode développeur,
- comment construire un exécutable Windows (`.exe`) avec PyInstaller.

---

## Documentation

- **Spécification métier** : `docs/spec/SPEC_METIER_SUPPLYCHAINAPP.md`
- **Décisions d’architecture (ADR)** : `docs/adr/`
- **Checklist PR** : `.github/pull_request_template.md`

Dernières ADR notables :

- `docs/adr/0004-application-lifecycle-shutdown.md` (heartbeat, bouton Quitter, auto-stop)

---

## 0. Installation & environnement

### 0.1. Prérequis

- **Python 3.13+** (conforme au `pyproject.toml`)
- Windows (tests et packaging ciblés sur cette plateforme)
- Accès aux fichiers sources métiers (parquets, etc.) attendus par l'application.

### 0.2. Installation des dépendances avec `uv` (recommandé)

Les dépendances de l'application sont décrites dans `pyproject.toml` et figées dans `uv.lock`.

Depuis la racine du projet :

```powershell
uv sync
```

Optionnel :

- installer les dépendances "LLM" (RAG / embeddings) :

```powershell
uv sync --extra llm
```

- installer les dépendances de build (PyInstaller) :

```powershell
uv sync --extra build
```

`uv` crée/actualise automatiquement l'environnement virtuel et installe toutes les dépendances déclarées.

### 0.3. Installation des dépendances sans `uv` (option manuelle)

Si `uv` n'est pas disponible, il est possible d'utiliser un environnement virtuel classique :

```powershell
python -m venv .venv
 .\.venv\Scripts\Activate.ps1
python -m pip install -U pip
python -m pip install -e .
```

---

## 0.4. Architecture de l'application

Vue d'ensemble des principaux composants :

```text
        +-------------------------+
        |  Utilisateur / Navigateur|
        +-------------+-----------+
                      |
                      | HTTP (port 8000)
                      v
        +-------------+-----------+
        |   Frontend statique     |
        |  (web/)                 |
        |  HTML / CSS / JS        |
        +-------------+-----------+
                      |
                      | HTTP (AJAX, port 5001)
                      v
        +-------------+-----------+
        |   API Flask             |
        |  (src/supplychain_app)  |
        |  /api/items, /api/pudo, |
        |  /api/stores, /api/...  |
        +-------------+-----------+
                      |
                      | Accès fichiers / ETL
                      v
        +-------------+-----------+
        | Données métiers         |
        | (parquets, Excel, etc.) |
        | path_supply_chain_app   |
        +-------------------------+
```

- `py -m supplychain_app.run` :
  - démarre **l'API Flask** sur `http://127.0.0.1:5001/api/*` ;
  - démarre un **serveur HTTP** pour le frontend (dossier `web/`) sur `http://127.0.0.1:8000/` ;
    - si le port `8000` est déjà occupé, l'application tente `8001`, `8002`, etc.
  - ouvre automatiquement le navigateur sur l'URL frontend (port effectif).
- `src/supplychain_app` :
  - organise l'API en **blueprints** (`items`, `pudo`, `stores`, `helios`, `technicians`, `downloads`, etc.) ;
  - expose aussi des endpoints techniques (`/api/health`, `/api/updates/status`).
- `src/supplychain_app.data.pudo_etl` :
  - gère les **tâches d'ETL** (chargement/parquetisation, mise à jour périodique dans `path_datan/<folder_name_app>`).
- Binaire PyInstaller (`SupplyChainApp.exe`) :
  - embarque le même code Python et le dossier `web/` ;
  - reproduit exactement le comportement de `py -m supplychain_app.run` sans dépendre de Python installé sur le poste utilisateur.

---

## 1. Lancer l'application en mode développeur

### 1.1. Activer l'environnement virtuel principal

Depuis la racine du projet :

```powershell
# Windows PowerShell
.\.venv\Scripts\Activate.ps1
```

Le prompt doit afficher quelque chose comme :

```text
(package-supplychain-app) PS C:\...>
```

### 1.2. Démarrer l'application

Toujours depuis la racine du projet :

```powershell
py -m supplychain_app.run
```

Ce script :

- démarre l'API Flask sur `http://127.0.0.1:5001`,
- démarre un petit serveur HTTP pour le frontend sur `http://127.0.0.1:8000`,
- ouvre automatiquement le navigateur sur `http://127.0.0.1:8000/`.

Pour arrêter :

- **Recommandé (UI)** : cliquer sur **Quitter** (bouton dans le header).
- **Alternative** : fermer toutes les pages/onglets de l'application ; un watchdog arrête automatiquement les serveurs au bout d'environ 45s sans activité.
- **Mode terminal** : `Ctrl + C` (si l'application est lancée depuis un terminal).

Endpoints techniques associés :

- `POST /api/app/ping` : heartbeat envoyé par le navigateur.
- `POST /api/app/exit` : arrêt propre des serveurs (utilisé par le bouton **Quitter**).

### 1.3. Assistant : modes de fonctionnement (règles vs Ollama)

L'assistant de navigation (`POST /api/assistant/query`) peut fonctionner selon 3 modes, pilotés par variables d'environnement :

- `ASSISTANT_MODE=rules` : routeur déterministe à règles (par défaut, fonctionne partout, ne dépend d'aucun LLM)
- `ASSISTANT_MODE=ollama` : tente d'utiliser Ollama en local
- `ASSISTANT_MODE=auto` : tente Ollama, puis bascule automatiquement vers les règles si Ollama est indisponible

Variables Ollama :

- `ASSISTANT_OLLAMA_URL` (défaut `http://127.0.0.1:11434`)
- `ASSISTANT_OLLAMA_MODEL` (défaut `llama3.1`)
- `ASSISTANT_OLLAMA_TIMEOUT_S` (défaut `15`)

#### 1.3.1. Endpoints assistant

- `POST /api/assistant/query` : point d'entrée principal (utilisé par l'input "Poser une question" de `home.html`).
- `GET /api/assistant/capabilities` : expose la table des intents supportés par le routeur à règles (page cible, schéma des paramètres, exemples).

#### 1.3.2. Navigation et paramètres d'URL (conventions)

L'assistant ne “calcule” pas de données métier : il renvoie uniquement un JSON `{answer, intent, params, target_page}`.
Le frontend ouvre ensuite la page cible avec des paramètres d'URL compatibles avec les pages existantes :

- `stock.html?code=<CODE_ARTICLE>`
- `items.html?code=<CODE_ARTICLE>`
- `photos.html?code=<CODE_ARTICLE>`
- `helios.html?code=<CODE_ARTICLE>`
- `stock_map.html?code=<CODE_ARTICLE>&address=<ADRESSE>`
- `stores.html?q=<ADRESSE_OU_VILLE>`
- `technician.html?q=<CODE_MAGASIN_OU_RECHERCHE>`
- `technician_assignments.html?store=<CODE>&pr=<CODE>&status=<ouvert|ferme>&roles=<role>&expand_store_roles=1`

Exemples de questions typiques :

- "Quel est le stock du code article TDF000629 ?" → `stock.html?code=TDF000629`
- "Où localiser le stock de TDF000629 autour de Lyon ?" → `stock_map.html?code=TDF000629&address=Lyon`
- "Quels sont les points relais proches de Bergerac ?" → `stores.html?q=Bergerac`
- "Quelles sont les photos de TDF000629 ?" → `photos.html?code=TDF000629`

---

## 2. Construire un exécutable Windows avec PyInstaller

La construction de l'exécutable se fait directement depuis l'environnement virtuel principal `.venv`.

### 2.1. Préparer l'environnement de build

1. Activer l'environnement virtuel (si ce n'est pas déjà fait) :

```powershell
.\.venv\Scripts\Activate.ps1
```

2. Installer PyInstaller (une seule fois) si nécessaire, ainsi que le projet en mode éditable :

```powershell
python -m pip install -e . pyinstaller
```

Une fois ces commandes exécutées, toutes les dépendances de l'application ainsi que PyInstaller sont disponibles dans `.venv`.

### 2.2. Commande PyInstaller (via le fichier .spec)

Depuis la racine du projet, avec `.venv` activé :

```powershell
pyinstaller --clean SupplyChainApp.spec
```

Cette commande utilise la configuration de build décrite dans `SupplyChainApp.spec` (point d'entrée, données embarquées, options PyInstaller, etc.).

> Remarque :
> - si un module n'est pas correctement détecté par PyInstaller, il est possible d'ajouter une option `--hidden-import nom_du_module` dans le fichier `.spec` ou en ligne de commande ;
> - les fichiers `.spec` fournis permettent de rejouer des configurations de build existantes.

#### Alternative : commande directe sans `.spec`

Il est également possible de construire l'exécutable sans utiliser le fichier `.spec` (utile pour un premier build rapide) :

```powershell
pyinstaller --noconfirm --clean --onefile --name SupplyChainApp --add-data "web;web" src\supplychain_app\run.py
```

Les options sont identiques à celles des versions précédentes :

- `--onefile` : génère un seul fichier `.exe` autonome.
- `--name SupplyChainApp` : nom du binaire généré.
- `--add-data "web;web"` : embarque le dossier frontend dans l'exécutable (Windows utilise `;` comme séparateur source/destination).
- `src\supplychain_app\run.py` : point d'entrée qui démarre API + frontend.

#### Script de build recommandé

Depuis la racine du projet, avec `.venv` activé :

```powershell
./scripts/build_exe.ps1
```

#### Script de build EXE « NoLLM » (distribution interne)

Depuis la racine du projet, avec `.venv` activé :

```powershell
./scripts/build_exe_no_llm.ps1
```

Ce script génère un exécutable nommé selon le modèle :

```text
dist\SUPPLYCHAIN_APP_v1.6.0.exe
```

### 2.3. Résultat

PyInstaller génère :

- un exécutable dans `dist/` :

```text
C:\...\PACKAGE_SUPPLYCHAIN_APP\dist\SUPPLYCHAIN_APP_v1.6.0.exe
```

- des fichiers intermédiaires dans `build/` (peuvent être supprimés si besoin).

### 2.4. Lancer l'exécutable

Depuis un terminal :

```powershell
cd .\dist\
.\SupplyChainApp.exe
```

L'exécutable :

- démarre l'API et le serveur frontend,
- ouvre le navigateur sur `http://127.0.0.1:8000/`,
- affiche les logs dans la console (si construit sans `--windowed`).

### 2.5. Capturer les logs en cas de crash de l'EXE

En cas de plantage très tôt au lancement (ex: erreur d'import), un fichier est créé à côté de l'EXE :

```text
early_boot_YYYYMMDD_HHMMSS.log
```

Une fois l'application démarrée (après `bootstrap()`), un log peut aussi être écrit dans le dossier `logs/` de l'application (ou à côté de l'EXE en fallback) :

```text
exe_crash_YYYYMMDD_HHMMSS.log
```

Ces fichiers permettent de diagnostiquer les erreurs rencontrées dans l'exécutable PyInstaller.

---

## 3. Fonctionnalités principales

L'application frontend (dossier `web/`) propose plusieurs onglets principaux accessibles depuis le header.

Navigation (header) :

- les liens sont regroupés en menus déroulants pour réduire la charge visuelle :
  - **STOCK**
  - **RÉFÉRENTIEL ARTICLE**
  - **PR & MAGASINS**
  - **APPLICATIONS / OUTILS**
- le lien **ASSISTANT (LLM+RAG)** peut apparaître selon la configuration (`/api/app/info`).

- **Accueil** : page d'entrée de l'application.
- **info_article (`items.html`)** :
  - recherche avancée d'articles,
  - affichage détaillé d'un article (données PIM, compta, logistique, etc.),
  - visualisation de la **nomenclature** de l'article,
  - affichage des **références fournisseurs** et des **articles équivalents**.
- **RECHERCHE_STOCK (`stock.html`)** :
  - recherche d'article puis affichage du stock agrégé par magasin / type de dépôt,
  - lien direct vers le stock détaillé et vers l'onglet info_article.
- **Stock détaillé (`stock_detailed.html`)** :
  - détail du stock par magasin et par emplacement pour un article donné.
- **Parc Helios (`helios.html`)** :
  - synthèse du parc installé par code article.
- **Magasins & points relais (`stores.html`)** :
  - recherche et infos de contact des magasins et points relais.
- **Stock ultra détaillé** :
  - vue API/exports permettant d’analyser le stock `lot / série / projet / colis` avec date de stock pour un article donné (cf. endpoint `/api/auth/stock/<code_article>/ultra-details`).
- **Localisation du stock (`stock_map.html`)** :
  - carte (Leaflet) montrant les magasins/dépôts :
    - soit ayant du stock pour un ou plusieurs **codes article** saisis ;
    - soit, si aucun code article n’est saisi, les **magasins actifs** (statut magasin = 0) correspondant au **type de dépôt** choisi, avec ou sans stock ;
  - filtres sur type de dépôt (avec case « tout cocher/décocher »), qualité, type de stock, option **HORS TRANSIT** ;
  - markers colorés par **type de dépôt** (NATIONAL, LOCAL, REO, LABORATOIRE, etc.) avec une légende sous la carte ;
  - calcul optionnel de la distance par rapport à un point de référence (code IG ou adresse) ;
  - bouton d’**export Excel** permettant de récupérer un fichier CSV (`localisation_stock.csv`) basé sur `stock_final.parquet`, respectant les filtres courants, uniquement si des résultats existent.
- **Téléchargements (`downloads.html`)** :
  - accès aux exports générés (stock détaillé, statistiques de sorties, PUDO, etc.).
- **Catalogue consommables (`catalogue_consommables.html`)** :
  - liste d'une **offre de consommables** (consultable sur smartphone) construite à partir d'un fichier Excel,
  - recherche texte + filtre par catégorie,
  - l'offre peut être mise à jour quotidiennement par simple dépôt d'un nouveau fichier.
- **Demande création / modification article (`article_request.html`)** :
  - saisie d'une demande via un tableau multi-lignes :
    - **Création d'article(s)** (mode formulaire ou feuille multi-lignes)
    - **Modification d'une criticité**
    - **Modification du statut achetable / non achetable**
    - **Déclaration d'une équivalence**
    - **Demande de passage en REBUT**
  - règles métiers & contrôles (création d'article) :
    - la page est servie par le **frontend** sur `http://127.0.0.1:8000/` (fichiers statiques `web/`) ;
    - les contrôles et exports s'appuient sur l'**API Flask** sur `http://127.0.0.1:5001/api/*`.
    - bloc **REFERENCE FABRICANT** :
      - l'utilisateur renseigne **Fabricant**, **Référence fabricant**, **Prix prévisionnel**.
      - un encart d'aide (Étape 1) guide la saisie.
    - normalisation des saisies texte (comportement UI) :
      - les champs texte (ex: référence fabricant, libellés, etc.) sont normalisés en **MAJUSCULES** et **sans accents** à la sortie du champ (blur).
      - exception : **Commentaire technique** n'est pas contraint (pas de conversion automatique, accents autorisés).
    - contraintes de longueur :
      - **Libellé court** : `120` caractères max, affichage en **textarea** + compteur.
      - **Libellé long** : `240` caractères max, affichage en **textarea** + compteur.
      - **Référence fabricant** : compteur indicatif sur `31` caractères conseillés.
    - contrôle anti-doublon sur la **référence fabricant** (PIM) :
      - au blur, l'application appelle `GET /api/items/pim/check_reference_fabricant?reference=...`.
      - la recherche se fait dans `manufacturers.parquet` / `manufacturer(s).parquet` sur la colonne `reference_article_fabricant`.
      - la comparaison normalise majuscules/sans accents et gère les espaces multiples / NBSP.
      - si une correspondance est trouvée, un **lien** est affiché : il ouvre `items.html` pré-filtré sur la référence (`items.html?ref_fab=...`) pour afficher la liste des articles correspondants.
  - auto-remplissage de champs article à partir du code article (appel API `/api/items/<code>/details`),
  - génération d'un email via `mailto:` vers `referentiel_logistique@tdf.fr` (objet standardisé + corps en TSV),
  - génération serveur d'un fichier Excel de demande et **sauvegarde automatique sur un partage réseau**,
  - limitation connue : `mailto:` ne permet pas d'attacher automatiquement un fichier (pièce jointe).
- **Écrans techniciens / affectations technicien ↔️ PUDO** :
  - écrans dédiés au suivi des techniciens, de leurs magasins de rattachement et de leurs PUDO (principal / backup / hors normes).
  - affichage optionnel de la **distance** (mètres → km) et de la **durée** (secondes → minutes) entre le magasin et ses PR (source : `distance_tech_pr.parquet`).

### 3.5. Demande de modification article (criticité)

- Page frontend : `web/article_request.html`
- Flux :
  - l'utilisateur renseigne le **type de demande**, son **prénom/nom**, et une ou plusieurs lignes (code article / nouvelle criticité / cause),
  - au clic sur **Valider** :
    - un fichier Excel est généré côté serveur (openpyxl) et sauvegardé sur un partage réseau,
    - un email `mailto:` est ouvert avec un sujet standard et un corps au format TSV.

Endpoints backend :

- `POST /api/downloads/demandes/modif_criticite_xlsx`
  - sauvegarde un fichier `dde_modif_art_criticite_YYYYMMDDTHHMMSS.xlsx` dans :
    - `\\apps\Vol1\Data\011-BO_XI_entrees\07-DOR_DP\Sorties\FICHIERS_REFERENTIEL_ARTICLE\DEMANDES`

- `POST /api/downloads/demandes/modif_achetable_xlsx`
  - sauvegarde un fichier `dde_modif_art_achetable_YYYYMMDDTHHMMSS.xlsx` dans le même répertoire.

- `POST /api/downloads/demandes/equivalence_xlsx`
  - sauvegarde un fichier `dde_equivalence_YYYYMMDDTHHMMSS.xlsx` dans le même répertoire.

- `POST /api/downloads/demandes/passage_rebut_xlsx`
  - sauvegarde un fichier `dde_passage_rebut_YYYYMMDDTHHMMSS.xlsx` dans le même répertoire.

- `POST /api/downloads/demandes/creation_articles_xlsx`
  - sauvegarde un fichier `dde_creation_article_YYYYMMDDTHHMMSS.xlsx` dans le même répertoire.

Notes :

- La sauvegarde sur partage nécessite que le process de l'API (ou l'EXE PyInstaller) ait les droits d'écriture sur le répertoire.
- Le `mailto:` est soumis à une limite de longueur d'URL (limite conservative utilisée: ~1800 caractères). Si dépassement, un message est affiché.

### 3.6. Assistant LLM+RAG (analyse & code Polars)

Le projet expose un endpoint "LLM+RAG" qui combine :

- un contexte RAG (index Chroma) pour identifier tables/jointures,
- une génération de code Polars,
- et, pour certains cas, une réponse **déterministe** basée sur les fichiers Parquet.

Endpoints :

- `POST /api/assistant/llm_rag` : répond à une question et renvoie :
  - `answer` (texte),
  - `polars_code` (script proposé),
  - `plan` (tables/jointures/colonnes),
  - `rag.hits` (contexte).

Cas déterministe implémenté :

- Demandes du type : "Pour un projet, besoin de 5 unités du code article TDF...".
- Analyse sur `stock_final.parquet` :
  - stock GOOD sur le projet `PJ00000564`,
  - stock GOOD sur autres projets `PJ*` groupé par ancienneté (plus ancien prioritaire),
  - stock GOOD en maintenance,
  - stock BAD (BAD + BLOQB) pour suggérer des réparations.

### 3.1. Catégorie "sans sortie" (categorie_sans_sortie)

Une nouvelle information est disponible pour les articles : la **catégorie sans sortie** (`categorie_sans_sortie`), calculée à partir des sorties historiques et stockée dans le fichier parquet `items_without_exit_final.parquet`.

- Cette catégorie est **chargée automatiquement** côté backend et copiée dans le répertoire de travail de l'application (`path_datan/<folder_name_app>/items_without_exit_final.parquet`).
- Une API dédiée expose cette information :
  - `GET /api/items/<code>/categorie-sans-sortie` → retourne `code_article` et `categorie_sans_sortie`.
- Côté frontend :
  - dans l'onglet **info_article** :
    - un bloc "Catégorie sans sortie" apparaît dans le panneau de détails, sous forme de badge coloré ;
  - dans l'onglet **RECHERCHE_STOCK** :
    - la `categorie_sans_sortie` est affichée dans le résumé de l'article sélectionné (badge coloré).

Le code couleur est le suivant :

- `"1 - moins de 2 mois"` → `#33CC00`
- `"2 - entre 2 et 6 mois"` → `#66AA00`
- `"3 - entre 6 mois et 1 an "` → `#999900`
- `"4 - entre 1 et 2 ans"` → `#CC6600`
- `"5 - entre 2 et 5 ans"` → `#FF3300`
- `"6 - entre 5 et 10 ans"` → `#FF0000`
- toute autre valeur → `#FF0000`

### 3.2. Recherche sur les champs fournisseurs

La recherche d'articles (`/api/items/search`) utilise le parquet `items.parquet` **enrichi** des informations de `manufacturers.parquet` :

- les colonnes de `manufacturers` sont agrégées par `code_article` dans un texte global,
- ce texte est intégré au "haystack" de recherche,
- **taper un nom de fournisseur ou une référence fabricant** permet donc de retrouver un article aussi bien dans :
  - l'onglet **info_article**,
  - que dans l'onglet **RECHERCHE_STOCK**.

### 3.3. Mise à jour automatique des données

L'API démarre un thread en arrière-plan qui appelle régulièrement `update_data()` :

- toutes les **30 minutes**, l'application :
  - vérifie si de nouveaux fichiers sources sont disponibles (annuaire PR, stores, items, minmax, stats de sorties, etc.),
  - recalcule / recopie les parquets nécessaires dans `path_datan/<folder_name_app>`.
- un endpoint expose l'état de la dernière mise à jour :
  - `GET /api/updates/status` → `{ "has_changes": bool, "timestamp": UNIX }`.
- le frontend interroge régulièrement ce statut et affiche un message dans le header :
  - bandeau sous le menu de navigation (`scapp-update-banner`),
  - message du type : `Données mises à jour à HHhMM`.

---

### 3.4. OL MODE DÉGRADÉ V2 (`ol_mode_degrade_v2.html`)

Écran dédié à la création d’**ordres de livraison en mode dégradé** pour les techniciens, avec intégration d’une carte et d’un tableau de stock unifié.

- Sélection d’un technicien, récupération automatique de son magasin, de ses coordonnées, de son **PR principal** et de son **PR hors normes**.
- Saisie d’un ou plusieurs **codes article** (séparés par `;`), avec récupération des magasins ayant du stock selon les filtres choisis.
- Choix du type de commande : `STANDARD`, `URGENT`, `MAD`.
- Choix de l’adresse de livraison (bloc "Lieu de livraison") :
  - **Code IG**,
  - **Point relais** (principal / hors normes),
  - **Adresse libre** (adresse, CP, ville obligatoires).

#### 3.4.1. Carte et visualisation des stocks

- Carte Leaflet affichant :
  - les **magasins avec stock** pour les articles saisis (un marker par magasin),
  - le **point de référence** (centre) si défini,
  - en STANDARD : les points relais **principal** et **hors normes** du technicien (avec enseigne + adresse dans le popup).
- Chaque marker magasin affiche :
  - code + libellé magasin,
  - adresse postale,
  - distance (km) par rapport au centre (si calculée),
  - une ligne par article avec la quantité de stock.
- Les magasins ayant **tous les articles demandés** sont mis en évidence par un marker de couleur différente.

#### 3.4.2. Tableau des résultats et règles de tri

- Tableau listant les magasins en stock avec, entre autres, les colonnes :
  - `Code article`, `Code magasin`, `Libellé magasin`, `Type de dépôt`, `Code qualité`, `Type stock (M/D)`,
  - `Qté stock totale`, `Tous les articles en stock`, `Distance centre (km)`,
  - en STANDARD/URGENT : `Dist. PR principal (km)`, `Dist. PR hors normes (km)`.
- Colonne **"Tous les articles en stock"** :
  - affiche `Oui` / `Non` par magasin, en fonction de la présence de **tous les articles saisis**.
- Règles de tri :
  - en **STANDARD** et **URGENT** :
    1. magasins ayant tous les articles en stock (`Oui`) avant les autres (`Non`),
    2. puis distance au **PR principal** croissante (valeurs nulles à la fin),
    3. puis `Code magasin` (ordre alphabétique) en cas d’égalité ;
  - en **MAD** : tri par `Distance centre (km)` croissante.

#### 3.4.3. Indicateur hors norme et liens vers RECHERCHE STOCK

- Le récapitulatif **"ORDRE DE LIVRAISON DÉGRADÉ"** affiche pour chaque ligne OL :
  - un indicateur **Hors norme** (`Oui` / `Non`),
  - avec fond rouge pour les articles hors norme.
- Dans le tableau et dans le récapitulatif OL :
  - le **code article** est un lien vers l’onglet **RECHERCHE STOCK** (`stock.html`),
  - le lien ouvre la page avec le paramètre `?code=<CODE>` et déclenche automatiquement la recherche et le chargement du stock pour cet article.

#### 3.4.4. Règles de validation principales et envoi des e‑mails

- Règles de validation (inchangées par rapport à la V1) :
  - Numéro de BT obligatoire.
  - Au moins **une ligne** avec `code_article` renseigné.
  - Pour chaque ligne avec article, `code_magasin` expéditeur obligatoire.
  - Destination obligatoire :
    - si `code_ig` → un code IG doit être saisi,
    - si `adresse_libre` → adresse, code postal et ville obligatoires.
- Logique d’envoi des e-mails (DAHER / LM2S) et format des messages : identiques à la V1 (voir documentation fonctionnelle interne pour le détail des destinataires et du format exact du mail).

---

## 4. Remarques

- Pour construire l'exécutable, utiliser l'environnement virtuel principal `.venv` (section 2) avec le projet et PyInstaller installés.
- Il est possible de rejouer une configuration de build existante via les fichiers `.spec` fournis, par exemple : `pyinstaller --clean SupplyChainApp.spec`.
- Si, au lancement de l'exécutable, une erreur `ModuleNotFoundError` apparaît pour un paquet supplémentaire, installer ce paquet dans `.venv` puis relancer la commande PyInstaller.
- En cas de modification importante de la structure du frontend (`web/`), il suffit de reconstruire l'exécutable avec la même commande PyInstaller (ou via le `.spec`).
- Sous Windows + OneDrive, l'option `--clean` peut parfois échouer avec une erreur de type `PermissionError [WinError 5]` lors de la suppression du dossier `build/` (fichiers verrouillés par OneDrive ou un antivirus). Dans ce cas :
  - fermer les fenêtres/terminaux qui pointent sur `build/` ou `dist/`,
  - mettre en pause temporairement la synchronisation OneDrive ou déplacer le projet hors OneDrive,
  - ou lancer PyInstaller sans `--clean` si nécessaire.

### 4.1. Dépannage : ports occupés (Windows)

Si l'application a été lancée plusieurs fois et qu'un ancien process tourne encore, les ports `8000` (frontend) et/ou `5001` (API) peuvent être occupés.

Commandes utiles :

```powershell
netstat -ano | findstr :8000
netstat -ano | findstr :5001
taskkill /PID <PID> /F
```

---

## 5. Livraison / déploiement de l'exécutable

- **Fichier à livrer** : `dist/SUPPLYCHAIN_APP_v1.6.0.exe`.
- **Public cible** : postes Windows internes ne disposant pas forcément de Python.

### 5.1. Prérequis côté utilisateur

- Windows 10 ou 11.
- Accès réseau aux répertoires de données métiers attendus (partages réseau, `path_datan`, etc.).
- Droits en écriture sur un répertoire local de travail (logs, copies de parquets, exports).

### 5.2. Mode opératoire recommandé

1. Copier `SUPPLYCHAIN_APP_v1.6.0.exe` dans un répertoire dédié (par exemple `C:\Applications\SupplyChainApp`).
2. Créer éventuellement un raccourci sur le bureau ou dans le menu Démarrer.
3. Double-cliquer sur l'exécutable :
   - une console s'ouvre avec les logs,
   - le navigateur s'ouvre sur `http://127.0.0.1:8000/`.
4. Pour fermer l'application :
   - cliquer sur la croix de la console **ou**
   - utiliser `Ctrl + C` dans la console.

> Remarque : en cas de message de sécurité SmartScreen, l'utilisateur doit choisir "Informations complémentaires" puis "Exécuter quand même" si l'exécutable est distribué en interne.

---

## 6. Changelog (extrait)

- **Technique (refactor)**
  - Passage à une structure professionnelle `src/` + `web/`.
  - Nouveau point d'entrée : `py -m supplychain_app.run`.
  - Build exécutable via `SupplyChainApp.spec` ou `scripts/build_exe.ps1`.

- **1.3.0**
  - Ajout de l'information **categorie_sans_sortie** sur les articles (backend + affichage dans `info_article` et `RECHERCHE_STOCK`).
  - Amélioration de la recherche d'articles par **fournisseur** / **référence fabricant** (enrichissement du parquet `items.parquet` avec `manufacturers.parquet`).
  - Mise en place d'une **mise à jour automatique** des données toutes les 30 minutes (`update_data()` et endpoint `/api/updates/status`).
  - Nouvel exécutable packagé `SUPPLYCHAIN_APP_v1.3.0.exe` (PyInstaller, fichier `SUPPLYCHAIN_APP_v1.3.0.spec`).

- **1.4.0**
  - Ajout de l'écran **OL MODE DÉGRADÉ V2** (`ol_mode_degrade_v2.html`) avec carte Leaflet intégrée (visualisation des magasins en stock, distances, PR technicien, etc.).
  - Nouveau tri des résultats OL (STANDARD / URGENT) : priorité aux magasins ayant tous les articles en stock, prise en compte de la distance au PR technicien, puis code magasin.
  - Amélioration de l'UX OL :
    - colonnes supplémentaires (distances PR, indicateur « Tous les articles en stock »),
    - surbrillance des articles hors norme dans le récapitulatif,
    - liens directs depuis les codes article OL vers l'onglet **RECHERCHE STOCK** pré-filtré sur l'article.
  - Mise à jour de la navigation : le lien **OL MODE DÉGRADÉ** pointe désormais vers la V2.
  - Nouvel exécutable packagé `SUPPLYCHAIN_APP_v1.4.0.exe` (PyInstaller, fichier `SUPPLYCHAIN_APP_v1.4.0.spec`).

- **1.5.0** *(brouillon métier)*
  - Évolutions de l’onglet **Localisation du stock** :
    - possibilité de lancer la carte **sans code article** pour visualiser les magasins actifs (statut = 0) par type de dépôt ;
    - filtres améliorés (case globale « tout cocher/décocher » pour les filtres stock) ;
    - markers colorés par type de dépôt avec légende ;
    - ajout d’un bouton d’**export Excel** (`localisation_stock.csv`) basé sur `stock_final.parquet` et respectant les filtres saisis.

  - Évolutions de l’onglet **CONSULTATION MAGASIN** (`technician.html`) :
    - le **point relais affiché** est issu du référentiel d’override **CHOIX_PR_TECH** (`R:\...\GESTION_PR\CHOIX_PR_TECH\choix_pr_tech.parquet`) ;
    - les **informations PR** (enseigne, adresse, statut, etc.) sont enrichies depuis `pudo_directory.parquet`.

  - Packaging :
    - exécutable NoLLM livré sous la forme `SUPPLYCHAIN_APP_v1.5.0.exe` (script `scripts/build_exe_no_llm.ps1`).

  - Nouvel onglet **Catalogue consommables** :
    - page frontend : `catalogue_consommables.html`
    - endpoint : `GET /api/consommables/offer`
    - administration simplifiée : dépôt d'un fichier Excel dans un dossier d'offre (voir ci-dessous)

- **1.6.0**
  - Catalogue consommables : enrichissements côté backend + affichage :
    - stock filtré **MPLC / flag_stock_d_m = M / code_qualite = GOOD** depuis `stock_554.parquet` (`stock_mplc_good_m`),
    - sorties consommation **somme toutes années** depuis `stats_exit.parquet` (`sorties_conso_total`),
    - affichage de la **catégorie sans sortie** sous forme de badge (`categorie_sortie`, basé sur `categorie_sans_sortie`) avec code couleur.
  - Onglet **RECHERCHE_STOCK** (`stock.html`) : amélioration de la lisibilité du tableau "Stock" :
    - ordre des colonnes : `flag_stock_d_m`, `type_de_depot`, `GOOD`, `BAD`, `BLOQG`, `BLOQB` ;
    - tri des lignes : `flag_stock_d_m` (`M` puis `D`), puis `type_de_depot` selon un ordre métier prédéfini.
  - Version affichée dans le header : la version est alignée sur le **nom de l'exécutable** (si l'app tourne en mode EXE) et affichée à côté du logo.
  - Sécurité OL MODE DÉGRADÉ V2 : verrouillage possible par liste blanche de logins via `SCAPP_OL_ALLOWED_LOGINS`.

- **1.6.x**
  - Techniciens / PR : ajout de l’affichage **distance + durée (voiture)** entre un magasin et ses points relais.
  - Nouvelle API : `GET /api/technicians/<code_magasin>/distances_pr`.
  - Écrans concernés : `technician.html`, `technician_admin.html`, `technician_assignments.html`.
  - Décision d’architecture : `docs/adr/0003-distance-technicien-pr.md`.

### 6.1. Administration : offre "Catalogue consommables"

L'offre de consommables est pilotée par un fichier Excel :

- Dossier d'offre (par défaut) : `D:\Datan\supply_chain_app\offre_consommables`
- Surcharge via variable d'environnement : `SCAPP_CONSO_OFFER_DIR`
- Règle de sélection : l'application charge le fichier d'offre **le plus récent** (date de modification / mtime), en privilégiant les fichiers dont le nom commence par `offre_consommable` / `offre_consommables`.
  - Convention recommandée : fichiers datés type `offre_consommables_YYYYMMDD.xlsx`.

Format de colonnes recommandé (tolérant côté frontend : plusieurs alias sont acceptés) :

- `code_article`
- `libelle`
- `categorie`
- `sous_categorie` (optionnel)
- `prix` (optionnel)
- `unite` (optionnel)
- `commentaire` (optionnel)

Dans l'onglet :

- un lien "Voir la fiche article" est affiché pour chaque ligne (ouvre `items.html?code=<CODE>`),
- un lien "Voir les photos" est affiché uniquement si des photos existent pour le code article.
