"""Vector store abstraction built on Chroma (or FAISS fallback).

The module provides a singleton‑like ``VectorStore`` class that:
* Loads/creates a persistent Chroma collection.
* Holds the embedding model (SentenceTransformer) used for both ingestion and query.
* Exposes ``embed_documents`` and ``similarity_search`` helpers.

The RAG pipeline (`loader.py` and `queries.py`) interacts with this wrapper.
"""

import os
from pathlib import Path
from typing import List

import chromadb
from chromadb.config import Settings as ChromaSettings

from sentence_transformers import SentenceTransformer

from app.config.settings import Settings as AppSettings

# Global singleton – instantiated lazily on first use
_vectorstore_instance = None


def get_vectorstore():
    """Return the global :class:`VectorStore` instance, creating it if needed.

    The function is deliberately side‑effect free apart from the first call, which
    reads environment variables via ``AppSettings``.
    """
    global _vectorstore_instance
    if _vectorstore_instance is None:
        _vectorstore_instance = VectorStore()
    return _vectorstore_instance


class VectorStore:
    """Encapsulates a persistent Chroma collection and an embedding model.

    * ``initialize`` – creates the collection if it does not exist.
    * ``get_or_create_collection`` – low‑level accessor used by the loader.
    * ``embed_documents`` – returns numpy embeddings for a list of strings.
    * ``similarity_search`` – returns top‑k documents (content + metadata).
    """

    def __init__(self) -> None:
        self.app_settings = AppSettings()
        self._client = None
        self._collection = None
        # Use a lightweight, CPU‑friendly model.
        self._embedder = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")

    # ---------------------------------------------------------------------
    # Internal client/collection handling
    # ---------------------------------------------------------------------
    def _ensure_client(self) -> chromadb.ClientAPI:
        if self._client is None:
            # ``persist_directory`` is where Chroma stores the SQLite files.
            self._client = chromadb.PersistentClient(
                path=self.app_settings.chroma_db_path,
                settings=ChromaSettings(anonymized_telemetry=False),
            )
        return self._client

    def get_or_create_collection(self):
        """Return the Chroma collection named ``clinic_knowledge``.

        If the collection does not exist, it is created empty; the loader will
        later add documents.
        """
        if self._collection is not None:
            return self._collection
        client = self._ensure_client()
        self._collection = client.get_or_create_collection(name="clinic_knowledge")
        return self._collection

    # ---------------------------------------------------------------------
    # Public API used by the rest of the codebase
    # ---------------------------------------------------------------------
    def initialize(self) -> None:
        """Ensure the persistent collection exists – safe to call multiple times.
        """
        self.get_or_create_collection()

    def embed_documents(self, texts: List[str]):
        """Return a list of embeddings for ``texts`` using the SentenceTransformer.
        """
        return self._embedder.encode(texts).tolist()

    def similarity_search(self, query: str, k: int = 4):
        """Return the top‑``k`` most similar chunks for ``query``.

        The result is a list of dicts with keys ``document`` (raw text) and
        ``metadata``.  ``chromadb`` returns embeddings internally, we only forward
        the stored ``documents`` and ``metadatas``.
        """
        collection = self.get_or_create_collection()
        # Embed the query and ask Chroma for nearest neighbours.
        query_emb = self._embedder.encode([query]).tolist()[0]
        results = collection.query(
            query_embeddings=[query_emb],
            n_results=k,
            include=["documents", "metadatas", "distances"],
        )
        # ``results`` is a dict with list values (one entry per query).
        docs = results.get("documents", [[]])[0]
        metas = results.get("metadatas", [[]])[0]
        distances = results.get("distances", [[]])[0]
        return [
            {"document": doc, "metadata": meta, "distance": dist}
            for doc, meta, dist in zip(docs, metas, distances)
        ]
