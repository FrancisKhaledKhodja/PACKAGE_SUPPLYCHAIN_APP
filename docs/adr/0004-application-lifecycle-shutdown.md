# ADR 0004 — Cycle de vie application (heartbeat, Quitter, auto-stop)

## Statut

Accepté

## Contexte

SupplyChainApp est une application locale composée de :

- un **frontend statique** servi sur `http://127.0.0.1:8000/` (HTML/CSS/JS),
- une **API Flask** sur `http://127.0.0.1:5001/api/*`.

En pratique, **fermer un onglet navigateur ne stoppe pas** un serveur backend.
Cela provoquait des cas où plusieurs instances restaient actives (ports occupés, comportements incohérents, nécessité de tuer les processus via le gestionnaire des tâches).

Objectif : garantir un arrêt fiable et simple pour l’utilisateur, sans exiger des commandes techniques.

## Décision

1) Ajouter un mécanisme de **heartbeat** :

- Le frontend envoie périodiquement `POST /api/app/ping`.
- Le backend stocke le dernier timestamp de ping.

2) Ajouter un endpoint de fermeture explicite :

- `POST /api/app/exit` déclenche un arrêt propre de l’application.
- Le header expose un bouton **Quitter** qui appelle cet endpoint.

3) Ajouter un **watchdog** côté application :

- si aucun heartbeat n’est reçu pendant une courte période (ex: ~45s), l’application se ferme automatiquement.

4) Rendre l’arrêt réalisable techniquement :

- l’API est servie via un serveur contrôlable (`make_server`) afin de pouvoir invoquer `shutdown()`.
- le serveur HTTP frontend est également stoppable.

## Conséquences

- **Positives**
  - Fermeture fiable via un bouton UI (**Quitter**) et/ou fermeture automatique en cas d’inactivité.
  - Réduction des processus “zombies” et des conflits de ports.
  - Réduction des incidents utilisateur (moins de manipulations via Task Manager / netstat).

- **Négatives / Risques**
  - Si un navigateur/onglet reste ouvert en arrière-plan, le heartbeat maintient l’application active.
  - Le délai d’auto-stop est un compromis (trop court = arrêts intempestifs ; trop long = processus persistants).

- **Alternatives considérées**
  - Compter sur la fermeture du navigateur : insuffisant (pas de lien direct avec l’arrêt des serveurs).
  - Demander aux utilisateurs de tuer les processus : rejeté (trop technique).
  - Intégrer un wrapper type Electron : non retenu à ce stade.
