# SupplyChainApp – Spécification des usages et besoins métiers

## 1. Contexte et objectifs

L’application **SupplyChainApp** est un outil interne destiné aux équipes Supply Chain (gestion des magasins, des stocks, du réseau de points relais et du parc Helios).

Elle centralise plusieurs sources de données (fichiers Excel, exports BO, fichiers Parquet) et les expose via une interface web unique permettant :

- **chercher et analyser des articles** (informations PIM, logistiques, comptables, fournisseurs, équivalences) ;
- **visualiser le stock** (par article, par magasin, par dépôt, par qualité) ;
- **identifier les articles dormants** via une **catégorie “sans sortie”** ;
- **consulter le parc installé (Helios)** ;
- **consulter les magasins / points relais et leurs contacts** ;
- **suivre les assignations technicien ↔ point relais**.

L’objectif métier est de **faciliter la décision opérationnelle** (gestion des stocks, arbitrage des articles dormants, choix des emplacements, suivi du parc) en réduisant les manipulations manuelles sur Excel et en proposant une vue consolidée.

---

## 2. Périmètre fonctionnel

### 2.1. Onglet `info_article` (`items.html`)

#### 2.1.1. Usages

- **Recherche d’article** à partir de :
  - **code article** ;
  - **libellé** partiel (court/long) ;
  - **texte libre** dans les colonnes PIM ;
  - **informations fournisseurs** (nom de fabricant, référence fabricant).

- **Consultation détaillée** pour un article donné :
  - description (libellés, commentaires techniques, mnémotechniques) ;
  - statut, type, criticité PIM ;
  - informations de catalogue et de famille comptable ;
  - informations logistiques (poids, dimensions, transport, matières dangereuses, conditionnement…) ;
  - paramètres d’approvisionnement (quantités mini/maxi, délais, points de commande) ;
  - données de réparation et garanties (lieu, délais, RMA…).

- **Nomenclature (BOM)** :
  - visualisation de l’arbre de nomenclature (articles fils, quantités) ;
  - représentation textuelle hiérarchisée (ASCII).

- **Fournisseurs** :
  - liste des références fabricants associées à l’article ;
  - affichage sous forme de tableau, une ligne par couple (fournisseur, référence).

- **Équivalences** :
  - liste des articles équivalents avec leur type de relation.

- **Catégorie “sans sortie”** :
  - affichage de la **`categorie_sans_sortie`** associée à l’article ;
  - présentation sous forme de **badge coloré** suivant une échelle métier (cf. § 3.1.2).

#### 2.1.2. Besoins métiers

- Trouver et **identifier rapidement** la fiche complète d’un article.
- Comprendre son **statut de vie** (actif / obsolète / consommable / etc.).
- Visualiser les **fournisseurs** et **articles équivalents** pour faciliter les substitutions.
- Disposer d’un **indicateur visuel** sur la catégorie de “non-sortie” pour préparer les plans de déstockage ou d’optimisation.

---

### 2.2. Onglet `RECHERCHE_STOCK` (`stock.html`)

#### 2.2.1. Usages

- **Recherche d’un article** (mêmes critères que `info_article`, y compris via les champs fournisseurs).
- Pour l’article sélectionné :
  - affichage d’un **résumé article** (champs clés PIM) ;
  - affichage de la **`categorie_sans_sortie`** (badge coloré) ;
  - affichage du **stock agrégé** par :
    - magasin / code magasin,
    - type de dépôt,
    - qualité.

- Lien rapide vers :
  - l’onglet **Stock détaillé** pour le même article ;
  - l’onglet **info_article** pour la fiche complète ;
  - les **statistiques de sorties** (par année / motif).

#### 2.2.2. Besoins métiers

- Visualiser **où se trouve le stock** d’un article (typologie de dépôts, volumes).
- Identifier les **stocks dormants** via la catégorie sans sortie.
- Pouvoir basculer rapidement vers une **analyse détaillée** (stock par magasin, sorties par année, fiche article).

---

### 2.3. Onglet `Stock détaillé` (`stock_detailed.html`)

#### 2.3.1. Usages

- Pour un **code article** donné :
  - afficher le **détail du stock** par ligne de stock :
    - magasin,
    - libellé magasin,
    - type de dépôt,
    - emplacement,
    - code qualité,
    - quantité.

#### 2.3.2. Besoins métiers

- Préparer des **transferts de stock** ou des **changements d’emplacement**.
- Analyser les **stocks par qualité** (bloqué, libre, défectueux…).
- Disposer d’une granularité fine pour les **analyses logistiques**.

---

### 2.4. Onglet `Parc Helios` (`helios.html`)

#### 2.4.1. Usages

- Pour un **code article** donné :
  - consulter une **synthèse du parc installé** (données Helios) :
    - code IG,
    - quantité active,
    - nombre de sites actifs,
    - autres indicateurs clés.

#### 2.4.2. Besoins métiers

- Connaître l’**importance du parc installé** pour un article.
- Mettre en perspective les décisions de **gestion de stock** (maintien, réduction, obsolescence) avec l’ampleur du parc.

---

### 2.5. Onglet `Magasins & points relais` (`stores.html`)

#### 2.5.1. Usages

- Rechercher un **magasin / dépôt / point relais** par :
  - code magasin,
  - type de dépôt,
  - texte libre (ville, contact, email, téléphone…).
- Visualiser les informations de **contact** :
  - équipe, responsable magasin,
  - nom, téléphone, email,
  - adresse postale.

#### 2.5.2. Besoins métiers

- Obtenir rapidement les **contacts logistiques** pertinents.
- Faciliter la **communication opérationnelle** (organisation de transferts, gestion d’incidents, clarifications de stock).

---

### 2.6. Écrans techniciens / affectations PUDO

#### 2.6.1. Usages

- Associer des **techniciens** à des **magasins / PUDO** (points relais).
- Visualiser pour un technicien donné :
  - ses magasins de rattachement,
  - ses PUDO principal / backup / hors normes,
  - leurs coordonnées et adresses.

#### 2.6.2. Besoins métiers

- Centraliser les **affectations technicien ↔ magasin/PUDO**.
- Aider à l’**organisation des tournées** et à la gestion des **stocks embarqués**.
- Permettre une meilleure **visibilité transversale** de qui est rattaché à quoi.

---

## 3. Indicateurs et règles métiers spécifiques

### 3.1. Catégorie “sans sortie” (`categorie_sans_sortie`)

#### 3.1.1. Définition

La **catégorie “sans sortie”** classe les articles selon la **durée depuis leur dernière sortie** (analyse des mouvements d’articles).  
L’information est calculée en amont et stockée dans le fichier Parquet `items_without_exit_final.parquet`, puis utilisée par l’application.

#### 3.1.2. Valeurs et couleurs

La valeur de `categorie_sans_sortie` est associée à une **couleur de fond** utilisée dans l’interface :

- `1 - moins de 2 mois` → `#33CC00` (vert clair)
- `2 - entre 2 et 6 mois` → `#66AA00` (vert)
- `3 - entre 6 mois et 1 an ` → `#999900` (jaune/olive)
- `4 - entre 1 et 2 ans` → `#CC6600` (orange)
- `5 - entre 2 et 5 ans` → `#FF3300` (orange/rouge)
- `6 - entre 5 et 10 ans` → `#FF0000` (rouge)
- toute autre valeur → `#FF0000` (rouge)

Affichage :

- dans **info_article** : bloc "Catégorie sans sortie" avec un badge coloré ;
- dans **RECHERCHE_STOCK** : badge dans le résumé de l’article sélectionné.

#### 3.1.3. Usages métier

- Prioriser les **actions de déstockage** sur les articles des catégories 5 et 6.
- Identifier les articles à **surveiller** (3–4) et ceux qui tournent normalement (1–2).
- Fournir un **argument chiffré et visuel** pour les décisions de réduction de stock ou d’arrêt.

---

### 3.2. Recherche sur les champs fournisseurs

#### 3.2.1. Définition

La recherche `/api/items/search` repose sur :

- le Parquet `items.parquet` (colonnes PIM classiques) ;
- **enrichi** avec un texte agrégé issu de `manufacturers.parquet` (fournisseurs).

Techniquement :

- pour chaque `code_article`, les colonnes texte de `manufacturers` sont concaténées dans un champ global,
- ce texte est inclus dans le champ de **recherche globale**.

#### 3.2.2. Usages métier

- Retrouver un article à partir d’un **nom de fournisseur** ou d’une **référence fabricant**.
- Améliorer la **recherche cross-fonctionnelle** entre équipes achats et supply chain.
- Réduire les erreurs liées aux correspondances manuelles article ↔ fournisseur.

---

## 4. Données et mises à jour

### 4.1. Sources de données

Principales familles de fichiers :

- **Excel / exports** :
  - annuaire PR,
  - stock temps réel 554,
  - fichiers de référence articles, etc.
- **Parquets** utilisés par l’application :
  - `pudo_directory.parquet` (annuaire points relais),
  - `stores.parquet` (magasins / dépôts),
  - `items.parquet` (articles),
  - `nomenclatures.parquet`,
  - `manufacturers.parquet` (fournisseurs),
  - `equivalents.parquet` (articles équivalents),
  - `minmax.parquet`,
  - `stats_exit.parquet` (statistiques de sorties),
  - `items_without_exit_final.parquet` (catégories sans sortie),
  - `stock_554.parquet` (stock détaillé 554 enrichi).

### 4.2. Mécanisme de mise à jour

- Toutes les **30 minutes**, un processus en arrière-plan :
  - vérifie si de nouveaux fichiers sources sont disponibles / plus récents,
  - met à jour les fichiers Parquet de travail (`path_datan/<folder_name_app>`).

- Un endpoint de statut :
  - `GET /api/updates/status` → `{ "has_changes": bool, "timestamp": UNIX }`.

- Le frontend :
  - interroge régulièrement cet endpoint,
  - affiche un **bandeau dans le header** (`Données mises à jour à HHhMM`) quand une mise à jour a eu lieu récemment.

### 4.3. Besoin métier associé

- Garantir que les **données consultées** (stock, articles, PUDO, Helios) sont **récemment rafraîchies**.
- Informer l’utilisateur en temps réel lorsqu’une **nouvelle mouture** des données est disponible (éviter de travailler sur des données obsolètes sans le savoir).
