# ADR 0001 — Architecture en couches (routes / services / data)

## Statut

Accepté

## Contexte

Le projet SupplyChainApp expose une API Flask (blueprints) et un frontend statique (dossier `web/`).
Avec l’ajout de nouvelles fonctionnalités, le risque est de faire dériver la logique métier dans les routes HTTP,
ce qui rend les changements plus difficiles à tester et augmente les régressions.

## Décision

Adopter une architecture en couches :

- **Routes (HTTP / API)** : fichiers `routes.py` dans `src/supplychain_app/blueprints/*/`.
  - Responsabilité : validation minimale des entrées, orchestration, conversion en JSON/réponse HTTP.
  - Interdiction : règles métier profondes, transformations complexes difficiles à tester.

- **Services (métier / cas d’usage)** : modules dédiés (ex: `src/supplychain_app/services/`).
  - Responsabilité : implémenter les règles métier et cas d’usage (fonctions pures autant que possible).
  - Doit être testable unitairement avec des jeux de données minimaux.

- **Data access (ETL / IO / référentiels)** : modules dédiés (ex: `src/supplychain_app/data/`).
  - Responsabilité : lecture/écriture (parquet/excel), accès aux répertoires, cache, normalisation.
  - Doit exposer des primitives stables aux services.

La **spécification métier** reste la source de vérité dans `docs/spec/SPEC_METIER_SUPPLYCHAINAPP.md`.
Toute nouvelle fonctionnalité doit être décrite/ajustée dans cette spec.

## Conséquences

- **Positives**
  - Tests plus simples : la logique est concentrée dans les services.
  - Moins de régressions : les routes deviennent fines et stables.
  - Ajout de fonctionnalités plus rapide : on sait où mettre le code.

- **Négatives / Risques**
  - Légère complexité initiale : création de modules `services/` et `data/`.
  - Nécessite une discipline de contribution (PR + checklist).

- **Alternatives considérées**
  - Mettre toute la logique dans les routes : rejeté (testabilité faible, maintenance difficile).
  - Introduire un framework plus lourd : non nécessaire à ce stade.
