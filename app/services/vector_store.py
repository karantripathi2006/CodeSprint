"""
Vector Store Service
====================
Wrapper around ChromaDB for storing and querying embeddings.
Falls back to in-memory storage when persistent directory is not available.
"""

import logging
from typing import List, Dict, Optional, Any

logger = logging.getLogger(__name__)

# Lazy-loaded ChromaDB client
_chroma_client = None


class VectorStoreService:
    """
    ChromaDB wrapper for storing skill, job, and candidate embeddings.
    
    Collections:
    - skill_embeddings: Skill vectors for similarity search
    - job_embeddings: Job description vectors
    - candidate_embeddings: Candidate profile vectors
    """

    def __init__(self, persist_dir: str = "./chroma_data"):
        """Initialize ChromaDB client."""
        self.persist_dir = persist_dir
        self._client = None
        self._collections: Dict[str, Any] = {}

    def _get_client(self):
        """Get or create ChromaDB client."""
        global _chroma_client
        if _chroma_client is not None:
            self._client = _chroma_client
            return self._client

        try:
            import chromadb
            from chromadb.config import Settings

            self._client = chromadb.Client(Settings(
                chroma_db_impl="duckdb+parquet",
                persist_directory=self.persist_dir,
                anonymized_telemetry=False,
            ))
            _chroma_client = self._client
            logger.info(f"ChromaDB initialized with persist dir: {self.persist_dir}")
        except Exception as e:
            logger.warning(f"ChromaDB persistent storage failed ({e}), using in-memory")
            try:
                import chromadb
                self._client = chromadb.Client()
                _chroma_client = self._client
                logger.info("ChromaDB initialized in-memory mode")
            except Exception as e2:
                logger.error(f"ChromaDB completely unavailable: {e2}")
                self._client = None

        return self._client

    def get_collection(self, name: str):
        """Get or create a ChromaDB collection."""
        if name in self._collections:
            return self._collections[name]

        client = self._get_client()
        if client is None:
            return None

        try:
            collection = client.get_or_create_collection(
                name=name,
                metadata={"hnsw:space": "cosine"},
            )
            self._collections[name] = collection
            return collection
        except Exception as e:
            logger.error(f"Failed to get/create collection {name}: {e}")
            return None

    def add_embeddings(self, collection_name: str, ids: List[str],
                       documents: List[str], metadatas: List[Dict] = None,
                       embeddings: List[List[float]] = None):
        """
        Add documents and their embeddings to a collection.
        If embeddings aren't provided, ChromaDB will generate them.
        """
        collection = self.get_collection(collection_name)
        if collection is None:
            logger.warning(f"Cannot add to {collection_name}: collection unavailable")
            return False

        try:
            kwargs = {"ids": ids, "documents": documents}
            if metadatas:
                kwargs["metadatas"] = metadatas
            if embeddings:
                kwargs["embeddings"] = embeddings

            collection.add(**kwargs)
            logger.info(f"Added {len(ids)} items to {collection_name}")
            return True
        except Exception as e:
            logger.error(f"Failed to add embeddings to {collection_name}: {e}")
            return False

    def search_similar(self, collection_name: str, query_text: str,
                       n_results: int = 5) -> List[Dict]:
        """Search for similar documents in a collection."""
        collection = self.get_collection(collection_name)
        if collection is None:
            return []

        try:
            results = collection.query(
                query_texts=[query_text],
                n_results=n_results,
            )
            # Format results
            formatted = []
            if results and results.get("ids"):
                for i, doc_id in enumerate(results["ids"][0]):
                    item = {"id": doc_id}
                    if results.get("documents"):
                        item["document"] = results["documents"][0][i]
                    if results.get("distances"):
                        item["distance"] = results["distances"][0][i]
                    if results.get("metadatas"):
                        item["metadata"] = results["metadatas"][0][i]
                    formatted.append(item)
            return formatted
        except Exception as e:
            logger.error(f"Search failed in {collection_name}: {e}")
            return []

    def delete(self, collection_name: str, ids: List[str]):
        """Delete documents from a collection by IDs."""
        collection = self.get_collection(collection_name)
        if collection is None:
            return False

        try:
            collection.delete(ids=ids)
            return True
        except Exception as e:
            logger.error(f"Delete failed in {collection_name}: {e}")
            return False
