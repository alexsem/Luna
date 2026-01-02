import os
import chromadb
import requests
import logging
from typing import List, Dict, Any, Optional, Union, Tuple, Generator

logger = logging.getLogger(__name__)

class KnowledgeBaseService:
    def __init__(self) -> None:
        self.chroma_host = os.getenv("CHROMA_DB_HOST", "localhost")
        self.chroma_port = os.getenv("CHROMA_DB_PORT", "8000")
        
        self.collection_world = "world_data"
        self.collection_novel = "novel_data"
        
        # Embedding Config (Ollama)
        self.ollama_url = os.getenv("OLLAMA_URL", "http://localhost:11434/api/embeddings")
        self.ollama_chat_url = self.ollama_url.replace("/embeddings", "/chat").replace("/generate", "/chat") 
        
        if "generate" in self.ollama_url:
            self.ollama_embed_url = self.ollama_url.replace("/generate", "/embeddings")
        else:
            self.ollama_embed_url = self.ollama_url
            
        self.model = "nomic-embed-text" 
        self.extract_model = "llama3.2"
        
        self._client = None
        logger.info("KnowledgeBaseService initialized")

    @property
    def client(self) -> Optional[chromadb.HttpClient]:
        if self._client is None:
            try:
                self._client = chromadb.HttpClient(host=self.chroma_host, port=self.chroma_port)
            except Exception as e:
                logger.error(f"Failed to connect to ChromaDB: {e}")
        return self._client

    def init_db(self) -> Tuple[bool, str]:
        client = self.client
        if client:
            try:
                client.heartbeat()
                # Ensure collections exist
                client.get_or_create_collection(name=self.collection_world)
                client.get_or_create_collection(name=self.collection_novel)
                return True, "ChromaDB Connected."
            except Exception as e:
                return False, str(e)
        return False, "Could not connect."

    def get_embedding(self, text: str) -> Optional[List[float]]:
        """Generates embedding using Ollama."""
        try:
            response = requests.post(
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

    def sync_vault(self, vault_path: str) -> Generator[Dict[str, Any], None, None]:
        client = self.client
        if not client:
            yield {"status": "error", "message": "ChromaDB not available."}
            return

        # Delete existing to Resync
        try:
            client.delete_collection(self.collection_world)
            client.delete_collection(self.collection_novel)
        except:
            pass

        col_world = client.get_or_create_collection(name=self.collection_world)
        col_novel = client.get_or_create_collection(name=self.collection_novel)
        
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
                        with open(full_path, 'r', encoding='utf-8') as f:
                            text = f.read()
                        
                        chunks = self.chunk_text(text)
                        
                        ids = []
                        documents = []
                        embeddings = []
                        metadatas = []

                        for idx, chunk in enumerate(chunks):
                            vec = self.get_embedding(chunk)
                            if vec:
                                chunk_id = f"{rel_path}_{idx}"
                                ids.append(chunk_id)
                                documents.append(chunk)
                                embeddings.append(vec)
                                metadatas.append({"source": rel_path, "type": "novel" if is_novel else "world"})
                        
                        if ids:
                            target_col.add(ids=ids, documents=documents, embeddings=embeddings, metadatas=metadatas)

                        yield {"status": "progress", "file": rel_path}
                        
                    except Exception as e:
                        logger.error(f"Error processing {rel_path}: {e}")
                        yield {"status": "error", "message": f"Error in {rel_path}: {e}"}

        yield {"status": "done", "total": files_processed}

    def search(self, query: str, top_k: int = 3) -> List[str]:
        vec = self.get_embedding(query)
        if not vec: return []
        
        client = self.client
        if not client: return []

        results = []
        try:
            # Search World
            c_world = client.get_collection(self.collection_world)
            r_world = c_world.query(query_embeddings=[vec], n_results=top_k)
            if r_world and r_world['documents']:
                for doc in r_world['documents'][0]:
                    clean_doc = doc.strip()
                    if clean_doc and clean_doc not in results:
                        results.append(clean_doc)

            # Search Novel
            c_novel = client.get_collection(self.collection_novel)
            r_novel = c_novel.query(query_embeddings=[vec], n_results=top_k)
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
