# ADR 0006 — Navigation du header (menus thématiques)

## Statut

Accepté

## Contexte

SupplyChainApp expose un frontend statique (`web/`) avec un header commun (généré en JavaScript) qui regroupe les liens vers les principaux écrans.

Au fur et à mesure des fonctionnalités ajoutées, la navigation devenait dense (trop de liens au même niveau), et certains écrans étaient mélangés dans un menu générique.

Objectifs :

- améliorer la lisibilité et réduire la charge visuelle ;
- regrouper les fonctionnalités par domaine métier (Helios, consommables) ;
- garder le menu **ADMINISTRATION** accessible, mais moins saillant (tout en conservant sa protection par mot de passe).

## Décision

1) Introduire des menus thématiques dédiés :

- menu **HELIOS** : regroupe l'accès à `helios.html`.
- menu **CONSOMMABLE** : regroupe l'accès à `catalogue_consommables.html`.

2) Réduire le contenu du menu **APPLICATIONS / OUTILS** :

- retirer les liens Helios et Consommables de ce menu ;
- conserver les outils transverses (ex: OL mode dégradé, téléchargements).

3) Placer **ADMINISTRATION** en fin de barre de navigation :

- le menu **ADMINISTRATION** reste protégé par mot de passe (cf. ADR 0005) ;
- il est affiché en dernier pour limiter l'ouverture involontaire.

## Conséquences

- **Positives**
  - Navigation plus claire : regroupement par domaines (Helios / Consommables).
  - Menu "Applications / Outils" recentré sur les outils transverses.
  - Administration toujours accessible mais moins exposée.

- **Négatives / Risques**
  - Un utilisateur habitué à l'ancien emplacement doit s'adapter.
  - Toute nouvelle page nécessite de maintenir la cohérence du regroupement.

- **Alternatives considérées**
  - Ajouter des liens en dur dans chaque page (rejeté : duplication / incohérences).
  - Passer à un framework UI (rejeté : surcoût technique non nécessaire).
