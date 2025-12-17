import json
import os
import re
import hashlib
import importlib
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class RagHit:
    id: str
    score: float
    doc_type: str
    payload: dict[str, Any]
    text: str


class _HashEmbeddingFunction:
    def __init__(self, dim: int = 384):
        self._dim = int(dim)

    def name(self) -> str:
        return f"local-hash-{self._dim}"

    def __call__(self, input: list[str]) -> list[list[float]]:
        vectors: list[list[float]] = []
        for text in input:
            if isinstance(text, (list, tuple)):
                text = " ".join(str(x) for x in text)
            elif not isinstance(text, str):
                text = str(text)

            v = [0.0] * self._dim
            tokens = [t for t in re.split(r"[^a-zA-Z0-9_]+", (text or "").lower()) if t]
            if not tokens:
                vectors.append(v)
                continue

            for tok in tokens:
                h = hashlib.md5(tok.encode("utf-8"), usedforsecurity=False).digest()
                idx = int.from_bytes(h[:4], "little") % self._dim
                sign = -1.0 if (h[4] % 2) else 1.0
                v[idx] += sign

            # L2 normalisation
            norm = sum(x * x for x in v) ** 0.5
            if norm > 0:
                v = [x / norm for x in v]
            vectors.append(v)

        return vectors

    def embed_documents(self, texts: list[str] | None = None, input: list[str] | None = None, **_: Any) -> list[list[float]]:
        batch = input if input is not None else (texts or [])
        return self(batch)

    def embed_query(self, text: str | None = None, input: Any = None, **_: Any) -> list[list[float]]:
        q = input if input is not None else (text or "")
        if isinstance(q, (list, tuple)):
            q = " ".join(str(x) for x in q)
        elif not isinstance(q, str):
            q = str(q)
        return self([q])


class _SentenceTransformerEmbeddingFunction:
    def __init__(self, model_name: str):
        SentenceTransformer = importlib.import_module("sentence_transformers").SentenceTransformer

        self._model = SentenceTransformer(model_name)
        self._model_name = model_name

    def name(self) -> str:
        return f"sentence-transformers::{self._model_name}"

    def __call__(self, input: list[str]) -> list[list[float]]:
        vectors = self._model.encode(input, normalize_embeddings=True)
        return vectors.tolist()

    def embed_documents(self, texts: list[str] | None = None, input: list[str] | None = None, **_: Any) -> list[list[float]]:
        batch = input if input is not None else (texts or [])
        return self(batch)

    def embed_query(self, text: str | None = None, input: Any = None, **_: Any) -> list[float]:
        q = input if input is not None else (text or "")
        if isinstance(q, (list, tuple)):
            q = " ".join(str(x) for x in q)
        elif not isinstance(q, str):
            q = str(q)
        return self([q])[0]


def _make_embedding_function(embedding_model: str):
    if not embedding_model:
        return _HashEmbeddingFunction()

    if embedding_model.strip().lower() in ("hash", "local-hash", "offline"):
        return _HashEmbeddingFunction()

    # SentenceTransformers (may require a local cache or internet)
    return _SentenceTransformerEmbeddingFunction(embedding_model)


def _default_catalog_path() -> Path:
    env = os.getenv("CATALOG_PATH")
    if env:
        return Path(env)

    data_dir = os.getenv("DATA_DIR")
    if data_dir:
        p = Path(data_dir) / "catalog.json"
        if p.exists():
            return p

    try:
        from supplychain_app.constants import folder_name_app, path_datan

        p = Path(path_datan) / folder_name_app / "catalog.json"
        if p.exists():
            return p
    except Exception:
        pass

    return Path.cwd() / "catalog.json"


def _default_persist_dir() -> Path:
    env = os.getenv("RAG_CHROMA_DIR")
    if env:
        return Path(env)

    try:
        from supplychain_app.core.paths import get_project_root_dir

        return get_project_root_dir() / "databases" / "chroma_catalog"
    except Exception:
        return Path.cwd() / "databases" / "chroma_catalog"


def _load_catalog(catalog_path: Path) -> dict[str, Any]:
    with catalog_path.open("r", encoding="utf-8") as f:
        return json.load(f)


def _sanitize_metadata(md: dict[str, Any]) -> dict[str, Any]:
    """Chroma attend des metadatas scalaires et, selon les versions, refuse les None."""
    out: dict[str, Any] = {}
    for k, v in (md or {}).items():
        if v is None:
            continue
        out[k] = v
    return out


def _table_doc(table: dict[str, Any]) -> tuple[str, str, dict[str, Any]]:
    name = table.get("name") or "unknown"
    cols = table.get("columns") or []
    col_names = [c.get("name") for c in cols if isinstance(c, dict) and c.get("name")]
    key_candidates = table.get("key_candidates") or []
    row_count = table.get("row_count")
    text = (
        f"TABLE {name}\n"
        f"row_count={row_count}\n"
        f"key_candidates={key_candidates}\n"
        f"columns={col_names}"
    )
    payload = _sanitize_metadata({
        "type": "table",
        "table": name,
        "row_count": row_count,
        "path": table.get("path"),
        "key_candidates_json": json.dumps(key_candidates, ensure_ascii=False),
        "columns_json": json.dumps(cols, ensure_ascii=False),
        "column_names_json": json.dumps(col_names, ensure_ascii=False),
    })
    doc_id = f"table::{name}"
    return doc_id, text, payload


def _join_doc(rel: dict[str, Any]) -> tuple[str, str, dict[str, Any]]:
    ft = rel.get("from_table")
    fc = rel.get("from_column")
    tt = rel.get("to_table")
    tc = rel.get("to_column")
    mr = rel.get("match_rate_sample")
    tiu = rel.get("to_is_unique_sample")
    text = (
        f"JOIN {ft}.{fc} -> {tt}.{tc}\n"
        f"match_rate_sample={mr}\n"
        f"to_is_unique_sample={tiu}"
    )
    payload = _sanitize_metadata({"type": "join", **(rel or {})})
    doc_id = f"join::{ft}.{fc}->{tt}.{tc}"
    return doc_id, text, payload


def build_or_update_index(
    catalog_path: Path | None = None,
    persist_dir: Path | None = None,
    collection_name: str = "supplychain_catalog",
    embedding_model: str | None = None,
) -> dict[str, Any]:
    catalog_path = catalog_path or _default_catalog_path()
    persist_dir = persist_dir or _default_persist_dir()
    embedding_model = embedding_model or os.getenv("RAG_EMBEDDING_MODEL", "hash")

    catalog = _load_catalog(catalog_path)

    persist_dir.mkdir(parents=True, exist_ok=True)
    chromadb = importlib.import_module("chromadb")
    Settings = importlib.import_module("chromadb.config").Settings
    client = chromadb.PersistentClient(
        path=str(persist_dir),
        settings=Settings(anonymized_telemetry=False),
    )

    embedder = _make_embedding_function(embedding_model)

    try:
        client.delete_collection(name=collection_name)
    except Exception:
        pass

    col = client.get_or_create_collection(name=collection_name, embedding_function=embedder)

    ids: list[str] = []
    documents: list[str] = []
    metadatas: list[dict[str, Any]] = []

    for t in catalog.get("tables") or []:
        doc_id, text, payload = _table_doc(t)
        ids.append(doc_id)
        documents.append(text)
        metadatas.append(payload)

    for r in catalog.get("relationships") or []:
        doc_id, text, payload = _join_doc(r)
        ids.append(doc_id)
        documents.append(text)
        metadatas.append(payload)

    if ids:
        col.add(ids=ids, documents=documents, metadatas=metadatas)

    return {
        "catalog_path": str(catalog_path),
        "persist_dir": str(persist_dir),
        "collection": collection_name,
        "embedding_model": embedding_model,
        "documents_indexed": len(ids),
        "tables": len(catalog.get("tables") or []),
        "relationships": len(catalog.get("relationships") or []),
    }


def query_index(
    question: str,
    top_k: int = 8,
    persist_dir: Path | None = None,
    collection_name: str = "supplychain_catalog",
    embedding_model: str | None = None,
) -> list[RagHit]:
    if not question:
        return []

    persist_dir = persist_dir or _default_persist_dir()
    embedding_model = embedding_model or os.getenv("RAG_EMBEDDING_MODEL", "hash")

    chromadb = importlib.import_module("chromadb")
    Settings = importlib.import_module("chromadb.config").Settings
    client = chromadb.PersistentClient(
        path=str(persist_dir),
        settings=Settings(anonymized_telemetry=False),
    )
    embedder = _make_embedding_function(embedding_model)

    col = client.get_or_create_collection(name=collection_name, embedding_function=embedder)

    # Certaines versions de Chroma utilisent embed_query() avec des signatures variables.
    # Pour rester robuste, on calcule nous-mêmes le vecteur de la question via __call__
    # et on interroge l'index avec query_embeddings.
    query_embeddings = embedder([question])

    res = col.query(query_embeddings=query_embeddings, n_results=int(top_k))

    ids = (res.get("ids") or [[]])[0]
    docs = (res.get("documents") or [[]])[0]
    metas = (res.get("metadatas") or [[]])[0]
    dists = (res.get("distances") or [[]])[0]

    hits: list[RagHit] = []
    for i, doc_id in enumerate(ids):
        md = metas[i] if i < len(metas) else {}
        doc_type = (md.get("type") or "unknown") if isinstance(md, dict) else "unknown"
        dist = dists[i] if i < len(dists) else None
        score = 1.0 - float(dist) if dist is not None else 0.0
        text = docs[i] if i < len(docs) else ""
        payload = md if isinstance(md, dict) else {}
        hits.append(RagHit(id=str(doc_id), score=score, doc_type=doc_type, payload=payload, text=text))

    hits.sort(key=lambda h: h.score, reverse=True)
    return hits
