# SupplyChainApp – Présentation métier (10 min) + Annexes SI/Tech + Data (v1.5.0)

## Objectif de la présentation (10 min)
Présenter SupplyChainApp de manière **positive et orientée valeur** pour une audience **direction + opérationnel**.

## Messages clés (à marteler)
- **Gain de temps** immédiat (moins de recherche, moins d’allers-retours).
- **Fiabilisation** de l’information (règles métiers intégrées, sources consolidées).
- **Décision actionnable** (adresse, statut, contact, localisation, etc.).
- **
- **Industrialisation** (EXE, logs, évolutions versionnées).
- **

---

# Slides (pitch 10 minutes) – contenu prêt à coller

## Slide 1 — SupplyChainApp : la promesse
- Centraliser l’information Supply / Magasin / Points Relais
- Donner une réponse **rapide, actionnable, fiable**
- Réduire le temps de recherche et les risques d’erreur

## Slide 2 — Constat terrain (Pourquoi)
- Données et outils historiquement **dispersés**
- Temps perdu à recouper les sources
- Risque d’actions basées sur une info incomplète
- Objectif : **accélérer** l’opérationnel tout en **fiabilisant** la décision

## Slide 3 — Ce que l’outil apporte (Valeur)
- Une interface unique pour :
  - **Article / stock** (consultation & analyse)
  - **Magasins & PR** (carte + détails)
  - **OL** (dont mode dégradé)
  - **Demande de modification article** (email standard + export Excel)
  - **Assistance LLM/RAG** (questions en langage naturel)
- Une logique pensée “métier” : du **besoin** vers la **réponse**

## Slide 4 — Consultation d’un article (cas d’usage direction + terrain)
- Retrouver un article rapidement (référence / critères)
- Accéder immédiatement aux informations utiles pour décider
- Bénéfice : **moins d’aller-retour**, réponse plus rapide

## Slide 5 — Stock & localisation : rendre le stock exploitable
- Lecture stock adaptée à l’opérationnel
- **Localisation du stock** : meilleure compréhension de “où agir”
- Gain : arbitrage plus rapide + meilleure efficacité terrain

## Slide 6 — Magasins & Points relais : vision opérationnelle
- Recherche par adresse / zone + restitution claire
- Carte + tableau : repérage rapide
- Données PR enrichies (enseigne / adresse / statut…)

## Slide 7 — Démo live (2–3 min) : Magasins & PR autour d’une adresse (Démo B)
- Saisir une adresse + rayon
- Afficher magasins/PR sur carte + liste
- Ouvrir un résultat et lire enseigne/adresse/statut
- Message : “Question terrain → réponse actionnable en quelques secondes.”

## Slide 8 — LLM / RAG (activé) : accélérer la recherche et sécuriser la réponse
- Objectif : **accélérer l’accès à l’information** via questions en langage naturel
- Le RAG apporte un contexte (données/catalogue/doc) pour des réponses plus pertinentes
- Cas concret (déterministe) : **"besoin de X unités d’un code article pour un projet"**
  - analyse `stock_final.parquet` (GOOD projet, GOOD autres PJ par ancienneté, GOOD maintenance, BAD)
  - sortie : synthèse + **proposition d’actions** (prioriser ancienneté, bascule maintenance si autorisée, réparations si BAD)
- Bénéfices :
  - gain de temps
  - standardisation des réponses
  - onboarding facilité

## Slide 9 — Demande de modification article (criticité) : standardiser et accélérer
- Besoin : formaliser une demande de changement de criticité **sans Excel manuel**
- Saisie guidée multi-lignes (code article / nouvelle criticité / cause)
- Sorties automatiques :
  - email standardisé (objet + corps TSV)
  - fichier Excel généré et sauvegardé sur le partage (traçabilité)
- Bénéfices : moins d’erreurs + traitement plus rapide + demande homogène

## Slide 10 — OL mode dégradé : option “continuité de service”
- Objectif : **assurer le service** même en contexte contraint
- Accès à l’essentiel pour maintenir l’opérationnel prioritaire
- Bénéfices : résilience, réduction de l’impact business

## Slide 11 — Industrialisation + trajectoire
- Déploiement simplifié (EXE) et exploitation sécurisée (logs)
- Évolutions itératives orientées besoins terrain
- Prochaines étapes possibles : UX, data, indicateurs, extensions assistant

---

# Script démo live (3–4 min) – recommandé

## Bloc 1 — Démo B (2 minutes) : Magasins & PR autour d’une adresse
- 00:00–00:20 : “Cas terrain : identifier rapidement magasins/PR autour d’une zone.”
- 00:20–01:20 : adresse + rayon → carte + liste.
- 01:20–02:20 : ouvrir un résultat → enseigne/adresse/statut.
- 02:20–03:00 : “gain de temps + fiabilité”.

## Bloc 2 — LLM/RAG (1–2 minutes) : “question → réponse orientée action”
- Préparer 2 questions “safe” :
  1) “Comment retrouver rapidement les infos d’un magasin / PR et quoi vérifier ?”
  2) “En mode dégradé OL, qu’est-ce qu’on peut continuer à faire en priorité ?”
- Conclusion : “Assistance = orientation + gain de temps, le métier reste au centre.”

## Bloc 3 — Demande de modification article (1 minute) : “demande standard en 30 secondes”
- Cas : "Changement de criticité" sur 1–3 articles
- Démo :
  - ouvrir `article_request.html`
  - saisir prénom/nom + lignes (code + nouvelle criticité + cause)
  - valider : sauvegarde Excel sur partage + mail standard prêt à envoyer
- Message : “Demande homogène + traçable, pas de ressaisie Excel.”

---

# Annexes SI / Technique (slides)

## Annexe SI 1 — Questions en langage naturel (page d’accueil) : comment ça marche
- La page `home.html`/`home.js` envoie la question vers `POST /api/assistant/query`.
- Le backend renvoie un JSON :
  - `answer` (texte court)
  - `intent` (action)
  - `params` (code article, adresse, etc.)
  - `target_page` (page à ouvrir)
- Le frontend ouvre la page cible avec les paramètres.
- Résilience : si le LLM est indisponible, fallback en **mode règles**.

## Annexe SI 2 — Sécurité login / mot de passe à l’ouverture
- Finalité : identifiants utilisés pour **l’authentification proxy** sur certaines requêtes sortantes (ex : géocodage).
- Transit : envoi en JSON vers `POST /api/auth/login` (en EXE : flux local/localhost).
- Stockage : `session["proxy_login"]` / `session["proxy_password"]` côté serveur Flask.
- Point de vigilance : la sécurité de session dépend de `SECRET_KEY` (recommandation : valeur robuste via variable d’environnement).

## Annexe SI 3 — LLM / RAG : architecture
- LLM : **Ollama on-prem** (HTTP `/api/chat` avec fallback `/api/generate`).
- RAG : **ChromaDB** persistant (index local) utilisé comme contexte.
- Le prompt “assistant routeur” vise à **router** l’utilisateur (pas à “donner la valeur de stock”).

## Annexe SI 4 — Préparation du LLM et du RAG
- LLM : pas d’entraînement dans l’app, configuration d’un modèle existant via Ollama (URL/modèle/timeout).
- RAG : index construit depuis un `catalog.json` (tables + joins) via `POST /api/assistant/rag/build`.
- Embeddings :
  - par défaut `hash` (offline, déterministe)
  - option SentenceTransformers si disponible.

---

# Annexes Data (Option B – détaillée)

## Annexe Data 1 — Vision d’ensemble : “Source → ETL → Référentiel local → Écrans”
- **Sources amont** (réseau/extractions)
- **ETL / synchronisation** (copie + conversions)
- **Référentiel local applicatif** (Parquet)
- **Consommation** via services API (lecture rapide)

Schéma (simplifié) :

```
[Sources réseau]
   |  (parquets + excel annuaire)
   v
[ETL: update_data()]  -> comparaison mtime -> conversion/copie
   |
   v
[D:\Datan\...\supply_chain_app\]  (parquets locaux)
   |
   v
[API Flask / écrans web]  (articles, stock, carte stock, magasins/PR, OL, etc.)
```

## Annexe Data 2 — Sources amont (références)
- Exports SupplyChain (parquets) :
  - `\\apps\Vol1\Data\011-BO_XI_entrees\07-DOR_DP\Sorties\FICHIERS_ANALYSES_SUPPLY_CHAIN\FICHIERS_PARQUET`
- Référentiel PR – annuaire :
  - `R:\24-DPR\11-Applications\04-Gestion_Des_Points_Relais\Data\GESTION_PR\ANNUAIRE_PR`
- Choix PR technicien (override métier) :
  - `R:\...\GESTION_PR\CHOIX_PR_TECH\choix_pr_tech.parquet`
- Stock temps réel “554” (Excel) :
  - `\\apps\Vol1\Data\011-BO_XI_entrees\07-DOR_DP\Sorties\554 - (STK SPD TPS REEL) - STOCK TEMPS REEL SUPPLYCHAIN_APP.xlsx`

## Annexe Data 3 — Référentiel local (parquets consommés)
Dépôt local (selon config) : `path_datan` + `folder_name_app` (ex : `D:\Datan\supply_chain_app\`).

- `pudo_directory.parquet` (annuaire PR)
- `stores.parquet`
- `helios.parquet`
- `items.parquet`
- `nomenclatures.parquet`
- `manufacturers.parquet`
- `equivalents.parquet`
- `items_parent_buildings.parquet`
- `items_without_exit_final.parquet`
- `minmax.parquet`
- `stats_exit.parquet`
- `stock_final.parquet`
- `stock_554.parquet` (généré/enrichi)

## Annexe Data 4 — ETL / rafraîchissement (mécanisme)
- Le module `supplychain_app.data.pudo_etl` :
  - `get_update_status()` compare `src_mtime` vs `dst_mtime` et déduit `needs_update`.
  - `update_data()` :
    - convertit l’annuaire PR Excel en `pudo_directory.parquet` si plus récent
    - copie les parquets sources vers les parquets locaux si plus récents
    - génère `stock_554.parquet` en joignant `stores.parquet` + `items.parquet`
- En exécution applicative :
  - un thread de fond lance `update_data()` périodiquement (~30 minutes).

## Annexe Data 5 — Règles métier “data-driven” (exemples)
- **PR consultation magasin** :
  - si override présent dans `choix_pr_tech.parquet`, c’est ce PR qui est affiché
  - les détails PR (enseigne/adresse/statut) sont enrichis via `pudo_directory.parquet`

## Annexe Data 6 — Qualité, traçabilité, exploitation
- Traçabilité : date source vs date cible (mtime) + statut de mise à jour.
- Robustesse : en cas d’indisponibilité réseau, l’app peut continuer sur la dernière base locale disponible (selon cas).
- Gouvernance : référentiels identifiés (stores / PR / items / stock) et règles explicites (override PR).

---

# Notes de présentation (phrases “direction-safe”)
- “On ne cherche pas à montrer plus de données, on cherche à rendre l’information **actionnable**.”
- “Le LLM/RAG est une **assistance** : orientation et gain de temps, pas une décision automatique.”
- “Le mode dégradé OL est une **assurance de continuité**.”
