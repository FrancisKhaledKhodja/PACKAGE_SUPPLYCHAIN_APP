# SupplyChainApp

Application Python pour la gestion SupplyChain (PUDO, stocks, Helios, statistiques de sorties, etc.).

Ce document résume :

- comment installer les dépendances du projet,
- comment lancer l'application en mode développeur,
- comment construire un exécutable Windows (`.exe`) avec PyInstaller.

---

## 0. Installation & environnement

### 0.1. Prérequis

- **Python 3.13+** (conforme au `pyproject.toml`)
- Windows (tests et packaging ciblés sur cette plateforme)
- Accès aux fichiers sources métiers (parquets, etc.) attendus par `package_pudo_api`.

### 0.2. Installation des dépendances avec `uv` (recommandé)

Les dépendances de l'application sont décrites dans `pyproject.toml` et figées dans `uv.lock`.

Depuis la racine du projet :

```powershell
uv sync
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
        |  (package_pudo_frontend)|
        |  HTML / CSS / JS        |
        +-------------+-----------+
                      |
                      | HTTP (AJAX, port 5001)
                      v
        +-------------+-----------+
        |   API Flask             |
        |  (package_pudo_api)     |
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

- `run_supplychainapp.py` :
  - démarre **l'API Flask** sur `127.0.0.1:5001` ;
  - démarre un **serveur HTTP simple** (module `http.server`) sur `127.0.0.1:8000` pour servir `package_pudo_frontend` ;
  - ouvre automatiquement le navigateur sur `http://127.0.0.1:8000/`.
- `package_pudo_api` :
  - organise l'API en **blueprints** (`items`, `pudo`, `stores`, `helios`, `technicians`, `downloads`, etc.) ;
  - expose aussi des endpoints techniques (`/api/health`, `/api/updates/status`).
- `package_pudo_api.data.pudo_etl` :
  - gère les **tâches d'ETL** (chargement/parquetisation, mise à jour périodique dans `path_datan/<folder_name_app>`).
- Binaire PyInstaller (`SUPPLYCHAIN_APP_v1.2.0.exe`) :
  - embarque le même code Python et le dossier `package_pudo_frontend` ;
  - reproduit exactement le comportement de `python run_supplychainapp.py` sans dépendre de Python installé sur le poste utilisateur.

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
python run_supplychainapp.py
```

Ce script :

- démarre l'API Flask (`package_pudo_api`) sur `http://127.0.0.1:5001`,
- démarre un petit serveur HTTP pour le frontend sur `http://127.0.0.1:8000`,
- ouvre automatiquement le navigateur sur `http://127.0.0.1:8000/`.

Pour arrêter : `Ctrl + C` dans le terminal.

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

### 2.2. Commande PyInstaller

Depuis la racine du projet, avec `.venv` activé :

```powershell
pyinstaller --onefile --name SUPPLYCHAIN_APP_v1.2.0 --add-data "package_pudo_frontend;package_pudo_frontend" run_supplychainapp.py
```

Détails des options :

- `--onefile` : génère un seul fichier `.exe` autonome.
- `--name SUPPLYCHAIN_APP_v1.2.0` : nom du binaire généré.
- `--add-data "package_pudo_frontend;package_pudo_frontend"` : embarque le dossier frontend dans l'exécutable (Windows utilise `;` comme séparateur source/destination).
- `run_supplychainapp.py` : point d'entrée qui démarre API + frontend.

> Remarque :
> - si un module n'est pas correctement détecté par PyInstaller, il est possible d'ajouter une option `--hidden-import nom_du_module` à la commande ci-dessus ;
> - des fichiers `.spec` sont également fournis (`SUPPLYCHAIN_APP_v1.1.0.spec`, `SUPPLYCHAIN_APP_v1.2.0.spec`) pour rejouer une configuration de build existante avec `pyinstaller SUPPLYCHAIN_APP_v1.2.0.spec`.

### 2.3. Résultat

PyInstaller génère :

- un exécutable dans `dist/` :

```text
C:\...\PACKAGE_SUPPLYCHAIN_APP\dist\SUPPLYCHAIN_APP_v1.2.0.exe
```

- des fichiers intermédiaires dans `build/` (peuvent être supprimés si besoin).

### 2.4. Lancer l'exécutable

Depuis un terminal :

```powershell
cd .\dist\
.\SUPPLYCHAIN_APP_v1.2.0.exe
```

L'exécutable :

- démarre l'API et le serveur frontend,
- ouvre le navigateur sur `http://127.0.0.1:8000/`,
- affiche les logs dans la console (si construit sans `--windowed`).

---

## 3. Fonctionnalités principales

L'application frontend (dossier `package_pudo_frontend`) propose plusieurs onglets principaux accessibles depuis le header :

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
- **Téléchargements (`downloads.html`)** :
  - accès aux fichiers générés/exportés.
- **Sélection du technicien / Affectation technicien ↔️ PUDO** :
  - écrans dédiés au suivi des techniciens et de leurs points relais.

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

## 4. Remarques

- Pour construire l'exécutable, utiliser l'environnement virtuel principal `.venv` (section 2) avec le projet et PyInstaller installés.
- Il est possible de rejouer une configuration de build existante via les fichiers `.spec` fournis, par exemple : `pyinstaller SUPPLYCHAIN_APP_v1.2.0.spec`.
- Si, au lancement de l'exécutable, une erreur `ModuleNotFoundError` apparaît pour un paquet supplémentaire, installer ce paquet dans `.venv` puis relancer la commande PyInstaller.
- En cas de modification importante de la structure du frontend (`package_pudo_frontend`), il suffit de reconstruire l'exécutable avec la même commande PyInstaller (ou via le `.spec`).
