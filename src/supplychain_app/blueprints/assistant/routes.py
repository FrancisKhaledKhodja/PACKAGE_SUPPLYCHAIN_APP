import json
import os
import re
from pathlib import Path

from flask import Blueprint, request, jsonify
import requests

from supplychain_app.core.paths import get_project_root_dir


bp = Blueprint("assistant", __name__)


CAPABILITIES = {
    "view_stock_article": {
        "target_page": "stock.html",
        "params": {"code_article": "string"},
        "examples": [
            "Quel est le stock du code article TDF000629 ?",
            "Quels sont les sorties du code article TDF000629 ?",
        ],
    },
    "view_stock_map": {
        "target_page": "stock_map.html",
        "params": {"code_article": "string?", "address": "string?"},
        "examples": [
            "Où sont localiser les stocks du code article TDF000629 ?",
            "Localiser le stock autour de Lyon",
        ],
    },
    "view_items": {
        "target_page": "items.html",
        "params": {"code_article": "string?", "q": "string?"},
        "examples": [
            "Quelles sont les informations de l'article TDF000629 ?",
            "Quelle est la nomenclature du code article TDF000629 ?",
            "Quelle est la criticité du code article TDF000629 ?",
        ],
    },
    "photos": {
        "target_page": "photos.html",
        "params": {"code_article": "string"},
        "examples": [
            "Quelles sont les photos du code article TDF000629 ?",
        ],
    },
    "helios": {
        "target_page": "helios.html",
        "params": {"code_article": "string?"},
        "examples": [
            "Quel le parc du code article TDF000629 ?",
        ],
    },
    "technicians": {
        "target_page": "technician.html",
        "params": {"q": "string?"},
        "examples": [
            "Quel le code magasin du technicien X ?",
            "Quel est le point relais principal du magasin 0803 ?",
        ],
    },
    "admin_pr": {
        "target_page": "technician_admin.html",
        "params": {},
        "examples": [
            "Administration PR",
        ],
    },
    "technician_assignments": {
        "target_page": "technician_assignments.html",
        "params": {
            "q": "string?",
            "store": "string?",
            "pr": "string?",
            "status": "string?",
            "roles": "list[string]?",
            "expand_store_roles": "bool?",
        },
        "examples": [
            "Quels sont les points relais en backup ?",
            "Quels sont les points relais hors normes fermés ?",
        ],
    },
    "ol_mode_degrade": {
        "target_page": "ol_mode_degrade.html",
        "params": {},
        "examples": [
            "Je dois passer une commande",
            "Passer un ordre de livraison",
        ],
    },
    "article_network": {
        "target_page": "article_network.html",
        "params": {"code_article": "string"},
        "examples": [
            "Montre le graphe / réseau d'équivalence pour TDF000629",
        ],
    },
    "exit_stats": {
        "target_page": "statistiques_sorties.html",
        "params": {"code_article": "string"},
        "examples": [
            "Statistiques de sorties pour TDF000629",
        ],
    },
    "view_nearest_pudo": {
        "target_page": "stores.html",
        "params": {"address": "string"},
        "examples": [
            "Quels sont les points relais proches de Bergerac ?",
            "Quels sont les points relais autour de 100 rue Lepic 75018 Paris ?",
        ],
    },
}


def _rag_available() -> bool:
    try:
        import importlib.util

        return importlib.util.find_spec("chromadb") is not None
    except Exception:
        return False


def _load_rag_catalog_module():
    from supplychain_app import rag_catalog

    return rag_catalog


def _load_spec_excerpt(max_chars: int = 6000) -> str:
    """Charge un extrait de la SPEC_METIER_SUPPLYCHAINAPP.md pour fournir du contexte au LLM.

    On tronque volontairement pour éviter d'envoyer un prompt trop volumineux.
    """
    try:
        root = get_project_root_dir()
        primary_spec_path = root / "docs" / "spec" / "SPEC_METIER_SUPPLYCHAINAPP.md"
        legacy_spec_path = root / "SPEC_METIER_SUPPLYCHAINAPP.md"
        spec_path = primary_spec_path if primary_spec_path.exists() else legacy_spec_path
        if not spec_path.exists():
            return ""
        with open(spec_path, "r", encoding="utf-8") as f:
            content = f.read()
        return content[:max_chars]
    except Exception:
        return ""


def _extract_first_json_object(text: str) -> str:
    if not text:
        return ""
    m = re.search(r"\{[\s\S]*\}", text)
    return m.group(0) if m else ""


def _parse_assistant_payload(raw_text: str) -> dict:
    if not raw_text:
        raise ValueError("empty_ollama_response")
    cleaned = raw_text.strip()
    try:
        payload = json.loads(cleaned)
    except Exception:
        obj = _extract_first_json_object(cleaned)
        if not obj:
            raise
        payload = json.loads(obj)

    if not isinstance(payload, dict):
        raise ValueError("assistant_payload_not_object")

    if "answer" not in payload or "intent" not in payload or "params" not in payload or "target_page" not in payload:
        raise ValueError("assistant_payload_missing_keys")

    if not isinstance(payload.get("params"), dict):
        payload["params"] = {}

    if "sources" in payload and not isinstance(payload.get("sources"), list):
        payload["sources"] = []

    return payload


def _ollama_route(question: str, system_prompt: str) -> dict:
    base_url = os.environ.get("ASSISTANT_OLLAMA_URL", "http://127.0.0.1:11434").rstrip("/")
    model = os.environ.get("ASSISTANT_OLLAMA_MODEL", "llama3.1").strip() or "llama3.1"
    timeout_s = float(os.environ.get("ASSISTANT_OLLAMA_TIMEOUT_S", "15"))

    url = f"{base_url}/api/chat"
    body = {
        "model": model,
        "stream": False,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": question},
        ],
        "options": {"temperature": 0},
    }

    r = requests.post(url, json=body, timeout=timeout_s)
    r.raise_for_status()
    data = r.json()

    content = ""
    if isinstance(data, dict):
        msg = data.get("message")
        if isinstance(msg, dict):
            content = (msg.get("content") or "").strip()
        if not content:
            content = (data.get("response") or "").strip()

    return _parse_assistant_payload(content)


def _ollama_text(question: str, system_prompt: str, *, model: str | None = None, timeout_s: float | None = None) -> str:
    base_url = os.environ.get("ASSISTANT_OLLAMA_URL", "http://127.0.0.1:11434").rstrip("/")
    model = (model or os.environ.get("ASSISTANT_OLLAMA_MODEL", "llama3.1")).strip() or "llama3.1"
    if timeout_s is None:
        timeout_s = float(os.environ.get("ASSISTANT_OLLAMA_TIMEOUT_S", "60"))

    # Ne pas utiliser les variables d'environnement de proxy (HTTP_PROXY/HTTPS_PROXY) pour Ollama.
    # Sur certains postes, le proxy intercepte les requêtes et renvoie des 404.
    session = requests.Session()
    session.trust_env = False

    chat_url = f"{base_url}/api/chat"
    chat_body = {
        "model": model,
        "stream": False,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": question},
        ],
        "options": {"temperature": 0},
    }

    r = session.post(chat_url, json=chat_body, timeout=timeout_s)
    if r.status_code == 404:
        # Fallback pour certaines versions/config d'Ollama : /api/generate
        gen_url = f"{base_url}/api/generate"
        gen_body = {
            "model": model,
            "stream": False,
            "prompt": f"{system_prompt}\n\nQuestion: {question}\nRéponse:",
            "options": {"temperature": 0},
        }
        gr = session.post(gen_url, json=gen_body, timeout=timeout_s)
        gr.raise_for_status()
        gdata = gr.json()
        if isinstance(gdata, dict):
            return (gdata.get("response") or "").strip()
        return ""

    r.raise_for_status()
    data = r.json()

    content = ""
    if isinstance(data, dict):
        msg = data.get("message")
        if isinstance(msg, dict):
            content = (msg.get("content") or "").strip()
        if not content:
            content = (data.get("response") or "").strip()

    return content


def _ollama_status_hint() -> str:
    base_url = os.environ.get("ASSISTANT_OLLAMA_URL", "http://127.0.0.1:11434").rstrip("/")
    try:
        session = requests.Session()
        session.trust_env = False
        r = session.get(f"{base_url}/api/tags", timeout=3)
        if r.status_code == 200:
            return f"Ollama détecté sur {base_url}."
        return f"Ollama non détecté sur {base_url} (HTTP {r.status_code})."
    except Exception:
        return (
            f"Impossible de joindre un serveur Ollama sur {base_url}. "
            "Vérifie que le service est lancé et/ou configure ASSISTANT_OLLAMA_URL."
        )


def _extract_code_article(question: str) -> str | None:
    m = re.search(r"\b([A-Z]{2,}\d{3,}|TDF\d{3,})\b", question or "", re.IGNORECASE)
    return m.group(1).upper() if m else None


def _extract_store_code(question: str) -> str | None:
    q = question or ""
    m = re.search(r"\b(M\d{3,6})\b", q, re.IGNORECASE)
    if m:
        return m.group(1).upper()
    m = re.search(r"\b(\d{4,6})\b", q)
    return m.group(1) if m else None


def _extract_pr_code(question: str) -> str | None:
    q = question or ""
    m = re.search(r"\b([A-Z]\d{3,6})\b", q, re.IGNORECASE)
    return m.group(1).upper() if m else None


def _extract_quality(question: str) -> str | None:
    q = (question or "").strip()
    if not q:
        return None
    m = re.search(r"\bqualit(?:e|é)\s+([A-Za-z0-9_\-]+)\b", q, re.IGNORECASE)
    if m:
        return m.group(1).upper()
    # fallback simple: si l'utilisateur dit juste "good" / "bad" (fréquent)
    lower_q = q.lower()
    if " good" in lower_q or lower_q.endswith("good"):
        return "GOOD"
    if " bloqb" in lower_q or lower_q.endswith("bloqb"):
        return "BLOQB"
    if " bad" in lower_q or lower_q.endswith("bad"):
        return "BAD"
    return None


def _quality_values(quality: str | None) -> list[str]:
    if not quality:
        return []
    q = quality.strip().upper()
    if not q:
        return []
    # Règle métier: "stock bad" => BAD + BLOQB
    if q == "BAD":
        return ["BAD", "BLOQB"]
    return [q]


def _wants_deployment_stock(question: str) -> bool:
    q = (question or "").lower()
    return "déploiement" in q or "deploiement" in q or "deployement" in q


def _extract_stock_dm_flag(question: str) -> str | None:
    q = (question or "").lower()
    if "déploiement" in q or "deploiement" in q or "deployement" in q:
        return "D"
    if "maintenance" in q:
        return "M"
    return None


def _extract_project_code(question: str) -> str | None:
    m = re.search(r"\b(PJ\d{6,})\b", question or "", re.IGNORECASE)
    return m.group(1).upper() if m else None


def _extract_requested_qty(question: str) -> int | None:
    q = question or ""
    if not q.strip():
        return None

    # Éviter de capter la quantité dans le code article (ex: TDF159698) ou le code projet (PJ00000564)
    q2 = re.sub(r"\bTDF\d{3,}\b", " ", q, flags=re.IGNORECASE)
    q2 = re.sub(r"\bPJ\d{6,}\b", " ", q2, flags=re.IGNORECASE)

    patterns = [
        # "besoin de 5"
        r"\bbesoin\s+(?:urgent\s+)?de\s+(\d{1,6})\b",
        # "j'ai besoin de 5" / "j'aurais besoin de 5"
        r"\bj['’]?ai\s+besoin\s+de\s+(\d{1,6})\b",
        r"\bj['’]?aurais\s+besoin\s+de\s+(\d{1,6})\b",
        # "fournir 5" / "communiquer 5" / "merci de ... 5"
        r"\bfournir\s+(\d{1,6})\b",
        r"\bcommuniquer\s+(\d{1,6})\b",
        r"\bmerci\s+de\s+me\s+communiquer\s+(\d{1,6})\b",
        # "requis : 5"
        r"\brequis\s*[:\-]?\s*(\d{1,6})\b",
        # "5 unités" / "5 exemplaires" / "5 codes" / "5 pièces"
        r"\b(\d{1,6})\s*(?:unit(?:e|é)s?|exemplaires?|codes?|pi(?:e|è)ces?)\b",
    ]

    for pat in patterns:
        m = re.search(pat, q2, re.IGNORECASE)
        if not m:
            continue
        try:
            return int(m.group(1))
        except Exception:
            return None

    return None


def _find_first_existing_col(schema: dict, candidates: tuple[str, ...]) -> str | None:
    for c in candidates:
        if c in schema:
            return c
    return None


def _category_sort_key(label: str) -> tuple[int, int, str]:
    """Heuristique pour trier les catégories d'ancienneté (plus ancien en premier).

    On essaie d'extraire un nombre (jours/mois) et on trie en décroissant.
    En cas d'échec, fallback alphabetique.
    """
    s = (label or "").strip().lower()
    if not s:
        return (0, 0, "")
    # extraire le plus grand nombre présent dans la string
    nums = [int(x) for x in re.findall(r"\d+", s) if x.isdigit()]
    if nums:
        return (1, max(nums), s)
    # certains labels type "A", "B"... on renvoie 0
    return (0, 0, s)


def _wants_all_articles(question: str) -> bool:
    q = (question or "").lower()
    return (
        "tous les articles" in q
        or "toutes les articles" in q
        or "tous articles" in q
        or "toutes articles" in q
        or "tous les codes" in q
        or "tous les codes article" in q
    )


def _wants_global_stock(question: str) -> bool:
    q = (question or "").lower()
    if "stock" not in q and "quantité" not in q and "quantite" not in q:
        return False
    # Si l'utilisateur parle explicitement de "tous les articles", c'est global.
    if _wants_all_articles(question):
        return True
    # Sinon, si aucun code article n'est mentionné mais qu'il y a un filtre (qualité / D/M),
    # c'est très probablement une demande globale.
    if _extract_code_article(question):
        return False
    if _extract_quality(question):
        return True
    if _extract_stock_dm_flag(question):
        return True
    return False


def _extract_address(question: str) -> str:
    q = question or ""
    lower_q = q.lower()
    addr = ""
    markers = [
        "qui est le",
        "qui est",
        "domicile",
        "adresse",
        "autour de",
        "autour du",
        "au ",
        " a ",
    ]
    for m in markers:
        idx = lower_q.find(m)
        if idx != -1:
            addr = q[idx + len(m):].strip()
            break
    if not addr:
        cp_match = re.search(r"\b\d{5}\b", q)
        if cp_match:
            cp_index = cp_match.start()
            addr = q[max(0, cp_index - 30):].strip()
    if not addr:
        tokens = [t for t in q.split() if t]
        if tokens:
            addr = tokens[-1]

    cleaned = (addr or "").strip().strip("\"'` ")
    cleaned = cleaned.strip(" \t\r\n!?.,;:()[]{}<>|/")
    if len(cleaned) < 2 or cleaned.lower() in ("x", "xx", "n/a", "na", "?"):
        return ""
    return cleaned


def _extract_roles(question: str) -> list[str]:
    q = (question or "").lower()
    roles = []
    if "principal" in q:
        roles.append("principal")
    if "backup" in q or "secours" in q:
        roles.append("backup")
    if "hors norme" in q or "hors normes" in q or "hn" in q:
        roles.append("hors_normes")
    return roles


def _rules_route(question: str) -> dict:
    lower_q = (question or "").lower()
    params: dict = {}
    target_page = None
    intent = "none"
    answer = "Je n'ai pas pu interpréter cette question."

    code_article = _extract_code_article(question)
    store_code = _extract_store_code(question)
    pr_code = _extract_pr_code(question)
    roles = _extract_roles(question)

    mentions_stock = "stock" in lower_q
    mentions_sorties = "sortie" in lower_q or "sorties" in lower_q
    mentions_map = ("carte" in lower_q) or ("localisation" in lower_q) or ("localiser" in lower_q) or ("où" in lower_q)
    mentions_photos = ("photo" in lower_q) or ("photos" in lower_q)
    mentions_helios = "helios" in lower_q or "hélios" in lower_q
    mentions_items = ("information" in lower_q) or ("informations" in lower_q) or ("nomenclature" in lower_q) or ("criticite" in lower_q) or ("criticité" in lower_q)
    mentions_network = "graphe" in lower_q or "réseau" in lower_q or "reseau" in lower_q or "network" in lower_q
    mentions_stats_sorties = "statistique" in lower_q and ("sortie" in lower_q or "sorties" in lower_q)

    mentions_pr = (
        "point relais" in lower_q
        or "points relais" in lower_q
        or "point-relais" in lower_q
        or "points-relais" in lower_q
        or " pr " in lower_q
        or "relais" in lower_q
    )
    mentions_technicians = ("technicien" in lower_q) or ("techniciens" in lower_q) or ("magasin" in lower_q)
    mentions_assignments = "affectation" in lower_q or "affectations" in lower_q or "assign" in lower_q
    mentions_admin_pr = "administration pr" in lower_q or ("admin" in lower_q and "pr" in lower_q)
    mentions_ol = "ordre de livraison" in lower_q or "commande" in lower_q or "ol" in lower_q

    if mentions_photos and code_article:
        intent = "photos"
        params = {"code_article": code_article}
        target_page = CAPABILITIES[intent]["target_page"]
        answer = f"J'ouvre l'écran photo pour l'article {code_article}."
    elif mentions_network and code_article:
        intent = "article_network"
        params = {"code_article": code_article}
        target_page = CAPABILITIES[intent]["target_page"]
        answer = f"J'ouvre le graphe de relations pour l'article {code_article}."
    elif mentions_stats_sorties and code_article:
        intent = "exit_stats"
        params = {"code_article": code_article}
        target_page = CAPABILITIES[intent]["target_page"]
        answer = f"J'ouvre les statistiques de sorties pour l'article {code_article}."
    elif mentions_helios:
        intent = "helios"
        params = {"code_article": code_article} if code_article else {}
        target_page = CAPABILITIES[intent]["target_page"]
        answer = "J'ouvre l'écran du parc Hélios."
    elif mentions_stock and (mentions_map or "localis" in lower_q):
        intent = "view_stock_map"
        target_page = CAPABILITIES[intent]["target_page"]
        if code_article:
            params["code_article"] = code_article
        addr = _extract_address(question)
        if addr:
            params["address"] = addr
        answer = "J'ouvre la carte de localisation du stock."
    elif (mentions_stock or mentions_sorties) and code_article:
        intent = "view_stock_article"
        target_page = CAPABILITIES[intent]["target_page"]
        params = {"code_article": code_article}
        answer = f"J'ouvre l'écran de stock pour l'article {code_article}."
    elif mentions_items and code_article:
        intent = "view_items"
        target_page = CAPABILITIES[intent]["target_page"]
        params = {"code_article": code_article}
        answer = f"J'ouvre le détail de l'article {code_article} dans l'onglet Items."
    elif mentions_admin_pr:
        intent = "admin_pr"
        target_page = CAPABILITIES[intent]["target_page"]
        params = {}
        answer = "J'ouvre l'écran Administration PR."
    elif mentions_assignments or (mentions_pr and ("affect" in lower_q or roles)):
        intent = "technician_assignments"
        target_page = CAPABILITIES[intent]["target_page"]
        params = {}
        if store_code:
            params["store"] = store_code
        if pr_code and ("point" in lower_q or "pr" in lower_q or "relais" in lower_q):
            params["pr"] = pr_code
        if roles:
            params["roles"] = roles
        if "ferme" in lower_q or "fermé" in lower_q or "fermée" in lower_q:
            params["status"] = "ferme"
        elif "ouvert" in lower_q:
            params["status"] = "ouvert"
        if "tout" in lower_q and ("role" in lower_q or "rôle" in lower_q):
            params["expand_store_roles"] = True
        answer = "J'ouvre l'écran des affectations points relais / techniciens."
    elif mentions_pr and not mentions_stock:
        intent = "view_nearest_pudo"
        target_page = CAPABILITIES[intent]["target_page"]
        addr = _extract_address(question)
        if addr:
            params["address"] = addr
            answer = "J'ouvre l'écran Magasins & points relais autour de l'adresse demandée."
        else:
            intent = "none"
            target_page = None
            params = {}
            answer = "J'ai besoin d'une adresse (ou d'une ville) pour chercher des points relais."
    elif mentions_technicians:
        intent = "technicians"
        target_page = CAPABILITIES[intent]["target_page"]
        params = {}
        if store_code:
            params["q"] = store_code
        answer = "J'ouvre l'écran magasin / technicien."
    elif mentions_ol:
        intent = "ol_mode_degrade"
        target_page = CAPABILITIES[intent]["target_page"]
        params = {}
        answer = "J'ouvre l'écran OL mode dégradé."

    return {
        "answer": answer,
        "intent": intent,
        "params": params,
        "target_page": target_page,
    }


@bp.get("/capabilities")
def assistant_capabilities():
    return jsonify({
        "capabilities": CAPABILITIES,
    })


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
        system_prompt += (
            "\nIMPORTANT : la spécification métier ci-dessous est la source de vérité. "
            "Si ta réponse s'appuie sur cette spécification, tu dois inclure un champ JSON `sources` (liste) "
            "avec au minimum une entrée contenant `file` et `note`. "
            "Si la question n'est pas couverte par la spécification, réponds avec intent=\"none\" et explique quoi préciser ou quoi documenter.\n"
            "Exemple attendu quand la spec est utilisée :\n"
            "{\n  \"answer\": \"...\",\n  \"intent\": \"none\",\n  \"params\": {},\n  \"target_page\": null,\n  \"sources\": [{\"file\": \"docs/spec/SPEC_METIER_SUPPLYCHAINAPP.md\", \"note\": \"section ...\"}]\n}\n"
            "\nContexte métier (extrait de la spécification) :\n\n"
            + spec_excerpt
        )

    lower_q = (question or "").lower()
    assistant_mode = os.environ.get("ASSISTANT_MODE", "rules").strip().lower()
    if assistant_mode not in ("rules", "ollama", "auto"):
        assistant_mode = "rules"

    payload = None
    used_rules_fallback = False
    if assistant_mode in ("ollama", "auto"):
        try:
            payload = _ollama_route(question=question, system_prompt=system_prompt)
        except Exception:
            payload = None

    if not payload:
        payload = _rules_route(question)
        used_rules_fallback = True

    answer = payload.get("answer") or ""
    intent = payload.get("intent") or "none"
    params = payload.get("params") or {}
    target_page = payload.get("target_page")
    sources = payload.get("sources") or []

    # Anti-hallucinations : si la spec est activée et que le LLM n'a fourni aucune source,
    # on neutralise l'action et on demande une clarification / mise à jour de la spec.
    if spec_enabled and assistant_mode in ("ollama", "auto") and not used_rules_fallback:
        if not sources:
            intent = "none"
            target_page = None
            params = {}
            answer = (
                "Je ne peux pas justifier cette action à partir de la spécification métier actuellement fournie. "
                "Peux-tu reformuler (ex: code article / écran visé) ou compléter la spécification métier ?"
            )

    if assistant_mode in ("ollama", "auto") and used_rules_fallback:
        if answer:
            answer = answer + " (mode règles)"

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
        "sources": sources,
    })


@bp.post("/rag/build")
def assistant_rag_build():
    """(Re)construit l'index Chroma pour le catalogue (tables + joins).

    Corps optionnel:
    {
      "catalog_path": "D:/.../catalog.json",
      "persist_dir": "...",
      "collection": "supplychain_catalog",
      "embedding_model": "sentence-transformers/all-MiniLM-L6-v2"
    }
    """
    if not _rag_available():
        return jsonify({"error": "rag_dependencies_missing"}), 500

    body = request.get_json(silent=True) or {}
    catalog_path = body.get("catalog_path")
    persist_dir = body.get("persist_dir")
    collection = body.get("collection") or "supplychain_catalog"
    embedding_model = body.get("embedding_model")

    rag_catalog = _load_rag_catalog_module()
    try:
        info = rag_catalog.build_or_update_index(
            catalog_path=Path(catalog_path) if catalog_path else None,
            persist_dir=Path(persist_dir) if persist_dir else None,
            collection_name=collection,
            embedding_model=embedding_model,
        )
    except Exception as e:
        return jsonify({"error": "rag_build_failed", "detail": str(e)}), 500

    return jsonify({"status": "ok", "info": info})


@bp.post("/rag/query")
def assistant_rag_query():
    """Interroge l'index Chroma et renvoie un contexte (tables/joins) pour une question."""
    if not _rag_available():
        return jsonify({"error": "rag_dependencies_missing"}), 500

    body = request.get_json(silent=True) or {}
    question = (body.get("question") or "").strip()
    if not question:
        return jsonify({"error": "question_required"}), 400

    top_k = int(body.get("top_k") or 8)
    persist_dir = body.get("persist_dir")
    collection = body.get("collection") or "supplychain_catalog"
    embedding_model = body.get("embedding_model")

    rag_catalog = _load_rag_catalog_module()
    try:
        hits = rag_catalog.query_index(
            question=question,
            top_k=top_k,
            persist_dir=Path(persist_dir) if persist_dir else None,
            collection_name=collection,
            embedding_model=embedding_model,
        )
    except Exception as e:
        return jsonify({"error": "rag_query_failed", "detail": str(e)}), 500

    return jsonify({
        "question": question,
        "top_k": top_k,
        "hits": [
            {
                "id": h.id,
                "score": h.score,
                "type": h.doc_type,
                "payload": h.payload,
                "text": h.text,
            }
            for h in hits
        ],
    })


@bp.post("/llm_rag")
def assistant_llm_rag():
    body = request.get_json(silent=True) or {}
    question = (body.get("question") or "").strip()
    if not question:
        return jsonify({"error": "question_required"}), 400

    if not _rag_available():
        return jsonify({"error": "rag_dependencies_missing"}), 500

    top_k = int(body.get("top_k") or 12)
    top_k_prompt = int(body.get("top_k_prompt") or 8)
    persist_dir = body.get("persist_dir")
    collection = body.get("collection") or "supplychain_catalog"
    embedding_model = body.get("embedding_model")
    preview_rows = int(body.get("preview_rows") or 200)
    if preview_rows < 1:
        preview_rows = 1
    if preview_rows > 2000:
        preview_rows = 2000

    rag_catalog = _load_rag_catalog_module()
    try:
        hits = rag_catalog.query_index(
            question=question,
            top_k=top_k,
            persist_dir=Path(persist_dir) if persist_dir else None,
            collection_name=collection,
            embedding_model=embedding_model,
        )
    except Exception as e:
        return jsonify({"error": "rag_query_failed", "detail": str(e)}), 500

    hits_payload = [
        {
            "id": h.id,
            "score": h.score,
            "type": h.doc_type,
            "payload": h.payload,
            "text": h.text,
        }
        for h in hits
    ]

    # Limiter le contexte envoyé au LLM (réduit les timeouts)
    hits_for_prompt = []
    for h in hits_payload[: max(0, top_k_prompt)]:
        payload = h.get("payload") if isinstance(h, dict) else None
        if not isinstance(payload, dict):
            payload = {}
        # garder seulement quelques clés importantes pour éviter des prompts énormes
        minimal_payload = {k: payload.get(k) for k in (
            "type",
            "table",
            "from_table",
            "from_column",
            "to_table",
            "to_column",
            "match_rate_sample",
            "to_is_unique_sample",
        ) if k in payload}
        hits_for_prompt.append({
            "id": h.get("id"),
            "type": h.get("type"),
            "text": h.get("text"),
            "payload": minimal_payload,
        })

    from supplychain_app.polars_assistant import _default_data_dir, build_plan_from_rag, compile_plan_to_polars_code

    data_dir = Path(body.get("data_dir")) if body.get("data_dir") else _default_data_dir()
    plan = build_plan_from_rag(question=question, rag_hits=hits_payload, preview_rows=preview_rows)
    polars_code = compile_plan_to_polars_code(plan=plan, data_dir=data_dir)

    deterministic_answer = None
    polars_code_override = None
    # Analyse stock (stock_final.parquet) pour les demandes type "besoin de X" dans un contexte projet.
    # Exemple: "dans le cadre d'un projet, besoin de 5 code article TDF159698 ?"
    if deterministic_answer is None:
        try:
            import polars as pl

            lower_q = (question or "").lower()
            asked = _extract_code_article(question)
            requested_qty = _extract_requested_qty(question)
            project_code = _extract_project_code(question)

            if asked and requested_qty and ("projet" in lower_q or project_code or " pj" in lower_q):
                stock_path = str(data_dir / "stock_final.parquet")
                lf = pl.scan_parquet(stock_path).filter(pl.col("code_article") == asked)

                schema = lf.schema
                qte_col = "qte_stock" if "qte_stock" in schema else None
                if not qte_col:
                    raise ValueError("missing_qte_stock")

                quality_col = _find_first_existing_col(schema, ("code_qualite", "code_aqualite", "qualite"))
                dm_col = _find_first_existing_col(schema, ("flag_stock_d_m",))
                project_col = _find_first_existing_col(schema, ("code_projet", "projet", "codeprojet"))
                anciennete_col = _find_first_existing_col(schema, (
                    "categorie_anciennete_stock",
                    "categorie_anciennete",
                    "categorie_anciennete_jours",
                    "categorie_anciennete_article",
                ))

                def _filter_quality(lf_in: pl.LazyFrame, quality: str):
                    vals = _quality_values(quality)
                    if not vals or not quality_col:
                        return lf_in
                    return lf_in.filter(
                        pl.col(quality_col)
                        .cast(pl.Utf8)
                        .str.strip_chars()
                        .str.to_uppercase()
                        .is_in(vals)
                    )

                def _filter_dm(lf_in: pl.LazyFrame, dm_flag: str):
                    if not dm_flag or not dm_col:
                        return lf_in
                    return lf_in.filter(
                        pl.col(dm_col)
                        .cast(pl.Utf8)
                        .str.strip_chars()
                        .str.to_uppercase()
                        == dm_flag
                    )

                def _filter_project(lf_in: pl.LazyFrame, proj: str):
                    if not proj or not project_col:
                        return lf_in
                    return lf_in.filter(
                        pl.col(project_col)
                        .cast(pl.Utf8)
                        .str.strip_chars()
                        .str.to_uppercase()
                        == proj
                    )

                def _sum_qty(lf_in: pl.LazyFrame) -> float:
                    df_sum = lf_in.select(pl.col(qte_col).sum().alias("_sum")).collect()
                    if df_sum.height == 0:
                        return 0.0
                    v = df_sum[0, "_sum"]
                    if v is None:
                        return 0.0
                    try:
                        return float(v)
                    except Exception:
                        return 0.0

                MAIN_PROJECT = "PJ00000564"

                # (1) Stock GOOD sur PJ00000564
                lf_good = _filter_quality(lf, "GOOD")
                good_main = _sum_qty(_filter_project(lf_good, MAIN_PROJECT))

                # (2) Stock GOOD sur autres PJ* (≠ PJ00000564), groupé par catégorie d'ancienneté
                other_pj_groups: list[tuple[str, float]] = []
                other_pj_total = 0.0
                if project_col:
                    lf_other_pj = lf_good.filter(
                        pl.col(project_col)
                        .cast(pl.Utf8)
                        .str.strip_chars()
                        .str.to_uppercase()
                        .str.starts_with("PJ")
                    ).filter(
                        pl.col(project_col)
                        .cast(pl.Utf8)
                        .str.strip_chars()
                        .str.to_uppercase()
                        != MAIN_PROJECT
                    )

                    if anciennete_col:
                        df_grp = (
                            lf_other_pj
                            .group_by(pl.col(anciennete_col).cast(pl.Utf8).fill_null("(inconnu)").alias("categorie"))
                            .agg(pl.col(qte_col).sum().alias("qte"))
                            .collect()
                        )
                        if df_grp.height:
                            other_pj_groups = [
                                (str(r["categorie"]), float(r["qte"] or 0))
                                for r in df_grp.to_dicts()
                            ]
                            other_pj_groups.sort(key=lambda t: _category_sort_key(t[0]), reverse=True)
                            other_pj_total = sum(q for _, q in other_pj_groups)
                    else:
                        other_pj_total = _sum_qty(lf_other_pj)

                # (3) Stock GOOD en maintenance
                good_maintenance = _sum_qty(_filter_dm(lf_good, "M"))

                # (4) Stock BAD (prioriser réparations)
                lf_bad = _filter_quality(lf, "BAD")
                bad_total = _sum_qty(lf_bad)

                # Fournir un script Polars cohérent avec cette analyse (utile côté UI "Générer Polars").
                polars_code_override = "\n".join([
                    "import polars as pl",
                    f"data_dir = r\"{str(data_dir)}\"",
                    "stock_final = pl.scan_parquet(f\"{data_dir}\\\\stock_final.parquet\")",
                    f"asked = \"{asked}\"",
                    f"MAIN_PROJECT = \"{MAIN_PROJECT}\"",
                    "lf = stock_final.filter(pl.col('code_article') == asked)",
                    "schema = lf.schema",
                    "qte_col = 'qte_stock' if 'qte_stock' in schema else None",
                    "quality_col = next((c for c in ('code_qualite','code_aqualite','qualite') if c in schema), None)",
                    "dm_col = 'flag_stock_d_m' if 'flag_stock_d_m' in schema else None",
                    "project_col = next((c for c in ('code_projet','projet','codeprojet') if c in schema), None)",
                    "anciennete_col = next((c for c in ('categorie_anciennete_stock','categorie_anciennete','categorie_anciennete_jours','categorie_anciennete_article') if c in schema), None)",
                    "",
                    "def norm_col(c):",
                    "    return pl.col(c).cast(pl.Utf8).str.strip_chars().str.to_uppercase()",
                    "",
                    "def filter_quality(lf_in, values):",
                    "    if not values or not quality_col:",
                    "        return lf_in",
                    "    return lf_in.filter(norm_col(quality_col).is_in(values))",
                    "",
                    "def sum_qty(lf_in):",
                    "    if not qte_col:",
                    "        return None",
                    "    df = lf_in.select(pl.col(qte_col).sum().alias('qte')).collect()",
                    "    return df[0,'qte'] if df.height else None",
                    "",
                    "lf_good = filter_quality(lf, ['GOOD'])",
                    "good_main = sum_qty(lf_good.filter(norm_col(project_col) == MAIN_PROJECT) if project_col else lf_good)",
                    "",
                    "other_pj = None",
                    "if project_col:",
                    "    other_pj = lf_good.filter(norm_col(project_col).str.starts_with('PJ')).filter(norm_col(project_col) != MAIN_PROJECT)",
                    "",
                    "other_pj_by_age = None",
                    "if other_pj is not None and anciennete_col:",
                    "    other_pj_by_age = (",
                    "        other_pj",
                    "        .group_by(pl.col(anciennete_col).cast(pl.Utf8).fill_null('(inconnu)').alias('categorie_anciennete_stock'))",
                    "        .agg(pl.col(qte_col).sum().alias('qte_good'))",
                    "    )",
                    "",
                    "good_maintenance = None",
                    "if dm_col:",
                    "    good_maintenance = sum_qty(lf_good.filter(norm_col(dm_col) == 'M'))",
                    "",
                    "lf_bad = filter_quality(lf, ['BAD','BLOQB'])",
                    "bad_total = sum_qty(lf_bad)",
                    "",
                    "print({'good_main_PJ00000564': good_main, 'good_maintenance': good_maintenance, 'bad_total': bad_total})",
                    "if other_pj_by_age is not None:",
                    "    print(other_pj_by_age.collect())",
                ])

                # Synthèse + proposition d'actions
                deficit = max(0.0, float(requested_qty) - float(good_main))

                lines: list[str] = []
                lines.append(f"Demande: {requested_qty} unité(s) de {asked} (contexte projet).")
                lines.append("")
                lines.append("Synthèse stock (source: stock_final.parquet) :")
                lines.append(f"1) GOOD sur projet {MAIN_PROJECT} : {int(good_main) if good_main.is_integer() else good_main}")
                if project_col:
                    if anciennete_col and other_pj_groups:
                        lines.append(f"2) GOOD sur autres projets PJ* (≠ {MAIN_PROJECT}) : {int(other_pj_total) if other_pj_total.is_integer() else other_pj_total}")
                        lines.append("   Détail par ancienneté (plus ancien prioritaire) :")
                        for cat, q in other_pj_groups[:8]:
                            q_str = int(q) if float(q).is_integer() else q
                            lines.append(f"   - {cat} : {q_str}")
                        if len(other_pj_groups) > 8:
                            lines.append(f"   - ... (+{len(other_pj_groups) - 8} catégorie(s))")
                    else:
                        lines.append(f"2) GOOD sur autres projets PJ* (≠ {MAIN_PROJECT}) : {int(other_pj_total) if other_pj_total.is_integer() else other_pj_total}")
                else:
                    lines.append("2) GOOD sur autres projets PJ*: indisponible (colonne projet absente).")
                if dm_col:
                    lines.append(f"3) GOOD en stock maintenance : {int(good_maintenance) if good_maintenance.is_integer() else good_maintenance}")
                else:
                    lines.append("3) GOOD en stock maintenance: indisponible (colonne D/M absente).")
                if quality_col:
                    lines.append(f"4) BAD (BAD+BLOQB) : {int(bad_total) if bad_total.is_integer() else bad_total}")
                else:
                    lines.append("4) BAD : indisponible (colonne qualité absente).")

                lines.append("")
                lines.append("Proposition d'actions :")
                if deficit <= 0:
                    lines.append(f"- Le stock GOOD sur {MAIN_PROJECT} couvre la demande (OK).")
                    lines.append(f"- Action: réserver/consommer {requested_qty} unité(s) sur {MAIN_PROJECT}.")
                else:
                    lines.append(f"- Il manque environ {int(deficit) if deficit.is_integer() else deficit} unité(s) en GOOD sur {MAIN_PROJECT}.")
                    if other_pj_total > 0:
                        lines.append("- Action prioritaire: transférer/affecter depuis d'autres projets PJ (en privilégiant les lots les plus anciens).")
                    if good_maintenance > 0:
                        lines.append("- Action complémentaire: basculer du stock maintenance (GOOD) si autorisé par le process.")
                    if bad_total > 0:
                        lines.append("- Action parallèle: lancer/prioriser des réparations sur ce code article (stock BAD disponible).")
                    if other_pj_total <= 0 and good_maintenance <= 0 and bad_total <= 0:
                        lines.append("- Aucun levier évident détecté (autres PJ/maintenance/BAD). Vérifier l'article, les filtres ou l'alimentation du stock_final.")

                deterministic_answer = "\n".join(lines)
        except Exception:
            deterministic_answer = None

    if plan.intent == "equivalent_article":
        try:
            from supplychain_app.polars_assistant import compile_plan_to_lazyframe

            lf = compile_plan_to_lazyframe(plan=plan, data_dir=data_dir)
            df = lf.limit(preview_rows).collect()
            rows = df.to_dicts()

            codes = []
            for r in rows or []:
                v = r.get("code_article_correspondant")
                if isinstance(v, str) and v and v not in codes:
                    codes.append(v)

            asked = _extract_code_article(question) or ""
            if codes:
                deterministic_answer = (
                    f"Substitution(s) trouvée(s) pour {asked}: "
                    + ", ".join(codes)
                    + "."
                )
            else:
                deterministic_answer = f"Aucune substitution trouvée pour {asked}."
        except Exception:
            deterministic_answer = None

    # Stock global (tous les articles) : somme(qte_stock) sur stock_554, avec filtres qualité / D/M.
    if deterministic_answer is None and plan.intent in ("stock_by_store", "stock_article"):
        try:
            import polars as pl

            asked = _extract_code_article(question)
            if asked:
                raise ValueError("not_global_stock")
            if not _wants_global_stock(question):
                raise ValueError("not_all_articles")

            quality = _extract_quality(question)
            stock_dm_flag = _extract_stock_dm_flag(question)

            stock_path = str(data_dir / "stock_554.parquet")
            lf = pl.scan_parquet(stock_path)

            quality_col = None
            quality_vals = _quality_values(quality)
            if quality_vals:
                schema = lf.schema
                for c in ("code_qualite", "code_aqualite", "qualite"):
                    if c in schema:
                        quality_col = c
                        break
                if quality_col:
                    lf = lf.filter(
                        pl.col(quality_col)
                        .cast(pl.Utf8)
                        .str.strip_chars()
                        .str.to_uppercase()
                        .is_in(quality_vals)
                    )

            dm_col = None
            if stock_dm_flag:
                schema = lf.schema
                for c in ("flag_stock_d_m"):
                    if c in schema:
                        dm_col = c
                        break
                if dm_col:
                    lf = lf.filter(
                        pl.col(dm_col)
                        .cast(pl.Utf8)
                        .str.strip_chars()
                        .str.to_uppercase()
                        == stock_dm_flag
                    )

            total_df = lf.select(pl.col("qte_stock").sum().alias("qte_stock_total")).collect()
            total = total_df[0, "qte_stock_total"] if total_df.height else None
            n_df = lf.select(pl.len().alias("n_rows")).collect()
            n_rows = int(n_df[0, "n_rows"]) if n_df.height else 0

            if total is None:
                deterministic_answer = "Quantité de stock indisponible (colonne qte_stock manquante)."
            else:
                try:
                    total_val = int(total)
                except Exception:
                    total_val = float(total)

                suffix_parts = []
                if quality_vals:
                    suffix_parts.append(f"qualité {'/'.join(quality_vals)}")
                if stock_dm_flag == "D":
                    suffix_parts.append("déploiement")
                elif stock_dm_flag == "M":
                    suffix_parts.append("maintenance")
                suffix = (" (" + ", ".join(suffix_parts) + ")") if suffix_parts else ""
                if quality_vals and not quality_col:
                    suffix += " [filtre qualité demandé mais colonne absente]"
                if stock_dm_flag and not dm_col:
                    suffix += " [filtre déploiement/maintenance demandé mais colonne absente]"

                deterministic_answer = f"Quantité totale de stock{suffix}: {total_val} (somme de qte_stock sur {n_rows} ligne(s))."
        except Exception:
            deterministic_answer = None

    if deterministic_answer is None and plan.intent == "stock_article":
        try:
            import polars as pl

            asked = _extract_code_article(question) or ""

            quality = _extract_quality(question)
            stock_dm_flag = _extract_stock_dm_flag(question)
            # Calculer directement depuis stock_554.parquet : c'est la table source du stock
            # et elle contient les colonnes qte_stock / code_qualite (plus fiable que le LF final).
            stock_path = str(data_dir / "stock_554.parquet")
            lf = pl.scan_parquet(stock_path).filter(pl.col("code_article") == asked)

            quality_col = None
            quality_vals = _quality_values(quality)
            if quality_vals:
                schema = lf.schema
                for c in ("code_qualite", "qualite"):
                    if c in schema:
                        quality_col = c
                        break
                if quality_col:
                    lf = lf.filter(
                        pl.col(quality_col)
                        .cast(pl.Utf8)
                        .str.strip_chars()
                        .str.to_uppercase()
                        .is_in(quality_vals)
                    )

            deploy_col = None
            if stock_dm_flag:
                schema = lf.schema
                for c in ("flag_stock_d_m"):
                    if c in schema:
                        deploy_col = c
                        break
                if deploy_col:
                    lf = lf.filter(
                        pl.col(deploy_col)
                        .cast(pl.Utf8)
                        .str.strip_chars()
                        .str.to_uppercase()
                        == stock_dm_flag
                    )

            # Calcul exact : pas de limit() ici.
            total_df = lf.select(pl.col("qte_stock").sum().alias("qte_stock_total")).collect()
            total = total_df[0, "qte_stock_total"] if total_df.height else None

            # Petit contexte utile : nb de lignes contributing
            n_df = lf.select(pl.len().alias("n_rows")).collect()
            n_rows = int(n_df[0, "n_rows"]) if n_df.height else 0

            if total is None:
                deterministic_answer = f"Stock total indisponible pour {asked} (colonne qte_stock manquante)."
            else:
                try:
                    total_val = int(total)
                except Exception:
                    total_val = float(total)
                suffix_parts = []
                if quality_vals:
                    suffix_parts.append(f"qualité {'/'.join(quality_vals)}")
                if stock_dm_flag == "D":
                    suffix_parts.append("déploiement")
                elif stock_dm_flag == "M":
                    suffix_parts.append("maintenance")
                suffix = (" (" + ", ".join(suffix_parts) + ")") if suffix_parts else ""
                if quality_vals and not quality_col:
                    suffix += " [filtre qualité demandé mais colonne absente]"
                if stock_dm_flag and not deploy_col:
                    suffix += " [filtre déploiement/maintenance demandé mais colonne absente]"
                deterministic_answer = f"Stock total pour {asked}{suffix}: {total_val} (somme de qte_stock sur {n_rows} ligne(s))."
        except Exception:
            deterministic_answer = None

    ollama_model = body.get("ollama_model")
    ollama_timeout_s = body.get("ollama_timeout_s")
    try:
        ollama_timeout_s = float(ollama_timeout_s) if ollama_timeout_s is not None else None
    except Exception:
        ollama_timeout_s = None

    system_prompt = (
        "Tu es un assistant data pour SupplyChainApp. "
        "Tu dois répondre en français. "
        "Tu peux t'appuyer sur le contexte RAG (tables et jointures) fourni ci-dessous. "
        "Tu peux proposer une stratégie de jointure et expliquer quelles tables utiliser. "
        "Si du code Polars est fourni, tu peux l'expliquer ou proposer des ajustements. "
        "Ne révèle pas d'informations sensibles."
        "\n\nCONTEXTE RAG (JSON):\n"
        + json.dumps(hits_for_prompt, ensure_ascii=False)[:6000]
        + "\n\nCODE POLARS (proposition):\n"
        + polars_code[:6000]
    )

    llm_error = None
    answer = ""
    if deterministic_answer is None:
        try:
            answer = _ollama_text(
                question=question,
                system_prompt=system_prompt,
                model=ollama_model,
                timeout_s=ollama_timeout_s,
            )
        except Exception as e:
            llm_error = str(e)
    else:
        answer = deterministic_answer

    if not answer:
        hint = _ollama_status_hint()
        degraded = (
            "LLM indisponible : je retourne une réponse dégradée basée sur le RAG (tables/jointures) "
            "et une proposition de code Polars.\n\n"
            f"Diagnostic: {hint}\n"
        )
        if llm_error:
            degraded += f"Détail: {llm_error}\n"
        degraded += "\nTu peux quand même utiliser 'Générer Polars' et 'Exécuter preview'."
        answer = degraded

    return jsonify({
        "question": question,
        "answer": answer,
        "llm": {
            "available": llm_error is None,
            "error": llm_error,
            "url": os.environ.get("ASSISTANT_OLLAMA_URL", "http://127.0.0.1:11434"),
            "model": (ollama_model or os.environ.get("ASSISTANT_OLLAMA_MODEL", "llama3.1")),
            "timeout_s": (ollama_timeout_s if ollama_timeout_s is not None else float(os.environ.get("ASSISTANT_OLLAMA_TIMEOUT_S", "60"))),
        },
        "rag": {
            "top_k": top_k,
            "collection": collection,
            "embedding_model": embedding_model or "hash",
            "hits": hits_payload,
        },
        "data_dir": str(data_dir),
        "plan": {
            "intent": plan.intent,
            "tables": plan.tables,
            "joins": plan.joins,
            "filters": plan.filters,
            "selected_columns": plan.selected_columns,
            "preview_rows": plan.preview_rows,
        },
        "polars_code": polars_code_override or polars_code,
    })


@bp.post("/polars/generate")
def assistant_polars_generate():
    """Génère un plan et du code Polars (sans exécuter) à partir d'une question."""
    body = request.get_json(silent=True) or {}
    question = (body.get("question") or "").strip()
    if not question:
        return jsonify({"error": "question_required"}), 400

    preview_rows = int(body.get("preview_rows") or 200)
    if preview_rows < 1:
        preview_rows = 1
    if preview_rows > 2000:
        preview_rows = 2000

    if not _rag_available():
        return jsonify({"error": "rag_dependencies_missing"}), 500

    top_k = int(body.get("top_k") or 12)
    persist_dir = body.get("persist_dir")
    collection = body.get("collection") or "supplychain_catalog"
    embedding_model = body.get("embedding_model")

    rag_catalog = _load_rag_catalog_module()
    try:
        hits = rag_catalog.query_index(
            question=question,
            top_k=top_k,
            persist_dir=Path(persist_dir) if persist_dir else None,
            collection_name=collection,
            embedding_model=embedding_model,
        )
    except Exception as e:
        return jsonify({"error": "rag_query_failed", "detail": str(e)}), 500

    hits_payload = [
        {
            "id": h.id,
            "score": h.score,
            "type": h.doc_type,
            "payload": h.payload,
            "text": h.text,
        }
        for h in hits
    ]

    from supplychain_app.polars_assistant import _default_data_dir, build_plan_from_rag, compile_plan_to_polars_code

    data_dir = Path(body.get("data_dir")) if body.get("data_dir") else _default_data_dir()
    plan = build_plan_from_rag(question=question, rag_hits=hits_payload, preview_rows=preview_rows)
    code = compile_plan_to_polars_code(plan=plan, data_dir=data_dir)

    return jsonify({
        "question": question,
        "data_dir": str(data_dir),
        "rag": {
            "top_k": top_k,
            "collection": collection,
            "embedding_model": embedding_model or "hash",
            "hits": hits_payload,
        },
        "plan": {
            "intent": plan.intent,
            "tables": plan.tables,
            "joins": plan.joins,
            "filters": plan.filters,
            "selected_columns": plan.selected_columns,
            "preview_rows": plan.preview_rows,
        },
        "polars_code": code,
    })


@bp.post("/polars/execute")
def assistant_polars_execute():
    """Exécute un plan Polars en backend et renvoie un preview JSON (sécurisé, sans eval)."""
    body = request.get_json(silent=True) or {}
    plan_obj = body.get("plan")
    if not isinstance(plan_obj, dict):
        return jsonify({"error": "plan_required"}), 400

    from supplychain_app.polars_assistant import PolarsPlan, _default_data_dir, compile_plan_to_lazyframe

    preview_rows = int(plan_obj.get("preview_rows") or body.get("preview_rows") or 200)
    if preview_rows < 1:
        preview_rows = 1
    if preview_rows > 2000:
        preview_rows = 2000

    data_dir = Path(body.get("data_dir")) if body.get("data_dir") else _default_data_dir()

    plan = PolarsPlan(
        intent=str(plan_obj.get("intent") or "unknown"),
        tables=list(plan_obj.get("tables") or []),
        joins=list(plan_obj.get("joins") or []),
        filters=list(plan_obj.get("filters") or []),
        selected_columns=list(plan_obj.get("selected_columns") or []),
        preview_rows=preview_rows,
    )

    try:
        lf = compile_plan_to_lazyframe(plan=plan, data_dir=data_dir)
        df = lf.limit(preview_rows).collect()
    except Exception as e:
        return jsonify({"error": "polars_execute_failed", "detail": str(e)}), 500

    return jsonify({
        "data_dir": str(data_dir),
        "preview_rows": preview_rows,
        "columns": df.columns,
        "rows": df.to_dicts(),
    })
