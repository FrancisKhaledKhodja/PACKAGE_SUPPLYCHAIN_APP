# ADR 0002 — Assistant : réponses fondées sur sources (anti-hallucinations)

## Statut

Accepté

## Contexte

SupplyChainApp inclut un assistant de navigation (LLM on-prem via endpoint `/api/assistant/query`).
L’assistant doit aider l’utilisateur à ouvrir le bon écran avec les bons paramètres.

Risque identifié : un LLM peut « halluciner » des règles métier (ou des écrans/actions) qui ne sont pas couvertes par la spécification,
ou proposer des actions non justifiées. Cela augmente les erreurs et la dette de maintenance.

## Décision

Quand l’assistant est exécuté avec le contexte de spécification métier activé (variable d’environnement `ASSISTANT_ENABLE_SPEC=1/true/yes`) :

- L’assistant doit produire une réponse JSON incluant un champ **`sources`**.
- Le champ `sources` doit référencer explicitement le contexte utilisé (au minimum : la spec métier).
- Si l’assistant ne peut pas s’appuyer sur la spécification (pas de source pertinente), il doit répondre avec `intent = "none"`.

Le backend applique un garde-fou : si la spec est activée et que la réponse du LLM ne contient pas de `sources`, le backend neutralise l’action
(`intent = "none"`, `target_page = null`, `params = {}`) et renvoie un message demandant une clarification ou une mise à jour de la spec.

## Conséquences

- **Positives**
  - Réduction des actions « inventées ».
  - Traçabilité : on sait sur quel passage de la spec l’assistant s’appuie.
  - Process clair : une question non couverte devient un signal pour enrichir la spec.

- **Négatives / Risques**
  - Réponses potentiellement plus « prudentes » (plus de `intent = "none"`).
  - Nécessite de garder la spec métier à jour.

- **Alternatives considérées**
  - Laisser l’assistant répondre librement : rejeté (risque d’hallucinations).
  - Bloquer complètement le LLM : rejeté (perte d’usage).
