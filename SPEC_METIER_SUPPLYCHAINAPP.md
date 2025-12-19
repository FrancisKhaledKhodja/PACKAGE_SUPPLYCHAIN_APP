# SupplyChainApp – Spécification des usages et besoins métiers (version 1.5.0)

> Cette version de la spécification correspond à l’application **SupplyChainApp 1.5.0**.

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

### 1.1. Impacts métiers spécifiques à la version 1.3.0

- **Catégorie "sans sortie"**
  - Permet d’identifier rapidement les articles dormants ou à faible rotation.
  - Sert de support aux décisions d’optimisation de stock (dégagement, redéploiement, ajustement de min/max).
- **Recherche enrichie par les données fournisseurs**
  - Facilite le travail des équipes qui raisonnent par **référence fabricant** ou par **nom de fournisseur**.
  - Réduit les allers-retours entre outils (PIM, Excel, fiches fournisseurs) pour retrouver un article.
- **Mise à jour automatique des données**
  - Assure une vision plus fraîche des stocks, PUDO, magasins, stats de sorties, sans action manuelle.
  - Diminue le risque de décision prise sur des données obsolètes.

### 1.2. Impacts métiers spécifiques à la version 1.4.0

- **OL MODE DÉGRADÉ V2 (OL V2)**
  - Simplifie la **préparation des ordres de livraison dégradés** pour les techniciens en réunissant sur un même écran : carte, tableau de stock, récapitulatif OL.
  - Permet de **prioriser les magasins les plus pertinents** (tous les articles en stock, proximité du PR technicien) et de sécuriser les envois.
  - Offre une meilleure **lisibilité des cas hors norme** (articles hors norme mis en évidence dans le récapitulatif).
- **Intégration renforcée avec RECHERCHE_STOCK**
  - Les codes article présents dans l’OL deviennent des **liens directs** vers l’onglet RECHERCHE_STOCK, pré-filtré sur l’article.
  - Facilite les **allers-retours métier** entre vision OL et vision stock globale pour un article.

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

#### 2.3.3. API "Stock ultra détaillé" (stock_final.parquet)

Un besoin complémentaire consiste à disposer, pour un **code article** donné, d’un **état de stock ultra détaillé** au niveau de chaque ligne de stock (lot / série / projet / colis), en incluant la **date de stock**.

- Endpoint backend : `GET /api/auth/stock/<code_article>/ultra-details`
- Paramètres :
  - `code_article` (path) : code article recherché.
- Source de données : `stock_final.parquet` (voir § 4.1).
- Principales colonnes restituées par ligne :
  - `code_magasin`, `libelle_magasin`, `type_de_depot`, `flag_stock_d_m`, `emplacement`,
  - `code_article`, `libelle_court_article`,
  - `n_lot`, `n_serie`,
  - `qte_stock`, `qualite`,
  - `n_colis_aller`, `n_colis_retour`,
  - `n_cde_dpm_dpi`, `demandeur_dpi`,
  - `code_projet`, `libelle_projet`, `statut_projet`, `responsable_projet`,
  - `date_reception_corrigee`,
  - `categorie_anciennete`, `categorie_sans_sortie`,
  - `bu`,
  - `date_stock` (date de référence du stock pour la ligne).

Cet endpoint est destiné à alimenter des écrans ou exports avancés (analyse par lots, suivi projet, enquêtes qualité, reconstitution de l’historique de stock).

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

### 2.6. Page d'accueil (`home.html`)

#### 2.6.1. Usages

- Fournir une **vue de synthèse** à l'ouverture de l'application :
  - statut des **mises à jour de données** (stock, PUDO, magasins, etc.) ;
  - statut et actions de **mise à jour des photos** ;
  - accès rapide aux principaux écrans (info article, recherche stock, parc Helios, téléchargements, etc.) ;
  - liens vers des ressources SharePoint logistique.
- Afficher une **mention explicite sur les photos métier** :
  - nombre de fichiers photo présents sur le **répertoire réseau** ;
  - nombre de fichiers photo présents **en local** sur le poste utilisateur ;
  - nombre de fichiers locaux **correspondant** à un fichier du répertoire réseau.

#### 2.7.2. Besoins métiers

- Vérifier rapidement que **les photos nécessaires sont disponibles** sur le poste (limiter les surprises lors de la consultation d’articles).
- Rendre visible, dès l'accueil, le **niveau de complétude** de la bibliothèque de photos locale par rapport au référentiel réseau.
- Permettre à l'utilisateur de **déclencher une synchronisation** des photos manquantes depuis le répertoire réseau.

---

### 2.6.3. Assistant de navigation (questions en langage naturel)

#### 2.6.3.1. Objectif

- Permettre à l’utilisateur de poser une question en français (ex : « quels sont les points relais proches de Bordeaux ? »).
- L’application détermine l’**écran à ouvrir** et les **paramètres** à appliquer.

#### 2.6.3.2. Règles de routage (mode règles-only)

Dans la version actuelle, l’assistant est un **routeur déterministe** basé sur des règles (mots-clés + extraction simple de paramètres).

Objectif : transformer une question en **action de navigation**.
L’assistant ne calcule pas les valeurs de stock, ne fait pas d’analyse métier et ne remplace pas les écrans : il renvoie seulement :

- une page cible (`target_page`) ;
- des paramètres (`params`) ;
- un message court (`answer`).

Routages principaux couverts :

- Stock par article → `stock.html?code=<CODE_ARTICLE>`
- Carte stock / localisation → `stock_map.html?code=<CODE_ARTICLE>&address=<ADRESSE>`
- Magasins & points relais autour d’une adresse → `stores.html?q=<ADRESSE_OU_VILLE>`
- Détail article (info_article) → `items.html?code=<CODE_ARTICLE>`
- Photos article → `photos.html?code=<CODE_ARTICLE>`
- Parc Helios → `helios.html?code=<CODE_ARTICLE>`
- Écran magasin / technicien → `technician.html?q=<CODE_MAGASIN_OU_RECHERCHE>`
- Affectations techniciens ↔ PR → `technician_assignments.html?store=<CODE>&pr=<CODE>&status=<ouvert|ferme>&roles=<role>&expand_store_roles=1`
- Graphe / réseau article → `article_network.html?code=<CODE_ARTICLE>`
- Statistiques sorties → `statistiques_sorties.html?code=<CODE_ARTICLE>`

#### 2.6.3.3. Modes de fonctionnement (règles vs Ollama)

L'assistant peut être configuré pour tester une variante basée sur Ollama :

- `ASSISTANT_MODE=rules` : routeur à règles (défaut)
- `ASSISTANT_MODE=ollama` : utilisation d'Ollama local (si disponible)
- `ASSISTANT_MODE=auto` : tente Ollama puis bascule vers règles si indisponible

Variables associées :

- `ASSISTANT_OLLAMA_URL` (par défaut `http://127.0.0.1:11434`)
- `ASSISTANT_OLLAMA_MODEL` (par défaut `llama3.1`)
- `ASSISTANT_OLLAMA_TIMEOUT_S` (par défaut `15`)

---

### 2.6.4. Assistant "LLM+RAG" (analyse & génération de code Polars)

#### 2.6.4.1. Objectif

- Permettre à l'utilisateur de poser une question plus analytique (pas uniquement de navigation), avec un support "data".
- Combiner :
  - un contexte RAG (catalogue des tables/jointures),
  - une proposition de code Polars,
  - et, pour certains cas, une **réponse déterministe** basée directement sur les Parquets (pour fiabiliser les réponses métier).

#### 2.6.4.2. Cas d'usage : besoin de stock dans un contexte projet

Exemples de formulations (même résultat attendu) :

- "Pour un projet en cours, pourriez-vous fournir 5 codes article TDF159698 ?"
- "Dans le cadre d'un projet, j'aurais besoin de 5 exemplaires du code article TDF159698."
- "Besoin urgent de 5 unités du code article TDF159698 pour un projet."
- "Au sein d'un projet, requis : 5 codes article TDF159698."

Règles d'analyse (source : `stock_final.parquet`) :

1. Calculer le stock de **qualité GOOD** sur le projet **PJ00000564**.
2. Calculer le stock de **qualité GOOD** sur les autres projets dont le code commence par `PJ` (≠ `PJ00000564`) et synthétiser par **categorie_anciennete_stock** (les plus anciens sont à privilégier).
3. Calculer le stock de **qualité GOOD** en stock de **maintenance** (`flag_stock_d_m = M`) pour ce code article.
4. Calculer le stock de **qualité BAD** (BAD + BLOQB) pour prioriser des **réparations** sur ce code article.

Sortie attendue :

- une synthèse chiffrée,
- une proposition d'actions (réserver sur PJ00000564, basculer/affecter depuis autres PJ en priorisant l'ancienneté, basculer depuis maintenance si autorisé, lancer/prioriser réparations si BAD disponible).

---

### 2.10. Demande de modification article (`article_request.html`)

#### 2.10.1. Objectif

- Standardiser et accélérer la **création de demandes** autour du référentiel article.
- Réduire les manipulations manuelles (copier/coller Excel, consolidation du contenu, etc.).
- Assurer une **traçabilité** via un fichier Excel sauvegardé automatiquement sur un partage réseau.

#### 2.10.2. Types de demandes couvertes

L'écran `article_request.html` couvre les demandes suivantes :

- **Modification d'une criticité**
- **Modification du statut achetable / non achetable**
- **Déclaration d'une équivalence**
- **Demande de passage en REBUT**

#### 2.10.3. Auto-remplissage des champs article

Pour les demandes basées sur un `code_article`, l'application récupère automatiquement les champs via l'API article :

- Endpoint : `GET /api/items/<code>/details`
- Objectif : limiter les erreurs de saisie et éviter les copier/coller depuis le PIM.

#### 2.10.4. Workflow utilisateur (générique)

1. L'utilisateur sélectionne un **type de demande**.
2. Il saisit : **Prénom** + **Nom**.
3. Il ajoute une ou plusieurs lignes de demande.
4. Au clic sur **Valider** :
   - un fichier Excel est généré et sauvegardé automatiquement sur un partage réseau,
   - puis un email est ouvert via `mailto:` avec un objet standard et un corps TSV,
   - le mail mentionne explicitement le **répertoire de sauvegarde** et le **chemin complet** du fichier Excel.

#### 2.10.5. Contenu standardisé du mail

- Destinataire : `referentiel_logistique@tdf.fr`
- Objet : `[DDE MODIF ARTICLE] - <type demande> - <prenom nom> - <date>`
- Corps :
  - en-tête (type de demande, prénom, nom, date),
  - répertoire de sauvegarde et chemin du fichier Excel,
  - liste des articles au format TSV.

Limitation : `mailto:` ne permet pas d'ajouter automatiquement une pièce jointe.

#### 2.10.6. Fichier Excel de demande (sauvegarde automatique)

- Répertoire cible :
  - `\\apps\Vol1\Data\011-BO_XI_entrees\07-DOR_DP\Sorties\FICHIERS_REFERENTIEL_ARTICLE\DEMANDES`

Le nom du fichier dépend du type de demande :

- Criticité : `dde_modif_art_criticite_YYYYMMDDTHHMMSS.xlsx`
- Achetable : `dde_modif_art_achetable_YYYYMMDDTHHMMSS.xlsx`
- Équivalence : `dde_equivalence_YYYYMMDDTHHMMSS.xlsx`
- Passage rebut : `dde_passage_rebut_YYYYMMDDTHHMMSS.xlsx`

#### 2.10.7. Endpoints backend (génération Excel)

- `POST /api/downloads/demandes/modif_criticite_xlsx`
- `POST /api/downloads/demandes/modif_achetable_xlsx`
- `POST /api/downloads/demandes/equivalence_xlsx`
- `POST /api/downloads/demandes/passage_rebut_xlsx`

---

Endpoint complémentaire (documentation / debug) :

- `GET /api/assistant/capabilities` → expose les intents supportés par le routeur à règles (page cible, schéma des paramètres, exemples).

Notes d’UX :

- L’URL `stores.html?q=<ville>` pré-remplit le champ d’adresse et lance automatiquement la recherche.
- L’URL `stock_map.html?code=<CODE>&address=<VILLE>` pré-remplit les champs et déclenche automatiquement une recherche.
- L’URL `technician_assignments.html?...` pré-remplit les filtres (q, magasin, PR, statut, rôles, expansion) et charge automatiquement les résultats.

---

### 2.7. Écrans techniciens / affectations PUDO

#### 2.7.1. Usages

- Associer des **techniciens** à des **magasins / PUDO** (points relais).
- Visualiser pour un technicien donné :
  - ses magasins de rattachement,
  - ses PUDO principal / backup / hors normes,
  - leurs coordonnées et adresses.

#### 2.7.2. Règle métier : source du point relais affiché (CONSULTATION MAGASIN)

Dans l’écran **CONSULTATION MAGASIN** (`technician.html`), le **code de point relais affiché** pour chaque rôle (principal / backup / hors normes) suit la règle :

- **Source prioritaire (override)** : fichier de choix PR technicien (répertoire `R:\24-DPR\11-Applications\04-Gestion_Des_Points_Relais\Data\GESTION_PR\CHOIX_PR_TECH\`).
  - Le fichier attendu par l’application est `choix_pr_tech.parquet`.
  - Ce fichier contient, au minimum, les colonnes :
    - `code_magasin` (code magasin / technicien)
    - `pr_role` (`principal` | `backup` | `hors_normes`)
    - `code_point_relais_override` (code PR à afficher)

- **Source de secours** : si aucun override n’est défini pour le magasin/role, l’application utilise le code PR présent dans le référentiel magasins (`stores.parquet`) pour ce rôle.

Les informations associées au PR (nom d’enseigne, adresse, statut, catégorie, prestataire, etc.) sont enrichies depuis :

- `pudo_directory.parquet` (annuaire points relais), en joignant sur `code_point_relais`.

Cette règle garantit que :

- le PR affiché à l’utilisateur est **celui validé métier** via le référentiel CHOIX_PR_TECH,
- tout en conservant des **informations d’annuaire cohérentes** via `pudo_directory.parquet`.

#### 2.6.2. Besoins métiers

- Centraliser les **affectations technicien ↔ magasin/PUDO**.
- Aider à l’**organisation des tournées** et à la gestion des **stocks embarqués**.
- Permettre une meilleure **visibilité transversale** de qui est rattaché à quoi.

---

### 2.8. Onglet `Localisation du stock` (`stock_map.html`)

#### 2.8.1. Usages

- Visualiser sur une **carte** (Leaflet) les **magasins / dépôts** selon deux modes :
  - **Mode par article** : pour un ou plusieurs **codes article** saisis, afficher les magasins qui détiennent du stock pour ces articles, en appliquant les filtres stock (type de dépôt, qualité, type de stock, HORS TRANSIT).
  - **Mode sans article** : si aucun code article n’est saisi, afficher les **magasins actifs** (statut magasin = 0) correspondant au **type de dépôt** sélectionné, qu’ils aient du stock ou non (quantité affichée à 0 si aucune ligne de stock).
- Permettre de **centrer la carte** et de calculer la **distance à vol d’oiseau** entre chaque magasin et un **point de référence** défini par l’utilisateur :
  - soit via un **code IG** (site client),
  - soit via une **adresse postale** libre.
- Filtrer les magasins affichés sur la carte et dans le tableau associé à l’aide de critères :
  - **type de dépôt** (NATIONAL, LOCAL, REO, PIED DE SITE, EMBARQUE, LABORATOIRE, DIVERS, END, FOURNISSEURS, SOUS TRAITANTS, DTOM, EXPERT DTE, EXPERT DPR, REPARATEUR INTERNE, REPARATEUR EXTERNE, RESERVE, FILIALE, DATACENTER, etc.), avec une **case globale** « tout cocher / tout décocher » pour simplifier l’usage ;
  - **code qualité** (GOOD, BLOQG, BAD, BLOQB, …) *(mode par article uniquement)* ;
  - **type de stock** (`flag_stock_d_m` : M, D) *(mode par article uniquement)* ;
  - option **HORS TRANSIT** pour exclure les emplacements se terminant par `-T` *(mode par article uniquement)*.
- Afficher, en complément de la carte :
  - un **récapitulatif article** (code, libellé) lorsque des codes article sont saisis ;
  - les **informations sur le centre choisi** (code IG ou adresse, éventuellement coordonnées géographiques) ;
  - un **tableau détaillé** listant les magasins retenus avec leurs attributs (magasin, type de dépôt, quantités agrégées, distances estimées…).
- Représenter visuellement le **type de dépôt** :
  - chaque magasin est affiché sous forme de **rond coloré** (Leaflet `circleMarker`) dont la couleur dépend du type de dépôt (ex. NATIONAL = bleu, LOCAL = vert, REO = rouge, LABORATOIRE = rose, etc.) ;
  - une **légende** sous la carte rappelle le code couleur utilisé.
- Permettre un **export Excel** (CSV) du résultat affiché, via un bouton dédié, basé sur `stock_final.parquet` et respectant les filtres saisis (export possible uniquement si des résultats existent).

#### 2.7.2. Besoins métiers

- **Préparer des décisions de déstockage / transfert** en visualisant rapidement où se trouve physiquement le stock d’un article.
- Identifier les **magasins les plus pertinents** pour servir un site client (proximité géographique, type de dépôt, qualité de stock).
- En mode sans article, disposer d’une **vue par maillage de magasins actifs** (par type de dépôt), même en l’absence de stock, pour préparer des scénarios de déploiement logistique.
- Aider à la **planification logistique** (choix du dépôt d’expédition, mutualisation de stocks, optimisation des tournées).
- Fournir une **vue géographique synthétique** permettant de raconter simplement la situation du stock à des interlocuteurs non experts (direction, métiers connexes).

#### 2.8.3. Exemples d’usage

- **Exemple 1 – Recherche par article avec filtres stock**
  - Le gestionnaire saisit `TDF158545;TDF158548` dans le champ *Code article*.
  - Il coche uniquement les types de dépôt `NATIONAL` et `LOCAL`, laisse `GOOD` et `M` cochés, et conserve l’option **HORS TRANSIT**.
  - Il renseigne un **code IG** client pour centrer la carte.
  - La carte affiche les magasins qui détiennent du stock pour ces articles, colorés par type de dépôt, avec les distances au site client.
  - Le tableau récapitule pour chaque magasin : type de dépôt, quantités agrégées, distances. Le gestionnaire exporte ensuite le résultat en CSV via le bouton d’export.

- **Exemple 2 – Vue réseau par type de dépôt sans article**
  - Le responsable logistique laisse le champ *Code article* vide.
  - Il sélectionne uniquement les types de dépôt `NATIONAL` et `DATACENTER`.
  - Il saisit une **adresse postale** (zone géographique cible) pour centrer la carte.
  - L’application affiche alors les **magasins actifs** (statut magasin = 0) de type NATIONAL ou DATACENTER, qu’ils aient du stock ou non (quantité 0 affichée si aucun stock renseigné).
  - Cette vue permet de discuter du maillage des dépôts et des scénarios d’implantation ou de mutualisation sans se limiter à un article.

---

### 2.9. OL MODE DÉGRADÉ V2 (`ol_mode_degrade_v2.html`)

#### 2.9.1. Usages

- Préparer un **ordre de livraison en mode dégradé** pour un technicien donné, en tenant compte :
  - des stocks disponibles par magasin pour un ou plusieurs **codes article**,
  - des **points relais** rattachés au technicien (PR principal / PR hors normes),
  - du **type de commande** (STANDARD, URGENT, MAD) et de l’adresse de livraison.
- Visualiser sur une **carte** les magasins potentiels et les PR du technicien, afin de choisir un scénario logistique cohérent.
- Disposer d’un **tableau de synthèse** des magasins avec des indicateurs clés (tous les articles en stock, distances PR, type de dépôt, etc.).
- Générer un **récapitulatif d’ordre de livraison** prêt à être intégré dans un mail (DAHER / LM2S).

#### 2.9.2. Comportement fonctionnel

- L’utilisateur sélectionne :
  - un **technicien** (liste issue des affectations technicien ↔ PUDO / magasins),
  - un **type de commande** : STANDARD, URGENT ou MAD,
  - un ou plusieurs **codes article** (saisie libre, séparés par `;`).
- L’application interroge l’API pour récupérer, pour chaque article, les **magasins en stock** selon les filtres choisis (type de dépôt, qualité, type de stock, HORS TRANSIT).
- Les résultats sont fusionnés dans :
  - un **tableau** listant les magasins, et
  - une **carte Leaflet** affichant un marker par magasin.
- En STANDARD / URGENT :
  - les **points relais du technicien** (PR principal / PR hors normes) sont affichés sur la carte avec leur **enseigne** et leur **adresse postale** dans les popups.

#### 2.9.3. Tableau de résultats et règles de tri

- Colonnes principales du tableau :
  - `Code article`, `Code magasin`, `Libellé magasin`, `Type de dépôt`, `Code qualité`, `Type stock (M/D)`,
  - `Qté stock totale`,
  - `Tous les articles en stock` (Oui/Non),
  - `Distance centre (km)`,
  - en STANDARD / URGENT : `Dist. PR principal (km)`, `Dist. PR hors normes (km)`.
- Colonne **Tous les articles en stock** :
  - indique si le magasin détient **l’ensemble des articles saisis** (tous les codes article de la recherche).
- Règles de tri :
  - en **STANDARD** et **URGENT** :
    1. magasins où **Tous les articles en stock = Oui**, puis ceux à `Non`,
    2. puis ordre croissant de **distance au PR principal** (magasin le plus proche du PR technicien en premier),
    3. puis `Code magasin` (ordre alphabétique) en cas d’égalité ;
  - en **MAD** : tri par **Distance centre (km)** croissante.

#### 2.9.4. Intégration avec RECHERCHE_STOCK

- Dans le tableau et dans le **récapitulatif OL** :
  - le **code article** est cliquable ;
  - le clic ouvre l’onglet **RECHERCHE_STOCK** (`stock.html`) avec le paramètre `?code=<CODE_ARTICLE>` ;
  - la page RECHERCHE_STOCK **pré-remplit et lance automatiquement** la recherche pour ce code et charge le stock détaillé.
- Objectif métier :
  - permettre aux utilisateurs de **creuser rapidement** le contexte stock d’un article (stocks agrégés, stats de sorties, parc Helios) directement depuis un travail OL.

#### 2.9.5. Règles de validation et logique d’envoi (rappel synthétique)

- **Règles de validation principales** (identiques à la V1, avec précisions V2) :
  - **BT obligatoire** ;
  - au moins **une ligne** avec `code_article` renseigné ;
  - pour chaque ligne avec article, `code_magasin` expéditeur obligatoire ;
  - destination obligatoire (Code IG, Point Relais ou Adresse libre avec adresse/CP/ville) ;
  - en **mode MAD**, l’adresse de livraison de l’OL est définie comme **les magasins expéditeurs eux‑mêmes** (pas de saisie d’adresse spécifique).
- **Adresse de livraison et Code IG** :
  - en cas de destination par **Code IG**, l’écran affiche sous le champ la **chaîne d’adresse complète** issue de la table Helios (libellé long + adresse postale) ;
  - cette même adresse est reprise dans le récapitulatif OL et dans le corps des e‑mails générés.
- **Envoi des mails** :
  - la logique métier DAHER / LM2S et le contenu des mails (objet, corps, destinataires) restent inchangés par rapport à la V1 ;
  - OL V2 apporte une **meilleure préparation** de ces mails via la carte + tableau + récap enrichi (hors norme, distances, adresses, lien Google Maps, etc.).
  - routage des mails selon les **codes magasins expéditeurs** des lignes OL :
    - si **toutes** les lignes ont `code_magasin = MPLC` → un seul mail **DAHER** est généré ;
    - si **aucune** ligne n’a `code_magasin = MPLC` → un seul mail **LM2S** est généré ;
    - si cas **mixte** (au moins une ligne MPLC et au moins une ligne non MPLC) → deux mails sont générés :
      - un mail DAHER pour les lignes `code_magasin = MPLC` ;
      - un mail LM2S pour les lignes avec `code_magasin ≠ MPLC`.
  - objet des mails :
    - `[MODE DEGRADE] - Commande OL dégradé - BT <numéro> - <TYPE_COMMANDE> - DAHER` (lignes MPLC) ;
    - `[MODE DEGRADE] - Commande OL dégradé - BT <numéro> - <TYPE_COMMANDE> - LM2S` (autres lignes) ;
    - sans suffixe spécifique lorsque le routage ne distingue pas de transporteur ;
  - principaux destinataires :
    - DAHER : `ordotdf@daher.com; t.robas@daher.com` en **À**, copie à `logistique_pilotage_operationnel@tdf.fr; sophie.khayat@tdf.fr; francis.khaled-khodja@tdf.fr` ;
    - LM2S : `serviceclients@lm2s.fr` en **À**, même copie qu’au-dessus ;
  - les mails sont envoyés en **haute priorité** (X-Priority/Importance).

#### 2.9.6. Workflow utilisateur (OL V2)

1. **Ouverture de l’écran OL V2**
   - L’utilisateur ouvre `ol_mode_degrade_v2.html` depuis le menu principal.

2. **Sélection du technicien et du type de commande**
   - Choix d’un **technicien** dans la liste (détermine PR principal / hors normes, périmètre PUDO/magasins).
   - Choix du **type de commande** : STANDARD, URGENT ou MAD.

3. **Saisie des articles et paramètres de recherche**
   - Saisie d’un ou plusieurs **codes article** (séparés par `;`).
   - Optionnel : ajustement des **filtres de stock** (type de dépôt, code qualité, type de stock, HORS TRANSIT).
   - Lancement de la recherche.

4. **Lecture de la carte et du tableau de résultats**
   - La **carte** affiche :
     - les **magasins en stock** pour les articles saisis,
     - les **PR du technicien** (principal / hors normes) avec enseigne + adresse postale dans les popups.
   - Le **tableau** liste les magasins avec :
     - la colonne **Tous les articles en stock** (Oui/Non),
     - les **distances** au centre et aux PR,
     - les informations de dépôt / qualité / type de stock.
   - En STANDARD / URGENT, l’ordre des lignes respecte le **tri métier** (tous les articles, distance PR principal, code magasin).

5. **Construction de l’Ordre de Livraison dégradé**
   - L’utilisateur sélectionne un ou plusieurs **magasins expéditeurs** pertinents.
   - L’écran génère un **récapitulatif OL** :
     - lignes article avec indication **hors norme** mise en évidence,
     - informations d’expédition (magasin, PR, adresse de livraison, transporteur cible…).
   - Les **codes article** du récap sont cliquables pour ouvrir RECHERCHE_STOCK au besoin.

6. **Contrôle final et envoi du mail**
   - Vérification des règles de validation (BT, au moins une ligne article, codes magasin expéditeurs, destination renseignée).
   - L’utilisateur valide puis **envoie le mail OL** vers DAHER / LM2S depuis l’application (contenu identique à la V1, mais préparé grâce aux apports de la V2).

#### 2.7.3. API associée

- Endpoint : `POST /api/stores/stock-map`

- Paramètres (corps JSON) :
  - `code_article` *(string, obligatoire)* : code article concerné.
  - `code_ig` *(string, optionnel)* : code IG pour le point de référence.
  - `address` *(string, optionnel)* : adresse postale libre pour le point de référence.
  - `type_de_depot` *(array[string])* : liste de types de dépôts à inclure (NATIONAL, LOCAL, REO, PIED DE SITE, EMBARQUE, LABORATOIRE, DIVERS, END, FOURNISSEURS, SOUS TRAITANTS, DTOM, EXPERT DTE, EXPERT DPR, REPARATEUR INTERNE, REPARATEUR EXTERNE, RESERVE, FILIALE, DATACENTER, etc.).
  - `code_qualite` *(array[string])* : liste de codes qualité à inclure (GOOD, BLOQG, BAD, BLOQB, …).
  - `flag_stock_d_m` *(array[string])* : liste de types de stock à inclure (`M`, `D`).
  - `hors_transit_only` *(bool)* : si `true`, exclut les emplacements se terminant par `-T`.

- Principaux champs de réponse (JSON) :
  - `rows` *(array[object])* : une ligne par magasin/dépôt avec stock, contenant notamment :
    - `code_magasin`, `libelle_magasin`, `type_de_depot`,
    - `code_qualite`, `flag_stock_d_m`,
    - `qte_stock_total` (quantité totale agrégée),
    - `latitude`, `longitude` (coordonnées géographiques si disponibles),
    - `distance_km` (distance à vol d’oiseau par rapport au point de référence, si calculée),
    - `adresse` (adresse textuelle du magasin/dépôt quand elle est connue),
    - autres attributs logistiques utilisés pour l’affichage détaillé.
  - `center_label` *(string, optionnel)* : libellé du point de référence (code IG ou adresse).
  - `center_lat`, `center_lon` *(number, optionnel)* : coordonnées géographiques du point de référence, si calculées.

---

## 3. Indicateurs et règles métiers spécifiques

### 3.1. Catégorie “sans sortie” (`categorie_sans_sortie`)

#### 3.1.1. Définition

La **catégorie “sans sortie”** classe les articles selon la **durée depuis leur dernière sortie** (analyse des mouvements d’articles).
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
  - `stock_554.parquet` (stock détaillé 554 enrichi),
  - `stock_final.parquet` (stock ultra détaillé avec informations lot/série/projet et date de stock, support des vues avancées telles que la carte de localisation du stock et l’API "stock ultra détaillé").

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

## 5. Projets d'évolution
### 5.1. Intégration d'un LLM et d'un RAG
  Affranchir l'utilisateur de maitriser l'application en lui appotant une assistance dans ces questions ou problèmatiques
  
  - Exemples:
	  - demander "où est mon colis du BT?"
	  - demander "Quels sont les points relais les plus proches de code ig ou de mon domicile?"
	  - demander "Je ne parviens pas à installer tel type de matériel?" 
	  - Demander "je souhaite retourner mon colis BT?" --> fourni la procédure où les contacts
	  - Un chef de projets a besoin de stock "J'ai besoin pour mon projet "PEXXXXX"?
	  - Demande d'une d'intervention --> Catégorisation -> estimation de la charge, des ressources, des compétences nécessaire, des spécificité du site ou du travail

---

## Annexe – Référence API (vue métier / technique)

### A.1. Principes généraux

- **Base URL** : `http://127.0.0.1:5001/api`
- **Format** : JSON
- **Auth / session** : certaines routes utilisent les cookies/session (le frontend envoie `credentials: "include"`).

### A.2. Endpoints transverses

#### A.2.1. `GET /api/health`

- **Description** : vérifie que l’API est joignable.
- **Réponse type** : `{ "status": "ok" }`.

#### A.2.2. `GET /api/updates/status`

- **Description** : donne l’état de la **dernière mise à jour de données** (thread ETL toutes les 30 minutes).
- **Réponse type** :

```json
{ "has_changes": true, "timestamp": 1732621200 }
```

#### A.2.3. `POST /api/assistant/query`

- **Description** : routeur de navigation “questions en langage naturel”.
- **Entrée** (body JSON) :
  - `question` *(string, obligatoire)* : texte libre.
- **Sortie** (body JSON) :
  - `answer` *(string)* : message court affiché à l’utilisateur.
  - `intent` *(string)* : action à lancer (ex : `view_stock_article`, `view_stock_map`, `view_nearest_pudo`, `photos`, `helios`, `technicians`, `none`).
  - `params` *(object)* : paramètres de l’action.
  - `target_page` *(string|null)* : page à ouvrir (`stock.html`, `stock_map.html`, `stores.html`, `photos.html`, `helios.html`, `technician.html`, ou `null`).

---

### A.3. Domaine Articles (`/api/items`)

#### A.3.1. `GET /api/items/search`

- **Description** : recherche d’articles par texte libre, code, libellé, fournisseurs (enrichissement par `manufacturers.parquet`).
- **Paramètres typiques** :
  - `q` *(string)* : texte recherché (code, libellé, texte PIM, nom fournisseur, référence fabricant…).
- **Comportement** :
  - s’appuie sur `items.parquet` + texte agrégé issu de `manufacturers.parquet` ;
  - retourne une liste d’articles correspondant au texte.

- **Exemple de requête** :

```http
GET /api/items/search?q=abc123 HTTP/1.1
Host: 127.0.0.1:5001
Accept: application/json
```

- **Exemple de réponse** :

```json
[
  {
    "code_article": "ABC123",
    "libelle_court_article": "Connecteur fibre 12 FO",
    "libelle_long_article": "Connecteur fibre optique 12 fibres, APC, monomode",
    "statut": "ACTIF",
    "type_article": "PIECE",
    "famille_comptable": "FIBRE",
    "criticite": "CRITIQUE",
    "categorie_sans_sortie": "2 - entre 2 et 6 mois"
  }
]
```

#### A.3.2. `GET /api/items/<code_article>`

- **Description** : fiche article détaillée pour l’écran `info_article`.
- **Path** : `code_article` *(string)*.
- **Champs typiques retournés** :
  - libellés, commentaires, statut, type, criticité, familles comptables ;
  - informations logistiques (poids, dimensions, conditionnement, matières dangereuses…) ;
  - paramètres d’approvisionnement (mini/maxi, point de commande, délais…) ;
  - données de garantie / réparation ;
  - `categorie_sans_sortie`.

- **Exemple de réponse** :

```json
{
  "code_article": "ABC123",
  "libelle_court_article": "Connecteur fibre 12 FO",
  "libelle_long_article": "Connecteur fibre optique 12 fibres, APC, monomode",
  "statut": "ACTIF",
  "type_article": "PIECE",
  "famille_comptable": "FIBRE",
  "criticite": "CRITIQUE",
  "commentaire_technique": "Usage intérieur, IP20",
  "poids_kg": 0.12,
  "longueur_cm": 10,
  "largeur_cm": 5,
  "hauteur_cm": 3,
  "matiere_dangereuse": false,
  "qte_min": 1,
  "qte_max": 200,
  "point_de_commande": 50,
  "delai_appro_jours": 14,
  "garantie_mois": 24,
  "lieu_reparation": "Atelier interne",
  "categorie_sans_sortie": "2 - entre 2 et 6 mois"
}
```

#### A.3.3. `GET /api/items/<code_article>/nomenclature`

- **Description** : retourne la **nomenclature (BOM)** d’un article.
- **Réponse** : arbre hiérarchique des composants (articles fils, quantités), éventuellement une représentation ASCII.

- **Exemple de réponse** :

```json
{
  "code_article": "ABC123",
  "libelle": "Baie optique 12 FO",
  "niveaux": [
    {
      "niveau": 1,
      "code_article_fils": "FO-CABLE-12",
      "libelle_fils": "Câble fibre 12 FO",
      "quantite": 1
    },
    {
      "niveau": 1,
      "code_article_fils": "FO-CONNECT-12",
      "libelle_fils": "Connecteur fibre 12 FO",
      "quantite": 12
    }
  ],
  "representation_ascii": "ABC123\n├─ FO-CABLE-12 x1\n└─ FO-CONNECT-12 x12\n"
}
```

#### A.3.4. `GET /api/items/<code_article>/fournisseurs`

- **Description** : liste des **références fabricants** associées à l’article.
- **Réponse** : tableau de lignes (`fournisseur`, `reference_fabricant`, autres méta-données éventuelles).

#### A.3.5. `GET /api/items/<code_article>/equivalents`

- **Description** : retourne les **articles équivalents**.
- **Réponse** : tableau de lignes (`code_article_equivalent`, `libelle`, `type_relation`, …).

#### A.3.6. `GET /api/items/<code_article>/categorie-sans-sortie`

- **Description** : expose la **catégorie "sans sortie"** d’un article.
- **Réponse type** :

```json
{ "code_article": "ABC123", "categorie_sans_sortie": "5 - entre 2 et 5 ans" }
```

---

### A.4. Domaine Stock & Magasins

#### A.4.1. `GET /api/auth/stock/<code_article>/ultra-details`

- **Description** : stock **ultra détaillé** (lot/série/projet/colis + date de stock), basé sur `stock_final.parquet`.
- **Path** : `code_article` *(string)*.
- **Champs principaux** :
  - `code_magasin`, `libelle_magasin`, `type_de_depot`, `flag_stock_d_m`, `emplacement` ;
  - `code_article`, `libelle_court_article` ;
  - `n_lot`, `n_serie` ;
  - `qte_stock`, `qualite` ;
  - `n_colis_aller`, `n_colis_retour` ;
  - `n_cde_dpm_dpi`, `demandeur_dpi` ;
  - `code_projet`, `libelle_projet`, `statut_projet`, `responsable_projet` ;
  - `date_reception_corrigee` ;
  - `categorie_anciennete`, `categorie_sans_sortie` ;
  - `bu` ;
  - `date_stock`.

- **Exemple de réponse** (tronqué) :

```json
[
  {
    "code_magasin": "M001",
    "libelle_magasin": "Magasin National Paris",
    "type_de_depot": "NATIONAL",
    "flag_stock_d_m": "M",
    "emplacement": "A01-01-01",
    "code_article": "ABC123",
    "libelle_court_article": "Connecteur fibre 12 FO",
    "n_lot": "LOT2024-001",
    "n_serie": null,
    "qte_stock": 120.0,
    "qualite": "GOOD",
    "n_colis_aller": "COL-0001",
    "n_colis_retour": null,
    "n_cde_dpm_dpi": "DPM123456",
    "demandeur_dpi": "DUPONT",
    "code_projet": "PRJ-FTTH-01",
    "libelle_projet": "Déploiement FTTH Région Nord",
    "statut_projet": "EN COURS",
    "responsable_projet": "MARTIN",
    "date_reception_corrigee": "2024-09-15",
    "categorie_anciennete": "0-6 mois",
    "categorie_sans_sortie": "2 - entre 2 et 6 mois",
    "bu": "FIBRE",
    "date_stock": "2024-11-25"
  }
]
```

#### A.4.2. `POST /api/stores/stock-map`

- **Description** : retourne les magasins/dépôts et leurs informations géographiques pour l’onglet `stock_map.html`.
- **Body JSON** :
  - `code_article` *(string, optionnel)* :
    - si renseigné → mode « par article » (retourne uniquement les magasins ayant du stock pour cet article, en appliquant les filtres stock) ;
    - si vide ou non fourni → mode « sans article » (retourne les magasins actifs, filtrés par type de dépôt, avec quantité éventuelle agrégée si disponible).
  - `code_ig` *(string, optionnel)* : code IG du point de référence.
  - `address` *(string, optionnel)* : adresse postale libre du point de référence.
  - `type_de_depot` *(array[string])* : types de dépôts inclus.
  - `code_qualite` *(array[string])* : codes qualité (utilisés uniquement en mode « par article »).
  - `flag_stock_d_m` *(array[string])* : types de stock (`M`, `D`) (utilisés uniquement en mode « par article »).
  - `hors_transit_only` *(bool)* : si `true`, exclut les emplacements finissant par `-T` (utilisé uniquement en mode « par article »).
- **Réponse** :
  - `rows[]` : une ligne par magasin/dépôt retenu, avec notamment :
    - `code_magasin`, `libelle_magasin`, `type_de_depot`,
    - `qte_stock_total` (quantité agrégée, 0 si aucune info de stock n’est disponible en mode sans article),
    - `latitude`, `longitude`,
    - `distance_km` (distance à vol d’oiseau par rapport au point de référence, si calculée),
    - `adresse` (adresse textuelle du magasin/dépôt),
    - autres attributs logistiques utilisés pour l’affichage détaillé.
  - `center_label` : libellé du point de référence.
  - `center_lat`, `center_lon` : coordonnées du point de référence.

- **Exemple de requête** :

```http
POST /api/stores/stock-map HTTP/1.1
Host: 127.0.0.1:5001
Content-Type: application/json
Accept: application/json

{
  "code_article": "ABC123",
  "code_ig": "FR12345",
  "address": "",
  "type_de_depot": ["NATIONAL", "LOCAL", "PIED DE SITE"],
  "code_qualite": ["GOOD", "BLOQG"],
  "flag_stock_d_m": ["M"],
  "hors_transit_only": true
}
```

- **Exemple de réponse** :

```json
{
  "rows": [
    {
      "code_magasin": "M001",
      "libelle_magasin": "Magasin National Paris",
      "type_de_depot": "NATIONAL",
      "code_qualite": "GOOD",
      "flag_stock_d_m": "M",
      "qte_stock_total": 120.0,
      "latitude": 48.8566,
      "longitude": 2.3522,
      "distance_km": 12.34,
      "adresse": "10 rue de la Logistique, 75000 Paris"
    }
  ],
  "center_label": "Site IG FR12345",
  "center_lat": 48.9000,
  "center_lon": 2.3000
}
```

#### A.4.3. `GET /api/stores` (recherche magasins / points relais)

- **Description** : liste / recherche de magasins, dépôts et points relais pour l’écran `stores.html`.
- **Paramètres typiques** :
  - `q` *(string)* : texte libre (ville, contact, email, téléphone…) ;
  - filtres éventuels : `code_magasin`, `type_de_depot`, etc.
- **Réponse** :
  - `code_magasin`, `libelle_magasin`, `type_de_depot`, coordonnées, contact, adresse.

- **Exemple de requête** :

```http
GET /api/stores?q=nanterre HTTP/1.1
Host: 127.0.0.1:5001
Accept: application/json
```

- **Exemple de réponse** :

```json
[
  {
    "code_magasin": "M045",
    "libelle_magasin": "Magasin Local Nanterre",
    "type_de_depot": "LOCAL",
    "ville": "Nanterre",
    "contact_nom": "Durand",
    "contact_email": "logistique.nanterre@exemple.com",
    "contact_tel": "+33 1 23 45 67 89",
    "adresse": "Zone industrielle, 92000 Nanterre",
    "latitude": 48.8925,
    "longitude": 2.2060
  }
]
```

---

### A.5. Domaine PUDO & Techniciens

#### A.5.1. Endpoints `/api/pudo/...`

- **Objet** : exposer l’annuaire des **points relais (PUDO)** et leurs caractéristiques pour les écrans d’affectation.

#### A.5.1.1. `POST /api/pudo/nearby-address`

- **Description** : recherche des points relais autour d’une adresse (géocodée).
- **Entrée** (body JSON) :
  - `address` *(string, obligatoire)*
  - `radius_km` *(number, optionnel, défaut 10)*
  - `enseignes` *(array[string], optionnel)*
- **Sortie** (body JSON) :
  - `rows` *(array[object])* : liste des points relais.
  - `geocoded_address` *(string|null)* : adresse normalisée issue du géocodage.
  - `center_lat`, `center_lon` *(number)* : coordonnées du centre (adresse géocodée).

#### A.5.2. Endpoints `/api/technicians/...`

- **Objet** : exposer les **techniciens** et leurs affectations (magasins, PUDO principal/backup/hors normes).
- **Usages** :
  - récupérer la liste des techniciens ;
  - pour un technicien donné, lister ses magasins et PUDO associés.

---

### A.6. Domaine Helios (`/api/helios`)

#### A.6.1. `GET /api/helios/<code_article>/parc` (nom indicatif)

- **Description** : fournit une **synthèse du parc installé Helios** pour un article (écran `helios.html`).
- **Champs typiques** : `code_article`, `code_ig`, `qte_active`, `nb_sites_actifs`, autres KPI de parc.

- **Exemple de réponse** :

```json
{
  "code_article": "ABC123",
  "total_qte_active": 340,
  "nb_sites_actifs": 52,
  "details_par_code_ig": [
    { "code_ig": "FR12345", "qte_active": 12 },
    { "code_ig": "FR67890", "qte_active": 8 }
  ]
}
```

---

### A.7. Domaine Téléchargements (`/api/downloads`)

#### A.7.1. `GET /api/downloads/...`

- **Description** : fournir les fichiers d’export (CSV, Excel, …) pour les différents domaines (stock détaillé, stats de sorties, PUDO, etc.).
- **Réponse typique** : liste d’objets (`id`, `label`, `url` ou équivalent) permettant de déclencher un téléchargement.

---

## B. Changelog fonctionnel (extrait)

- **Version 1.3.0**
  - Introduction de la **catégorie "sans sortie"** pour les articles, avec exposition API et intégration dans les écrans `info_article` et `RECHERCHE_STOCK`.
  - Enrichissement des recherches d’articles par les **données fournisseurs** (nom fabricant, référence fabricant) via agrégation des informations de `manufacturers`.
  - Mise en place d’un **processus de mise à jour automatique** des données toutes les 30 minutes, avec suivi via l’endpoint `/api/updates/status` et affichage dans l’interface.
  - Alignement avec le packaging technique : binaire `SUPPLYCHAIN_APP_v1.3.0.exe` distribué aux utilisateurs internes.

- **Version 1.4.0**
  - Introduction de **OL MODE DÉGRADÉ V2** avec carte intégrée, tableau de stock unifié et règles de tri métier (tous les articles en stock, distance PR technicien, code magasin).
  - Meilleure intégration entre OL et les autres écrans (RECHERCHE_STOCK, Helios, statistiques de sorties) via des **liens contextuels sur les codes article**.
  - Mise à jour de la documentation fonctionnelle et technique (README, SPEC METIER) et alignement avec le packaging `SUPPLYCHAIN_APP_v1.4.0.exe`.

---

## C. Diffusion et déploiement auprès des utilisateurs métiers

- L’application est mise à disposition des utilisateurs sous forme d’un **exécutable Windows autonome** : `SupplyChainApp.exe`.
- Les modalités techniques de livraison (répertoire cible, création de raccourcis, gestion des messages de sécurité Windows, etc.) sont décrites dans le `README.md` (section "Livraison / déploiement de l'exécutable").
- Références techniques (pour l'équipe de maintenance) :
  - code Python sous `src/supplychain_app/` (structure `src/`),
  - frontend statique sous `web/`,
  - lancement en mode dev : `py -m supplychain_app.run` (API `127.0.0.1:5001` + frontend `127.0.0.1:8000`),
  - construction de l'exécutable : `scripts/build_exe.ps1` (PyInstaller) ou `SupplyChainApp.spec`.
- Du point de vue métier, il est recommandé :
  - de diffuser l’outil via les canaux habituels (portail interne, partage réseau sécurisé, procédure d’installation bureautique),
  - d’accompagner la diffusion par une courte **note d’usage** rappelant les principaux cas d’usage (consultation stock, identification articles dormants, recherche fournisseur, etc.).



