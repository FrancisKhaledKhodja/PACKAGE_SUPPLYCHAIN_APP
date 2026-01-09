# ADR 0007 — CSS séparé du HTML (pas de styles inline)

## Statut

Accepté

## Contexte

SupplyChainApp expose un frontend statique (`web/`) composé de pages HTML et de JavaScript.

Pour améliorer la maintenabilité, la cohérence visuelle et la capacité à faire évoluer l’UI sans modifier les pages, on souhaite formaliser une règle de séparation :

- la structure et le contenu dans le HTML,
- la logique dans le JavaScript,
- la présentation (styles) dans des fichiers CSS dédiés.

## Décision

1) Les styles doivent être centralisés dans des fichiers CSS

- Les pages HTML doivent référencer les styles via `<link rel="stylesheet" href="css/...">`.
- Les styles communs restent dans `web/css/style.css`.
- Les styles spécifiques peuvent être ajoutés dans des fichiers dédiés (ex : `web/css/<page>.css`) si nécessaire.

2) Interdictions côté HTML

- Pas de styles inline via l’attribut `style="..."`.
- Pas de balises `<style>...</style>` dans les pages.

3) Exceptions

- Exceptions possibles uniquement si documentées explicitement dans l’ADR ou dans une règle de contribution dédiée, et limitées à des cas techniques (ex : styles injectés par une librairie tierce).

## Conséquences

- **Positives**
  - Maintenabilité accrue (évite la duplication et les divergences de styles entre pages).
  - UI plus cohérente (thèmes, variables CSS, composants réutilisables).
  - Modifications de style possibles sans toucher au HTML.

- **Négatives / Risques**
  - Nécessite une discipline lors des évolutions (refuser les ajouts de styles inline).
  - Certaines pages existantes devront être refactorées progressivement (migration des styles inline vers CSS).

- **Alternatives considérées**
  - Laisser des styles inline pour itérer plus vite : rejeté (dette technique rapide, incohérences).
  - CSS-in-JS : rejeté (frontend statique sans framework, complexité inutile).
