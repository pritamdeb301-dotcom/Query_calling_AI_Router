"""Utilities to load the static knowledge‑base markdown and populate the vector store.

The loader is idempotent – if the collection already exists it will skip re‑adding
chunks.  This function can be called manually (e.g. ``python -m app.rag.loader``) or
automatically during FastAPI startup.
"""

import os
from pathlib import Path
from typing import List

from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import TextLoader

from app.rag.vectorstore import get_vectorstore
from app.config.settings import Settings

KB_PATH = Path(__file__).parents[2] / "clinic_knowledge.md"

def _load_raw_text() -> str:
    if not KB_PATH.is_file():
        raise FileNotFoundError(f"Knowledge‑base file not found at {KB_PATH}")
    return KB_PATH.read_text(encoding="utf-8")

def _split_into_chunks(text: str) -> List[dict]:
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=500,
        chunk_overlap=50,
        separators=["\n\n", "\n", " ", ""]
    )
    chunks = splitter.split_text(text)
    # Attach simple metadata so we can trace the source later
    return [{"page_content": chunk, "metadata": {"source": "clinic_knowledge.md"}} for chunk in chunks]

def ingest_kb() -> None:
    """Load the KB, chunk it, embed it, and store in Chroma.

    This function is safe to call multiple times – it will only add missing
    documents.  It is deliberately lightweight because the KB is tiny.
    """
    settings = Settings()
    vectorstore = get_vectorstore()
    collection = vectorstore.get_or_create_collection()

    # Load and chunk the markdown
    raw_text = _load_raw_text()
    documents = _split_into_chunks(raw_text)

    # Determine which documents are already present (by content hash)
    existing_ids = set(collection.get(ids=None, include=[]).get("ids", []))
    # Chroma uses custom IDs; we generate deterministic IDs based on content hash
    import hashlib
    new_ids, new_embeddings, new_metadatas, new_documents = [], [], [], []
    for doc in documents:
        content = doc["page_content"]
        doc_id = hashlib.sha256(content.encode()).hexdigest()
        if doc_id in existing_ids:
            continue
        new_ids.append(doc_id)
        new_documents.append(content)
        new_metadatas.append(doc["metadata"])

    if not new_ids:
        print("[RAG] No new knowledge‑base chunks to add – collection is up to date.")
        return

    # Embed the new chunks
    embeddings = vectorstore.embed_documents(new_documents)
    collection.add(
        ids=new_ids,
        documents=new_documents,
        metadatas=new_metadatas,
        embeddings=embeddings,
    )
    print(f"[RAG] Ingested {len(new_ids)} new chunks into the vector store.")

if __name__ == "__main__":
    ingest_kb()
