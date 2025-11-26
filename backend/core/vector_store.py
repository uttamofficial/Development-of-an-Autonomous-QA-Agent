"""
Vector store management using Chroma.
"""
import os
import sys
import warnings
from typing import List, Dict

# Disable ALL telemetry BEFORE importing chromadb
# Must be set before any chromadb import
os.environ["ANONYMIZED_TELEMETRY"] = "False"
os.environ["CHROMA_TELEMETRY"] = "False"
os.environ["OTEL_SDK_DISABLED"] = "true"
os.environ["CHROMA_SERVER_NOFILE"] = "1"  # Disable file-based telemetry

# Suppress ChromaDB telemetry warnings
warnings.filterwarnings("ignore", category=UserWarning, module="chromadb")

# Suppress telemetry errors by redirecting stderr during import
class SuppressTelemetryErrors:
    """Context manager to suppress ChromaDB telemetry errors."""
    def __init__(self):
        self.original_stderr = sys.stderr
        self.null_stderr = open(os.devnull, 'w')
    
    def __enter__(self):
        sys.stderr = self.null_stderr
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        sys.stderr = self.original_stderr
        self.null_stderr.close()
        return False

try:
    # Suppress telemetry errors during import
    with SuppressTelemetryErrors():
        import chromadb
        from chromadb.config import Settings as ChromaSettings
        from chromadb.api.types import EmbeddingFunction
except ImportError:
    chromadb = None
    ChromaSettings = None
    EmbeddingFunction = None

try:
    from sentence_transformers import SentenceTransformer
except ImportError:
    SentenceTransformer = None


class SentenceTransformerEmbedding(EmbeddingFunction):
    """Embedding function adapter for ChromaDB (>=0.4.16)."""

    def __init__(self, model_name: str):
        if SentenceTransformer is None:
            raise ImportError(
                "sentence-transformers is required. Install: pip install sentence-transformers"
            )
        self.model = SentenceTransformer(model_name)

    def __call__(self, input: List[str]) -> List[List[float]]:
        embeddings = self.model.encode(input, show_progress_bar=False)
        return embeddings.tolist()


class VectorStore:
    """Manages the Chroma vector database."""

    def __init__(
        self,
        db_path: str,
        collection_name: str,
        embedding_model_name: str = "sentence-transformers/all-MiniLM-L6-v2",
    ):

        if chromadb is None:
            raise ImportError("chromadb is required. Install: pip install chromadb")

        os.makedirs(db_path, exist_ok=True)

        # Disable telemetry in ChromaDB settings
        settings = ChromaSettings(
            anonymized_telemetry=False,
            allow_reset=True,
        )
        
        # Additional telemetry disable (redundant but ensures it's off)
        if hasattr(settings, 'anonymized_telemetry'):
            settings.anonymized_telemetry = False

        # Persistent DB client (suppress telemetry errors during creation)
        with SuppressTelemetryErrors():
            self.client = chromadb.PersistentClient(
                path=db_path,
                settings=settings,
            )

        self.embedding_function = SentenceTransformerEmbedding(embedding_model_name)

        # Suppress telemetry errors during collection creation
        with SuppressTelemetryErrors():
            self.collection = self.client.get_or_create_collection(
                name=collection_name,
                embedding_function=self.embedding_function,
            )

    def add_documents(self, docs: List[Dict]) -> None:
        """Add documents to the vector store."""
        if not docs:
            return

        texts = [doc["text"] for doc in docs]
        metadatas = [doc.get("metadata", {}) for doc in docs]
        ids = [doc.get("id", f"doc_{i}") for i, doc in enumerate(docs)]

        self.collection.add(
            documents=texts,
            metadatas=metadatas,
            ids=ids,
        )

    def query(self, query_text: str, top_k: int = 5) -> List[Dict]:
        """Query vector store."""
        result = self.collection.query(
            query_texts=[query_text],
            n_results=top_k,
        )

        formatted = []
        if result.get("documents") and len(result["documents"][0]) > 0:
            for i in range(len(result["documents"][0])):
                formatted.append(
                    {
                        "text": result["documents"][0][i],
                        "metadata": result["metadatas"][0][i] if result["metadatas"] else {},
                        "distance": result["distances"][0][i] if result["distances"] else None,
                        "id": result["ids"][0][i] if result["ids"] else None,
                    }
                )

        return formatted

    def delete_collection(self) -> None:
        """Delete and recreate collection."""
        name = self.collection.name
        self.client.delete_collection(name=name)
        self.collection = self.client.get_or_create_collection(
            name=name,
            embedding_function=self.embedding_function,
        )
