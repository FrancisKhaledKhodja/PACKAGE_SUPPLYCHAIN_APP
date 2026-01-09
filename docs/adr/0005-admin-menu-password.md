# ADR 0005 — Menu Administration protégé par mot de passe (frontend)

## Statut

Accepté

## Contexte

SupplyChainApp expose un frontend statique (`web/`) avec un header commun (généré en JavaScript).

Certains écrans sont destinés à des usages d’administration et ne doivent pas être ouverts par inadvertance depuis la navigation standard, tout en restant accessibles facilement lorsque nécessaire.

Objectif : proposer un accès "Administration" simple côté UI, sans dépendre d’un mécanisme d’authentification serveur (application locale), en limitant au maximum la friction utilisateur.

## Décision

1) Regrouper les pages d’administration dans un menu dédié :

- Menu déroulant **ADMINISTRATION** dans le header.
- Liens regroupés :
  - `treatments.html`
  - `technician_admin.html`

2) Protéger l’ouverture de ce menu par un mot de passe en dur :

- Mot de passe : `12344321`.

3) Mémoriser le déverrouillage côté navigateur :

- Stockage dans `localStorage` (clé `scapp_admin_unlocked=1`) afin de ne demander le mot de passe qu’une seule fois, y compris à travers plusieurs onglets.

## Conséquences

- **Positives**
  - Accès simple et rapide aux pages d’administration.
  - Réduction des erreurs de navigation (moins d’accès involontaires).
  - Expérience utilisateur fluide : saisie unique du mot de passe (persistant via `localStorage`).

- **Négatives / Risques**
  - Ce mécanisme n’est pas une sécurité forte : le mot de passe est présent côté frontend.
  - Un utilisateur peut accéder directement à une page admin via l’URL si le serveur sert les fichiers statiques.

- **Alternatives considérées**
  - Authentification serveur (sessions / rôles) : non retenue pour le moment (application locale, complexité supplémentaire).
  - Stockage `sessionStorage` : rejeté (redemande du mot de passe à chaque nouvel onglet).
