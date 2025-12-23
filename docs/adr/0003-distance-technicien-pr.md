# ADR 0003 — Distances/durées technicien ↔ points relais (distance_tech_pr)

## Statut

Accepté

## Contexte

Plusieurs écrans “techniciens / points relais” nécessitent d’afficher des informations opérationnelles supplémentaires :

- la **distance routière** (voiture) entre le magasin du technicien (`code_magasin`) et ses points relais (PR),
- la **durée de trajet** associée.

Ces informations sont fournies par un fichier parquet dédié `distance_tech_pr.parquet` (colonnes attendues : `code_magasin`, `code_pr`, `distance`, `duration`).

Contraintes :

- l’application est composée d’un frontend statique (`web/`) et d’une API Flask (`/api/*`) ;
- les fichiers métiers peuvent être copiés dans un répertoire applicatif via l’ETL (`update_data()`), mais en environnement existant certains fichiers peuvent déjà être disponibles dans un autre répertoire de référence ;
- la solution doit rester robuste (fallback en cas d’absence de données) et ne pas casser l’affichage des pages existantes.

## Décision

- Ajouter `distance_tech_pr.parquet` au mécanisme d’ETL / mise à jour (copie vers le répertoire de données applicatif quand la source est plus récente).
- Exposer une API dédiée dans le blueprint `technicians` :
  - `GET /api/technicians/<code_magasin>/distances_pr`
  - retourne les lignes de `distance_tech_pr.parquet` filtrées sur `code_magasin`.
- Côté frontend, afficher distance/durée :
  - sous les PR dans `technician.html` et `technician_admin.html`,
  - dans le tableau `technician_assignments.html`.
- Conversion d’unités côté UI :
  - `distance` (mètres) → kilomètres (km),
  - `duration` (secondes) → minutes.
- En cas de donnée absente (pas de ligne trouvée pour un PR), afficher un message neutre : **“Distance/durée indisponibles”**.
- Robustesse IO : si `distance_tech_pr.parquet` n’est pas présent dans le répertoire applicatif attendu, l’API tente un **chemin alternatif** connu (afin d’éviter une rupture en attendant la mise en place complète des copies ETL sur tous les environnements).

## Conséquences

- **Positives**
  - Visibilité opérationnelle : le technicien peut évaluer rapidement la pertinence d’un PR.
  - API réutilisable par plusieurs écrans.
  - Implémentation localisée (services + route fine), cohérente avec l’ADR 0001.

- **Négatives / Risques**
  - Les données peuvent être incomplètes (ex : certains PR non présents dans le parquet) → affichage “indisponibles”.
  - Coût de requêtes multiples côté frontend (notamment sur `technician_assignments.html` si beaucoup de magasins) ; à surveiller.
  - Le chemin alternatif est un compromis : il augmente la robustesse, mais doit rester documenté et contrôlé.

- **Alternatives considérées**
  - Calculer la distance à la volée via une API externe : rejeté (dépendance réseau, quota, temps de réponse, complexité).
  - Stocker les distances dans une base SQL : non retenu à ce stade (parquets suffisants, ETL déjà en place).
