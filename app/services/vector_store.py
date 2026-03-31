"""
LangChain Vector Store Service
================================
Stores candidate profiles in ChromaDB via LangChain for semantic search.
Falls back to a simple hash-based embedding when sentence-transformers is unavailable.
"""

import logging
import hashlib
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)

# ── Fallback embedding when sentence-transformers is not installed ────────────

class _HashEmbeddings:
    """
    Deterministic 384-dim embeddings from character n-gram hashing.
    Used as fallback when sentence-transformers is unavailable.
    Results are consistent but not semantically meaningful.
    """
    DIM = 384

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        return [self._embed(t) for t in texts]

    def embed_query(self, text: str) -> List[float]:
        return self._embed(text)

    def _embed(self, text: str) -> List[float]:
        words = text.lower().split()
        vec = [0.0] * self.DIM
        for i, word in enumerate(words):
            h = int(hashlib.md5(word.encode()).hexdigest(), 16)
            vec[h % self.DIM] += 1.0 / (i + 1)
        mag = sum(x * x for x in vec) ** 0.5
        return [x / (mag or 1.0) for x in vec]


def _get_embeddings():
    """Return sentence-transformer embeddings or hash fallback."""
    try:
        from langchain_community.embeddings import HuggingFaceEmbeddings
        from app.core.config import get_settings
        settings = get_settings()
        emb = HuggingFaceEmbeddings(model_name=settings.EMBEDDING_MODEL)
        logger.info(f"Using HuggingFace embeddings: {settings.EMBEDDING_MODEL}")
        return emb
    except Exception as e:
        logger.warning(f"HuggingFace embeddings unavailable ({e}), using hash fallback")
        return _HashEmbeddings()


# ── Singleton store ───────────────────────────────────────────────────────────

_store_instance = None


def _get_store():
    """Lazy-init the LangChain Chroma vector store (singleton)."""
    global _store_instance
    if _store_instance is not None:
        return _store_instance

    try:
        from langchain_chroma import Chroma
        from app.core.config import get_settings
        settings = get_settings()

        embeddings = _get_embeddings()
        _store_instance = Chroma(
            collection_name="candidates",
            embedding_function=embeddings,
            persist_directory=settings.CHROMA_PERSIST_DIR,
        )
        logger.info(f"ChromaDB initialised at {settings.CHROMA_PERSIST_DIR}")
    except Exception as e:
        logger.warning(f"ChromaDB persistent store unavailable ({e}), trying in-memory")
        try:
            from langchain_chroma import Chroma
            _store_instance = Chroma(
                collection_name="candidates",
                embedding_function=_get_embeddings(),
            )
            logger.info("ChromaDB running in-memory")
        except Exception as e2:
            logger.error(f"Could not initialise any vector store: {e2}")
            _store_instance = None

    return _store_instance


# ── Helpers ───────────────────────────────────────────────────────────────────

def _build_profile_text(parsed_data: Dict, normalized_skills: Dict) -> str:
    """Build a rich text blob of the candidate for embedding."""
    parts = []

    name = parsed_data.get("name", "")
    if name:
        parts.append(f"Name: {name}")

    summary = parsed_data.get("summary", "")
    if summary:
        parts.append(f"Summary: {summary}")

    all_skills = (normalized_skills or {}).get("all_skills") or parsed_data.get("skills", [])
    if all_skills:
        parts.append(f"Skills: {', '.join(all_skills)}")

    for exp in parsed_data.get("experience", [])[:3]:
        role = exp.get("role", "")
        company = exp.get("company", "")
        if role or company:
            parts.append(f"Role: {role} at {company}".strip())
        for resp in exp.get("responsibilities", [])[:2]:
            parts.append(resp)

    for edu in parsed_data.get("education", [])[:2]:
        degree = edu.get("degree", "")
        institution = edu.get("institution", "")
        if degree:
            parts.append(f"Education: {degree} {institution}".strip())

    return "\n".join(parts) if parts else (name or "Unknown candidate")


# ── Public API ────────────────────────────────────────────────────────────────

def index_candidate(
    candidate_id: int,
    parsed_data: Dict[str, Any],
    normalized_skills: Optional[Dict[str, Any]] = None,
) -> bool:
    """
    Index a candidate's full profile into the vector store.
    Uses candidate_{id} as the document ID so re-indexing is idempotent (upsert).

    Returns True on success, False if vector store is unavailable.
    """
    store = _get_store()
    if store is None:
        return False

    try:
        from langchain_core.documents import Document

        text = _build_profile_text(parsed_data, normalized_skills or {})
        all_skills = (normalized_skills or {}).get("all_skills") or parsed_data.get("skills", [])

        doc = Document(
            page_content=text,
            metadata={
                "candidate_id": candidate_id,
                "name": parsed_data.get("name", ""),
                "email": parsed_data.get("email", ""),
                # Chroma metadata values must be scalar — join skills as string
                "skills": ", ".join(all_skills[:20]),
            },
        )
        doc_id = f"candidate_{candidate_id}"

        # Delete stale version before re-inserting
        try:
            store.delete(ids=[doc_id])
        except Exception:
            pass

        store.add_documents([doc], ids=[doc_id])
        logger.info(f"Indexed candidate {candidate_id} ({parsed_data.get('name', '?')}) into vector store")
        return True

    except Exception as e:
        logger.error(f"Failed to index candidate {candidate_id}: {e}")
        return False


def search_candidates(query: str, k: int = 5) -> List[Dict[str, Any]]:
    """
    Semantic similarity search over indexed candidates.

    Returns list of dicts: candidate_id, name, email, skills, score, content
    """
    store = _get_store()
    if store is None:
        return []

    try:
        results = store.similarity_search_with_relevance_scores(query, k=k)
        out = []
        for doc, score in results:
            out.append({
                "candidate_id": doc.metadata.get("candidate_id"),
                "name": doc.metadata.get("name", ""),
                "email": doc.metadata.get("email", ""),
                "skills": doc.metadata.get("skills", ""),
                "score": round(float(score), 3),
                "content": doc.page_content,
            })
        return out
    except Exception as e:
        logger.error(f"Vector search failed: {e}")
        return []


def delete_candidate(candidate_id: int) -> bool:
    """Remove a candidate's document from the vector store."""
    store = _get_store()
    if store is None:
        return False
    try:
        store.delete(ids=[f"candidate_{candidate_id}"])
        logger.info(f"Removed candidate {candidate_id} from vector store")
        return True
    except Exception as e:
        logger.error(f"Failed to delete candidate {candidate_id} from vector store: {e}")
        return False


# ── Legacy shim — keeps old imports working ───────────────────────────────────

class VectorStoreService:
    """Backward-compat wrapper. New code should use module-level functions."""

    def add_candidate(self, candidate_id: int, parsed_data: dict, normalized_skills: dict = None):
        return index_candidate(candidate_id, parsed_data, normalized_skills)

    def search(self, query: str, k: int = 5):
        return search_candidates(query, k)

    def remove_candidate(self, candidate_id: int):
        return delete_candidate(candidate_id)
