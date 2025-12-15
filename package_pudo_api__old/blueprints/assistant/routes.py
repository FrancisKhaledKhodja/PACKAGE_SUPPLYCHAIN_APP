import json
import os

from flask import request, jsonify

from . import bp


def _load_spec_excerpt(max_chars: int = 6000) -> str:
    """Charge un extrait de la SPEC_METIER_SUPPLYCHAINAPP.md pour fournir du contexte au LLM.

    On tronque volontairement pour éviter d'envoyer un prompt trop volumineux.
    """
    try:
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
        spec_path = os.path.join(base_dir, "SPEC_METIER_SUPPLYCHAINAPP.md")
        if not os.path.exists(spec_path):
            return ""
        with open(spec_path, "r", encoding="utf-8") as f:
            content = f.read()
        return content[:max_chars]
    except Exception:
        return ""


@bp.post("/query")
def assistant_query():
    """Point d'entrée assistant basé sur un LLM on-prem (Ollama).

    Corps attendu : { "question": "..." }

    Réponse :
    {
      "answer": "texte à afficher",
      "intent": "view_stock_article" | "view_stock_map" | "view_nearest_pudo" | "none",
      "params": { ... },
      "target_page": "stock.html" | "stock_map.html" | "stores.html" | null
    }
    """
    body = request.get_json(silent=True) or {}
    question = (body.get("question") or "").strip()
    if not question:
        return jsonify({"error": "question_required"}), 400

    # Chargement optionnel de la spec metier : desactive par defaut,
    # peut etre active via ASSISTANT_ENABLE_SPEC=1/true/yes
    spec_enabled = os.environ.get("ASSISTANT_ENABLE_SPEC", "0").lower() in ("1", "true", "yes")
    spec_excerpt = _load_spec_excerpt() if spec_enabled else ""

    system_prompt = (
        "Tu es un ROUTEUR D'ACTIONS pour l'application interne SupplyChainApp (gestion des articles, stocks, magasins et points relais). "
        "TU NE DOIS PAS FOURNIR LES VALEURS RÉELLES DE STOCK, NI ACCÉDER À UNE BASE DE DONNÉES. "
        "Ton rôle est UNIQUEMENT de décider quel écran ouvrir, quels paramètres passer et quel court message afficher.\n"

        "L'utilisateur pose des questions en français et l'interface a besoin de savoir :\n"
        "- quelle action lancer (quel écran ouvrir) ;\n"
        "- avec quels paramètres (code article, adresse, etc.) ;\n"
        "- et quel petit texte afficher comme réponse.\n\n"

        "TA RÉPONSE DOIT TOUJOURS ÊTRE UN JSON STRICT, SANS TEXTE AUTOUR, de la forme :\n"
        "{\n  \"answer\": <string>,\n  \"intent\": <string>,\n  \"params\": <object>,\n  \"target_page\": <string or null>\n}\n\n"

        "Les valeurs possibles de intent sont :\n"
        "- view_stock_article : ouvrir l'onglet RECHERCHE_STOCK (stock.html) pour un ou plusieurs codes article ;\n"
        "- view_stock_map : ouvrir l'onglet de localisation du stock (stock_map.html) ;\n"
        "- view_nearest_pudo : ouvrir l'onglet Magasins & points relais (stores.html) pour chercher des PR/magasins proches ;\n"
        "- photos: ouvrir l'onglet de la photo de l'article (photos.html)"
        "- helios: ouvrir l'onglet du parc hélios (helios.html)"
        "- technicians: ouvrir l'onglet du magasin (technicians.html)"
        "- none : aucune action précise possible (simple réponse texte).\n\n"

        "La clé target_page doit être :\n"
        "- \"stock.html\" si l'action principale concerne le stock d'article (view_stock_article) ;\n"
        "- \"stock_map.html\" si l'action principale est la carte de localisation du stock (view_stock_map) ;\n"
        "- \"stores.html\" si l'action principale concerne les magasins / points relais (view_nearest_pudo) ;\n"
        "- null si aucune page ne doit être ouverte.\n\n"

        "La clé params est un objet JSON avec les paramètres utiles :\n"
        "- pour view_stock_article : {\"code_article\": \"TDF000629\"} (un seul code) ;\n"
        "- pour view_stock_map : {\"code_article\": \"TDF000629\"} ou {\"address\": \"100 rue ... 75000 Paris\"} ;\n"
        "- pour view_nearest_pudo : {\"address\": \"100 rue ... 75000 Paris\"}.\n\n"

        "Exemples de mapping attendu :\n"
        "- Question : \"donne moi le stock du code article TDF000629\"\n"
        "  → TU NE DONNES PAS LA VALEUR DU STOCK. Tu retournes par exemple :\n"
        "  {\n    \"answer\": \"J'ouvre l'écran de stock pour l'article TDF000629.\",\n    \"intent\": \"view_stock_article\",\n    \"params\": {\"code_article\": \"TDF000629\"},\n    \"target_page\": \"stock.html\"\n  }\n"
        "- Question : \"montre la localisation du stock de TDF000629 autour de Lyon\"\n"
        "  → intent = \"view_stock_map\", params = {code_article: \"TDF000629\", address: \"Lyon\"}, target_page = \"stock_map.html\".\n\n"

        "Règles spécifiques pour les questions de points relais (PR) :\n"
        "- Si la question contient les mots \"point relais\", \"points relais\" ou \"PR\" ou \"pr\" ou le mot \"relais\" tout seul, tu dois en général choisir intent = \"view_nearest_pudo\".\n"
        "- Si la question contient une adresse complète (numéro, rue, code postal, ville), utilise cette adresse telle quelle dans params.address.\n"
        "- Si la question contient une adresse complète (numéro, rue, ville), utilise cette adresse telle quelle dans params.address.\n"
        "- Si la question contient une adresse complète (rue, ville), utilise cette adresse telle quelle dans params.address.\n"
        "- Si la question ne contient qu'un nom de ville (par ex. \"Bergerac\", \"Lyon\", \"Bordeaux\"), considère ce nom de ville comme une adresse valide et mets-le dans params.address.\n"
        "- Dans ces cas, utilise target_page = \"stores.html\".\n"
        "- SI TU CHOISIS intent = \"view_nearest_pudo\" ALORS params.address DOIT TOUJOURS ÊTRE RENSEIGNÉ (jamais vide ou manquant).\n"
        "- Ne mets JAMAIS intent = \"view_nearest_pudo\" sans fournir une valeur non vide pour params.address.\n\n"
        "- Question : \"quel est le point relais le plus proche de mon domicile qui est le 100 rue Lepic 75018 Paris\"\n"
        "  → intent = \"view_nearest_pudo\", params = {address: \"100 rue Lepic 75018 Paris\"}, target_page = \"stores.html\".\n"
        "- Question : \"quels sont les points relais proches de Bergerac\" (même si l'utilisateur écrit \"prochent\" ou fait une petite faute)\n"
        "  → intent = \"view_nearest_pudo\", params = {address: \"Bergerac\"}, target_page = \"stores.html\".\n"
        "- Question : \"montre moi les points relais autour de Bordeaux\"\n"
        "  → intent = \"view_nearest_pudo\", params = {address: \"Bordeaux\"}, target_page = \"stores.html\".\n\n"


        "Si tu n'es pas sûr, choisis intent = \"none\", params = {}, target_page = null, mais garde un champ answer explicatif.\n"
        "NE RETOURNE RIEN D'AUTRE QU'UN JSON VALIDE. PAS DE COMMENTAIRE, PAS DE TEXTE EN DEHORS DU JSON.\n"
        "NE METS JAMAIS de ``` ni de bloc markdown, ni de préfixe comme JSON:. \n"
        "RÉPONDS UNIQUEMENT par un JSON brut, sans backticks, sans balises de code, sans texte autour.\n"
    )

    if spec_excerpt:
        system_prompt += ("\nContexte métier (extrait de la spécification) :\n\n" + spec_excerpt)

    # Mode règles uniquement (pas de dépendance Ollama/LLM) :
    # on route l'utilisateur vers le bon écran à partir de mots-clés.
    lower_q = (question or "").lower()
    params = {}
    target_page = None
    intent = "none"
    answer = ""

    import re

    article_match = re.search(r"\b([A-Z]{2,}\d{3,}|TDF\d{3,})\b", question or "", re.IGNORECASE)
    code_article = article_match.group(1).upper() if article_match else None

    mentions_pr = (
        "point relais" in lower_q
        or "points relais" in lower_q
        or "point-relais" in lower_q
        or "points-relais" in lower_q
        or " pr " in lower_q
        or "relais" in lower_q
    )
    mentions_stock = "stock" in lower_q
    mentions_map = ("carte" in lower_q) or ("localisation" in lower_q) or ("localiser" in lower_q)
    mentions_photos = ("photo" in lower_q) or ("photos" in lower_q)
    mentions_helios = "helios" in lower_q
    mentions_technicians = ("technicien" in lower_q) or ("techniciens" in lower_q)

    if mentions_photos and code_article:
        intent = "photos"
        params = {"code_article": code_article}
        target_page = "photos.html"
        answer = f"J'ouvre l'écran photo pour l'article {code_article}."
    elif mentions_helios:
        intent = "helios"
        params = {}
        target_page = "helios.html"
        answer = "J'ouvre l'écran du parc Hélios."
    elif mentions_technicians:
        intent = "technicians"
        params = {}
        target_page = "technician.html"
        answer = "J'ouvre l'écran magasin / technicien."
    elif mentions_stock and mentions_map:
        intent = "view_stock_map"
        target_page = "stock_map.html"
        if code_article:
            params["code_article"] = code_article
        answer = "J'ouvre la carte de localisation du stock."
    elif mentions_stock and code_article:
        intent = "view_stock_article"
        target_page = "stock.html"
        params = {"code_article": code_article}
        answer = f"J'ouvre l'écran de stock pour l'article {code_article}."
    elif mentions_pr and not mentions_stock:
        intent = "view_nearest_pudo"
        target_page = "stores.html"
        # Extraction simple d'une adresse/ville à partir de la question
        addr = ""
        markers = [
            "qui est le",
            "qui est",
            "domicile",
            "adresse",
            "au ",
            " a ",
        ]
        for m in markers:
            idx = lower_q.find(m)
            if idx != -1:
                addr = (question or "")[idx + len(m):].strip()
                break
        if not addr:
            cp_match = re.search(r"\b\d{5}\b", question or "")
            if cp_match:
                cp_index = cp_match.start()
                addr = (question or "")[max(0, cp_index - 30):].strip()
        if not addr:
            tokens = [t for t in (question or "").split() if t]
            if tokens:
                addr = tokens[-1]
        if addr:
            params["address"] = addr
        answer = "J'ouvre l'écran Magasins & points relais autour de l'adresse demandée."
    else:
        intent = "none"
        params = {}
        target_page = None
        answer = "Je n'ai pas pu interpréter cette question."

    # Correction côté backend de l'intent pour les questions PR évidentes :
    # si la question contient "point relais" / "points relais" / "pr" / "relais" sans parler de stock,
    # on force intent = view_nearest_pudo et target_page = stores.html.
    mentions_pr = (
        "point relais" in lower_q
        or "points relais" in lower_q
        or "point-relais" in lower_q
        or "points-relais" in lower_q
        or " pr " in lower_q
        or "relais" in lower_q
    )
    mentions_stock = "stock" in lower_q
    if mentions_pr and not mentions_stock:
        intent = "view_nearest_pudo"
        if not target_page:
            target_page = "stores.html"

    # Normalisation / sécurisation des paramètres pour les points relais :
    # si intent = view_nearest_pudo mais que le LLM a oublié de renseigner params.address,
    # on essaie de déduire une adresse simple à partir de la question.
    if intent == "view_nearest_pudo":
        addr = (
            params.get("address")
            or params.get("adresse")
            or params.get("location")
            or params.get("city")
        )
        if not addr:
            q = question or ""
            lower_q = q.lower()
            markers = [
                "qui est le",
                "qui est",
                "domicile",
                "adresse",
                "au ",
                " a ",
            ]
            for m in markers:
                idx = lower_q.find(m)
                if idx != -1:
                    addr = q[idx + len(m):].strip()
                    break

            if not addr:
                import re

                cp_match = re.search(r"\b\d{5}\b", q)
                if cp_match:
                    cp_index = cp_match.start()
                    addr = q[max(0, cp_index - 30):].strip()

            if not addr:
                tokens = [t for t in q.split() if t]
                if tokens:
                    addr = tokens[-1]

        if addr:
            cleaned_addr = (addr or "").strip().strip("\"'` ")
            cleaned_addr = cleaned_addr.strip(" \t\r\n!?.,;:()[]{}<>|/")
            if len(cleaned_addr) < 2 or cleaned_addr.lower() in ("x", "xx", "n/a", "na", "?"):
                cleaned_addr = ""
            if not cleaned_addr:
                params.pop("address", None)
                import re

                q = (question or "").strip().strip("\"'` ")
                q = q.strip(" \t\r\n!?.,;:()[]{}<>|/")
                m = re.search(r"([A-Za-zÀ-ÿ\-']{2,})\s*$", q)
                if m:
                    cleaned_addr = m.group(1).strip()
            if cleaned_addr:
                params["address"] = cleaned_addr

    return jsonify({
        "answer": answer,
        "intent": intent,
        "params": params,
        "target_page": target_page,
    })
