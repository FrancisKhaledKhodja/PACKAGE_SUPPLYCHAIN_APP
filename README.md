# SupplyChainApp

Application Python pour la gestion SupplyChain (PUDO, stocks, Helios, statistiques de sorties, etc.).

Ce document résume :

- comment lancer l'application en mode développeur,
- comment construire un exécutable Windows (`.exe`) avec PyInstaller.

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

La construction de l'exécutable se fait dans un environnement virtuel dédié, `.venv_build`, pour éviter les problèmes liés à l'environnement de développement principal.

### 2.1. Activer l'environnement de build

Depuis la racine du projet :

```powershell
.\.venv_build\Scripts\Activate.ps1
```

Le prompt doit afficher :

```text
(.venv_build) PS C:\...>
```

### 2.2. Dépendances nécessaires dans `.venv_build`

Dans cet environnement, il faut installer les paquets utilisés par l'application (exemples principaux) :

```powershell
python -m pip install flask polars-lts-cpu loguru fastexcel
```

Adapter cette liste si d'autres dépendances sont ajoutées au projet.

### 2.3. Commande PyInstaller

Toujours depuis la racine du projet :

```powershell
pyinstaller --onefile --name SUPPLYCHAIN_APP_v1.1.0 --add-data "package_pudo_frontend;package_pudo_frontend" run_supplychainapp.py
```

Détails des options :

- `--onefile` : génère un seul fichier `.exe` autonome.
- `--name SUPPLYCHAIN_APP_v1.1.0` : nom du binaire généré.
- `--add-data "package_pudo_frontend;package_pudo_frontend"` : embarque le dossier frontend dans l'exécutable (Windows utilise `;` comme séparateur source/destination).
- `run_supplychainapp.py` : point d'entrée qui démarre API + frontend.

> Remarque : si un module n'est pas correctement détecté par PyInstaller, il est possible d'ajouter une option `--hidden-import nom_du_module` à la commande ci-dessus.

### 2.4. Résultat

PyInstaller génère :

- un exécutable dans `dist/` :

```text
C:\...\PACKAGE_SUPPLYCHAIN_APP\dist\SUPPLYCHAIN_APP_v1.1.0.exe
```

- des fichiers intermédiaires dans `build/` (peuvent être supprimés si besoin).

### 2.5. Lancer l'exécutable

Depuis un terminal :

```powershell
cd .\dist\
.\SUPPLYCHAIN_APP_v1.1.0.exe
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

- Pour construire l'exécutable **toujours utiliser `.venv_build`**, pas l'environnement `.venv` qui est réservé au développement.
- Si, au lancement de l'exécutable, une erreur `ModuleNotFoundError` apparaît pour un paquet supplémentaire, installer ce paquet dans `.venv_build` puis relancer la commande PyInstaller.
- En cas de modification importante de la structure du frontend (`package_pudo_frontend`), il faut simplement reconstruire l'exe avec la même commande PyInstaller.
