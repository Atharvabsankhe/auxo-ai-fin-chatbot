import chromadb
import google.generativeai as genai
from typing import List
from src.models import DocumentChunk
from src.config import Config, GEMINI_API_KEY
import time

# Suppress chromadb telemetry noise
import chromadb.config
chromadb.config.Settings(anonymized_telemetry=False)

EMBEDDING_MODEL = "models/gemini-embedding-2"


class VectorStore:
    """ChromaDB-backed vector store using Gemini embeddings."""

    def __init__(self):
        genai.configure(api_key=GEMINI_API_KEY)
        self.chroma_client = chromadb.PersistentClient(path=Config.CHROMA_DB_DIR)
        self.collection = self.chroma_client.get_or_create_collection(
            name="infosys_docs",
        )

    def add_chunks(self, chunks: List[DocumentChunk]):
        """Embed and store chunks in batches, skipping those already indexed."""
        if not chunks:
            return

        # Fetch existing IDs to skip them
        existing_ids = set()
        try:
            results = self.collection.get(include=[])
            if results and "ids" in results:
                existing_ids = set(results["ids"])
                print(f"  Found {len(existing_ids)} existing chunks in vector store. Skipping...")
        except Exception as e:
            print(f"  Error fetching existing IDs: {e}")

        # Filter chunks that aren't indexed yet
        new_chunks = [c for c in chunks if c.id not in existing_ids]
        if not new_chunks:
            print("  All chunks already indexed.")
            return

        print(f"  Indexing {len(new_chunks)} new chunks...")

        batch_size = 5  # Reduced to 5 for maximum stability on free tier
        total_batches = (len(new_chunks) + batch_size - 1) // batch_size

        for batch_idx in range(total_batches):
            start = batch_idx * batch_size
            batch = new_chunks[start : start + batch_size]

            ids = [c.id for c in batch]
            documents = [c.content for c in batch]
            metadatas = [
                {
                    "source": c.source,
                    "page": c.page if c.page is not None else -1,
                    "type": c.type,
                    "quarter": c.quarter if c.quarter else "Unknown",
                }
                for c in batch
            ]
            contents = [c.content for c in batch]

            # Retry loop for rate limits
            success = False
            for attempt in range(10):  # More retries
                try:
                    result = genai.embed_content(
                        model=EMBEDDING_MODEL,
                        content=contents,
                        task_type="retrieval_document",
                    )
                    embeddings = result["embedding"]

                    self.collection.upsert(  # Use upsert
                        ids=ids,
                        embeddings=embeddings,
                        documents=documents,
                        metadatas=metadatas,
                    )
                    print(f"  Indexed batch {batch_idx + 1}/{total_batches}")
                    success = True
                    break
                except Exception as e:
                    err = str(e).lower()
                    if "429" in err or "quota" in err:
                        wait = 30 * (attempt + 1)  # Longer wait
                        print(f"  Rate limited, waiting {wait}s...")
                        time.sleep(wait)
                    else:
                        print(f"  Embedding error: {e}")
                        break
            
            if not success:
                print(f"  CRITICAL: Failed to index batch {batch_idx + 1} after multiple retries. Moving on...")

            # Delay between batches to stay under 15 RPM
            time.sleep(5)

    def search(self, query: str, top_k: int = 5) -> List[dict]:
        """Search the vector store for similar chunks."""
        for attempt in range(3):
            try:
                result = genai.embed_content(
                    model=EMBEDDING_MODEL,
                    content=query,
                    task_type="retrieval_query",
                )
                query_embedding = result["embedding"]

                results = self.collection.query(
                    query_embeddings=[query_embedding],
                    n_results=top_k,
                )

                formatted = []
                if results and results["ids"] and len(results["ids"][0]) > 0:
                    for i in range(len(results["ids"][0])):
                        formatted.append({
                            "id": results["ids"][0][i],
                            "content": results["documents"][0][i],
                            "metadata": results["metadatas"][0][i],
                            "distance": (
                                results["distances"][0][i]
                                if "distances" in results and results["distances"]
                                else 0
                            ),
                        })
                return formatted
            except Exception as e:
                if "429" in str(e):
                    time.sleep(10)
                else:
                    print(f"Search error: {e}")
                    return []
        return []
