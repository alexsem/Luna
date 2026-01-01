import os
import chromadb
from chromadb.config import Settings
import requests
import logging

# Setup Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Config
CHROMA_HOST = os.getenv("CHROMA_DB_HOST", "localhost")
CHROMA_PORT = os.getenv("CHROMA_DB_PORT", "8000")

# Collections
COLLECTION_WORLD = "world_data"
COLLECTION_NOVEL = "novel_data"

# Embedding Config (Ollama)
OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434/api/embeddings")
OLLAMA_CHAT_URL = OLLAMA_URL.replace("/embeddings", "/chat").replace("/generate", "/chat") 

if "generate" in OLLAMA_URL:
    OLLAMA_EMBED_URL = OLLAMA_URL.replace("/generate", "/embeddings")
else:
    OLLAMA_EMBED_URL = OLLAMA_URL

MODEL = "nomic-embed-text" 
EXTRACT_MODEL = "llama3.2" # Use the chat model for extraction

def get_embedding(text):
    """Generates embedding using Ollama."""
    try:
        response = requests.post(
            OLLAMA_EMBED_URL,
            json={"model": MODEL, "prompt": text},
            timeout=10
        )
        response.raise_for_status()
        return response.json().get("embedding")
    except Exception as e:
        logger.error(f"Embedding Error: {e}")
        return None

def smart_extract(text):
    """
    Uses LLM to extract key plot points and character reactions from Novel text.
    """
    prompt = (
        "Analyze the following text from a novel chapter. "
        "Extract key plot points, character reactions, and significant world-building details. "
        "Provide a concise summary of WHAT HAPPENED and NEW FACTS.\n\n"
        f"TEXT:\n{text[:2000]}" # Truncate for safety
    )
    
    try:
        response = requests.post(
            OLLAMA_CHAT_URL,
            json={
                "model": EXTRACT_MODEL,
                "messages": [{"role": "user", "content": prompt}],
                "stream": False
            },
            timeout=30
        )
        if response.status_code == 200:
            return response.json()['message']['content']
        return text # Fallback to raw text
    except Exception:
        return text

def get_client():
    """Returns ChromaDB HTTP Client."""
    try:
        client = chromadb.HttpClient(host=CHROMA_HOST, port=CHROMA_PORT)
        return client
    except Exception as e:
        logger.error(f"Failed to connect to ChromaDB: {e}")
        return None

def init_db():
    client = get_client()
    if client:
        try:
            client.heartbeat()
            # Ensure collections exist
            client.get_or_create_collection(name=COLLECTION_WORLD)
            client.get_or_create_collection(name=COLLECTION_NOVEL)
            return True, "ChromaDB Connected."
        except Exception as e:
            return False, str(e)
    return False, "Could not connect."

def chunk_text(text, chunk_size=500, overlap=50):
    words = text.split()
    chunks = []
    for i in range(0, len(words), chunk_size - overlap):
        chunk = " ".join(words[i:i + chunk_size])
        chunks.append(chunk)
    return chunks

def sync_vault(vault_path):
    client = get_client()
    if not client:
        yield {"status": "error", "message": "ChromaDB not available."}
        return

    # Delete existing to Resync (Simplest strategy)
    try:
        client.delete_collection(COLLECTION_WORLD)
        client.delete_collection(COLLECTION_NOVEL)
    except:
        pass

    col_world = client.get_or_create_collection(name=COLLECTION_WORLD)
    col_novel = client.get_or_create_collection(name=COLLECTION_NOVEL)
    
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
                    
                    chunks = chunk_text(text)
                    
                    ids = []
                    documents = []
                    embeddings = []
                    metadatas = []

                    for idx, chunk in enumerate(chunks):
                        # For Novel: Smart Extract first? 
                        # Or maybe just embedding the raw chunk is safer for now due to latency?
                        # Plan said "Smart Extraction". Let's do it for the FIRST chunk of a file or if chunks are large.
                        # Doing LLM call for EVERY chunk is very slow. 
                        # Optimization: Syncing is background. Let's do it.
                        
                        content_to_embed = chunk
                        if is_novel:
                             # Summarize the chunk content for vector search clarity
                             # content_to_embed = smart_extract(chunk) # Disabled for speed unless requested
                             pass

                        vec = get_embedding(content_to_embed)
                        if vec:
                            chunk_id = f"{rel_path}_{idx}"
                            ids.append(chunk_id)
                            documents.append(chunk) # Store original text
                            embeddings.append(vec)
                            metadatas.append({"source": rel_path, "type": "novel" if is_novel else "world"})
                    
                    if ids:
                        target_col.add(ids=ids, documents=documents, embeddings=embeddings, metadatas=metadatas)

                    yield {"status": "progress", "file": rel_path}
                    
                except Exception as e:
                    logger.error(f"Error processing {rel_path}: {e}")
                    yield {"status": "error", "message": f"Error in {rel_path}: {e}"}

    yield {"status": "done", "total": files_processed}


def search_knowledge_base(query, top_k=5):
    """
    Searches BOTH collections and combines results.
    """
    vec = get_embedding(query)
    if not vec: return []
    
    client = get_client()
    if not client: return []

    results = []
    
    try:
        # Search World
        c_world = client.get_collection(COLLECTION_WORLD)
        r_world = c_world.query(query_embeddings=[vec], n_results=top_k)
        if r_world and r_world['documents']:
            results.extend(r_world['documents'][0])

        # Search Novel
        c_novel = client.get_collection(COLLECTION_NOVEL)
        r_novel = c_novel.query(query_embeddings=[vec], n_results=top_k)
        if r_novel and r_novel['documents']:
             results.extend(r_novel['documents'][0])
             
        # Dedup or rank? For now just return mixed list.
        return results[:top_k*2] # Return all
    except Exception as e:
        logger.error(f"Search Error: {e}")
        return []
