"""
Curriculum Loader — Ingests subject curricula into ChromaDB for RAG retrieval.
Chunks content by topic/concept with metadata for subject, topic, and difficulty level.
"""

import os
import glob

from dotenv import load_dotenv
from langchain_community.vectorstores import Chroma
from langchain_openai import OpenAIEmbeddings
from langchain.text_splitter import RecursiveCharacterTextSplitter

load_dotenv()

CHROMA_PERSIST_DIR = os.getenv("CHROMA_PERSIST_DIR", "./data/chroma_db")
CHROMA_COLLECTION = os.getenv("CHROMA_COLLECTION_NAME", "education_curriculum")
CURRICULA_DIR = os.path.join("data", "curricula")

SUPPORTED_SUBJECTS = ["math", "science", "cs", "history"]


def load_curriculum_file(filepath: str) -> dict:
    """Load a single curriculum text file and extract metadata from its path."""
    parts = os.path.normpath(filepath).split(os.sep)
    # Expected: data/curricula/<subject>/<topic>.txt
    subject = parts[-2] if len(parts) >= 2 else "unknown"
    topic = os.path.splitext(parts[-1])[0] if parts else "unknown"

    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()

    return {
        "content": content,
        "metadata": {
            "subject": subject,
            "topic": topic,
            "source": filepath,
        },
    }


def chunk_curriculum(doc: dict, chunk_size: int = 800, chunk_overlap: int = 150) -> list[dict]:
    """Split a curriculum document into chunks preserving topic/concept boundaries."""
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        separators=["\n## ", "\n### ", "\n\n", "\n", ". ", " "],
    )
    texts = splitter.split_text(doc["content"])
    chunks = []
    for i, text in enumerate(texts):
        meta = {**doc["metadata"], "chunk_index": i}
        chunks.append({"content": text, "metadata": meta})
    return chunks


def build_vectorstore(chunks: list[dict]) -> Chroma:
    """Create or update ChromaDB vectorstore from curriculum chunks."""
    embeddings = OpenAIEmbeddings()
    texts = [c["content"] for c in chunks]
    metadatas = [c["metadata"] for c in chunks]

    vectorstore = Chroma.from_texts(
        texts=texts,
        metadatas=metadatas,
        embedding=embeddings,
        persist_directory=CHROMA_PERSIST_DIR,
        collection_name=CHROMA_COLLECTION,
    )
    return vectorstore


def get_vectorstore() -> Chroma:
    """Retrieve existing ChromaDB vectorstore."""
    embeddings = OpenAIEmbeddings()
    return Chroma(
        persist_directory=CHROMA_PERSIST_DIR,
        collection_name=CHROMA_COLLECTION,
        embedding_function=embeddings,
    )


def get_retriever(search_kwargs: dict | None = None):
    """Get a LangChain retriever from the curriculum vectorstore."""
    vs = get_vectorstore()
    return vs.as_retriever(search_kwargs=search_kwargs or {"k": 5})


def load_all_curricula() -> list[dict]:
    """Discover and load all curriculum files from the data directory."""
    all_chunks = []
    pattern = os.path.join(CURRICULA_DIR, "**", "*.txt")
    files = glob.glob(pattern, recursive=True)

    if not files:
        print(f"No curriculum files found in {CURRICULA_DIR}/")
        return all_chunks

    for filepath in sorted(files):
        print(f"Loading: {filepath}")
        doc = load_curriculum_file(filepath)
        chunks = chunk_curriculum(doc)
        all_chunks.extend(chunks)
        print(f"  → {len(chunks)} chunks from {doc['metadata']['subject']}/{doc['metadata']['topic']}")

    return all_chunks


def ingest():
    """Full ingestion pipeline: load files → chunk → embed → store."""
    print("=" * 60)
    print("Curriculum Ingestion Pipeline")
    print("=" * 60)

    chunks = load_all_curricula()
    if not chunks:
        print("No data to ingest. Run sample_curriculum.py first.")
        return

    print(f"\nTotal chunks: {len(chunks)}")
    print("Building vectorstore...")
    vs = build_vectorstore(chunks)
    print(f"Vectorstore created at {CHROMA_PERSIST_DIR}")
    print(f"Collection: {CHROMA_COLLECTION}")
    print("Done.")


if __name__ == "__main__":
    ingest()
