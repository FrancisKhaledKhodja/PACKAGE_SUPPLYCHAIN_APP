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
- Binaire PyInstaller (`SUPPLYCHAIN_APP_v1.4.0.exe`) :
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

### 2.2. Commande PyInstaller (via le fichier .spec)

Depuis la racine du projet, avec `.venv` activé :

```powershell
pyinstaller --clean SUPPLYCHAIN_APP_v1.4.0.spec
```

Cette commande utilise la configuration de build décrite dans `SUPPLYCHAIN_APP_v1.4.0.spec` (point d'entrée, données embarquées, options PyInstaller, etc.).

> Remarque :
> - si un module n'est pas correctement détecté par PyInstaller, il est possible d'ajouter une option `--hidden-import nom_du_module` dans le fichier `.spec` ou en ligne de commande ;
> - les fichiers `.spec` fournis (`SUPPLYCHAIN_APP_v1.1.0.spec`, `SUPPLYCHAIN_APP_v1.2.0.spec`, `SUPPLYCHAIN_APP_v1.4.0.spec`) permettent de rejouer des configurations de build existantes.

#### Alternative : commande directe sans `.spec`

Il est également possible de construire l'exécutable sans utiliser le fichier `.spec` (utile pour un premier build rapide) :

```powershell
pyinstaller --onefile --name SUPPLYCHAIN_APP_v1.4.0 --add-data "package_pudo_frontend;package_pudo_frontend" run_supplychainapp.py
```

Les options sont identiques à celles des versions précédentes :

- `--onefile` : génère un seul fichier `.exe` autonome.
- `--name SUPPLYCHAIN_APP_v1.4.0` : nom du binaire généré.
- `--add-data "package_pudo_frontend;package_pudo_frontend"` : embarque le dossier frontend dans l'exécutable (Windows utilise `;` comme séparateur source/destination).
- `run_supplychainapp.py` : point d'entrée qui démarre API + frontend.

### 2.3. Résultat

PyInstaller génère :

- un exécutable dans `dist/` :

```text
C:\...\PACKAGE_SUPPLYCHAIN_APP\dist\SUPPLYCHAIN_APP_v1.4.0.exe
```

- des fichiers intermédiaires dans `build/` (peuvent être supprimés si besoin).

### 2.4. Lancer l'exécutable

Depuis un terminal :

```powershell
cd .\dist\
.\SUPPLYCHAIN_APP_v1.3.0.exe
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
- **Stock ultra détaillé** :
  - vue API/exports permettant d’analyser le stock `lot / série / projet / colis` avec date de stock pour un article donné (cf. endpoint `/api/auth/stock/<code_article>/ultra-details`).
- **Localisation du stock (`stock_map.html`)** :
  - carte (Leaflet) montrant les magasins/dépôts qui détiennent du stock pour un article,
  - filtres sur type de dépôt, qualité, type de stock, HORS TRANSIT,
  - calcul optionnel de la distance par rapport à un point de référence (code IG ou adresse).
- **Téléchargements (`downloads.html`)** :
  - accès aux exports générés (stock détaillé, statistiques de sorties, PUDO, etc.).
- **Écrans techniciens / affectations technicien ↔️ PUDO** :
  - écrans dédiés au suivi des techniciens, de leurs magasins de rattachement et de leurs PUDO (principal / backup / hors normes).

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
- Il est possible de rejouer une configuration de build existante via les fichiers `.spec` fournis, par exemple : `pyinstaller --clean SUPPLYCHAIN_APP_v1.3.0.spec`.
- Si, au lancement de l'exécutable, une erreur `ModuleNotFoundError` apparaît pour un paquet supplémentaire, installer ce paquet dans `.venv` puis relancer la commande PyInstaller.
- En cas de modification importante de la structure du frontend (`package_pudo_frontend`), il suffit de reconstruire l'exécutable avec la même commande PyInstaller (ou via le `.spec`).
- Sous Windows + OneDrive, l'option `--clean` peut parfois échouer avec une erreur de type `PermissionError [WinError 5]` lors de la suppression du dossier `build/` (fichiers verrouillés par OneDrive ou un antivirus). Dans ce cas :
  - fermer les fenêtres/terminaux qui pointent sur `build/` ou `dist/`,
  - mettre en pause temporairement la synchronisation OneDrive ou déplacer le projet hors OneDrive,
  - ou lancer PyInstaller sans `--clean` si nécessaire.

---

## 5. Livraison / déploiement de l'exécutable

- **Fichier à livrer** : `dist/SUPPLYCHAIN_APP_v1.4.0.exe`.
- **Public cible** : postes Windows internes ne disposant pas forcément de Python.

### 5.1. Prérequis côté utilisateur

- Windows 10 ou 11.
- Accès réseau aux répertoires de données métiers attendus (partages réseau, `path_datan`, etc.).
- Droits en écriture sur un répertoire local de travail (logs, copies de parquets, exports).

### 5.2. Mode opératoire recommandé

1. Copier `SUPPLYCHAIN_APP_v1.4.0.exe` dans un répertoire dédié (par exemple `C:\Applications\SupplyChainApp`).
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
