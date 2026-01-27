import os
import chromadb
import httpx
import logging
import asyncio
from typing import List, Dict, Any, Optional, Union, Tuple, AsyncGenerator

logger = logging.getLogger(__name__)

class KnowledgeBaseService:
    def __init__(self) -> None:
        self.chroma_host = os.getenv("CHROMA_DB_HOST", "localhost")
        self.chroma_port = os.getenv("CHROMA_DB_PORT", "8000")
        
        self.collection_world = "world_data"
        self.collection_novel = "novel_data"
        
        # Embedding Config (Ollama)
        self.ollama_url = os.getenv("OLLAMA_URL", "http://localhost:11434/api/embeddings")
        
        if "generate" in self.ollama_url:
            self.ollama_embed_url = self.ollama_url.replace("/generate", "/embeddings")
        else:
            self.ollama_embed_url = self.ollama_url
            
        self.model = "nomic-embed-text" 
        self.extract_model = "llama3.2"
        
        self._client: Optional[chromadb.AsyncHttpClient] = None
        logger.info("KnowledgeBaseService initialized")

    async def get_client(self) -> chromadb.AsyncHttpClient:
        if self._client is None:
            self._client = await chromadb.AsyncHttpClient(host=self.chroma_host, port=self.chroma_port)
        return self._client

    async def close(self):
        if self._client:
            try:
                await self._client.close()
                self._client = None
                logger.info("ChromaDB client closed.")
            except Exception as e:
                logger.error(f"Error closing ChromaDB client: {e}")

    async def init_db(self) -> Tuple[bool, str]:
        try:
            client = await self.get_client()
            await client.heartbeat()
            # Ensure collections exist
            await client.get_or_create_collection(name=self.collection_world)
            await client.get_or_create_collection(name=self.collection_novel)
            return True, "ChromaDB Connected."
        except Exception as e:
            logger.error(f"Failed to connect/init ChromaDB: {e}")
            return False, str(e)

    async def get_embedding(self, text: str) -> Optional[List[float]]:
        """Generates embedding using Ollama."""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    self.ollama_embed_url,
                    json={"model": self.model, "prompt": text},
                    timeout=10
                )
                response.raise_for_status()
                return response.json().get("embedding")
        except Exception as e:
            logger.error(f"Embedding Error: {e}")
            return None

    def chunk_text(self, text: str, chunk_size: int = 500, overlap: int = 50) -> List[str]:
        words = text.split()
        chunks = []
        for i in range(0, len(words), chunk_size - overlap):
            chunk = " ".join(words[i:i + chunk_size])
            chunks.append(chunk)
        return chunks

    async def sync_vault(self, vault_path: str) -> AsyncGenerator[Dict[str, Any], None]:
        try:
            client = await self.get_client()
        except Exception as e:
            yield {"status": "error", "message": f"ChromaDB not available: {e}"}
            return

        # Delete existing to Resync
        try:
            await client.delete_collection(self.collection_world)
            await client.delete_collection(self.collection_novel)
        except:
            pass

        col_world = await client.get_or_create_collection(name=self.collection_world)
        col_novel = await client.get_or_create_collection(name=self.collection_novel)
        
        files_processed = 0
        
        for root, _, files in os.walk(vault_path):
            for file in files:
                if file.lower().endswith(('.md', '.txt')):
                    files_processed += 1
                    full_path = os.path.join(root, file)
                    rel_path = os.path.relpath(full_path, vault_path)
                    
                    # Determine Category
                    is_novel = "Novel" in rel_path
                    target_col = col_novel if is_novel else col_world
                    
                    try:
                        # PR Feedback: Reading file off the event loop
                        text = await asyncio.to_thread(self._read_file_sync, full_path)
                        
                        chunks = self.chunk_text(text)
                        
                        ids = []
                        documents = []
                        embeddings = []
                        metadatas = []

                        for idx, chunk in enumerate(chunks):
                            vec = await self.get_embedding(chunk)
                            if vec:
                                chunk_id = f"{rel_path}_{idx}"
                                ids.append(chunk_id)
                                documents.append(chunk)
                                embeddings.append(vec)
                                metadatas.append({"source": rel_path, "type": "novel" if is_novel else "world"})
                        
                        if ids:
                            await target_col.add(ids=ids, documents=documents, embeddings=embeddings, metadatas=metadatas)

                        yield {"status": "progress", "file": rel_path}
                        
                    except Exception as e:
                        logger.error(f"Error processing {rel_path}: {e}")
                        yield {"status": "error", "message": f"Error in {rel_path}: {e}"}

        yield {"status": "done", "total": files_processed}

    def _read_file_sync(self, filepath: str) -> str:
        with open(filepath, 'r', encoding='utf-8') as f:
            return f.read()

    async def search(self, query: str, top_k: int = 3) -> List[str]:
        vec = await self.get_embedding(query)
        if not vec: return []
        
        try:
            client = await self.get_client()
        except Exception:
            return []

        results = []
        try:
            # Search World
            c_world = await client.get_collection(self.collection_world)
            r_world = await c_world.query(query_embeddings=[vec], n_results=top_k)
            if r_world and r_world['documents']:
                for doc in r_world['documents'][0]:
                    clean_doc = doc.strip()
                    if clean_doc and clean_doc not in results:
                        results.append(clean_doc)

            # Search Novel
            c_novel = await client.get_collection(self.collection_novel)
            r_novel = await c_novel.query(query_embeddings=[vec], n_results=top_k)
            if r_novel and r_novel['documents']:
                 for doc in r_novel['documents'][0]:
                    clean_doc = doc.strip()
                    if clean_doc and clean_doc not in results:
                        results.append(clean_doc)
                 
            return results[:4] # Cap at 4 highly relevant snippets
        except Exception as e:
            logger.error(f"Search Error: {e}")
            return []

# Global instance
kb_service = KnowledgeBaseService()
