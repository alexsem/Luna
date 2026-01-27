from fastapi import FastAPI, Request, HTTPException, Response
from fastapi.responses import StreamingResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv
import os
import asyncio
import json
from contextlib import asynccontextmanager
from typing import List, Dict, Any, Optional, Union

from general_functions import check_ollama_connection, get_mood_from_text, ask_ollama
from project_service import project_service
from vault_service import vault_service
from knowledge_base_service import kb_service
from web_search_service import web_search_service

# Load environment variables
load_dotenv()

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Initialize DB
    await kb_service.init_db()
    yield
    # Shutdown: Clean up
    await kb_service.close()

app = FastAPI(title="Luna API", lifespan=lifespan)

# Allow CORS for development (React runs on 5173, FastAPI on 5000)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Models
class ProjectCreate(BaseModel):
    name: str
    history: List[Dict[str, Any]] = []
    config: Dict[str, Any] = {}
    trigger_init: bool = False
    description: Optional[str] = None

class ProjectUpdate(BaseModel):
    config: Dict[str, Any] = {}
    history: List[Dict[str, Any]] = []
    description: Optional[str] = None

class ChatRequest(BaseModel):
    prompt: str
    history: List[Dict[str, Any]] = []

class ConfigUpdate(BaseModel):
    vault_path: str

class VaultPathRequest(BaseModel):
    path: str

class VaultSaveRequest(BaseModel):
    path: str
    content: str

class FixGrammarRequest(BaseModel):
    content: str


@app.get("/projects")
async def get_projects():
    return project_service.list_projects()

@app.post("/projects")
async def create_project(data: ProjectCreate):
    if not data.name:
        raise HTTPException(status_code=400, detail="Name is required")
    
    project_data = await project_service.save_project(
        data.name, data.history, data.config,
        trigger_init=data.trigger_init,
        description=data.description
    )
    return {"status": "created", "project": project_data}

@app.patch("/projects/{name}")
async def update_project_config(name: str, data: ProjectUpdate):
    config = data.config
    history = data.history
    
    description = config.pop("description", None) or data.description
    
    old = project_service.load_project(name)
    if not old:
        raise HTTPException(status_code=404, detail="Project not found")
    
    if description is None:
        description = old.get("description")

    project_data = await project_service.save_project(name, history, config, description=description)
    return {"status": "updated", "project": project_data}

@app.delete("/projects/{name}")
async def remove_project(name: str, delete_files: bool = False):
    if project_service.delete_project(name, delete_physical=delete_files):
        return {"status": "deleted"}
    raise HTTPException(status_code=404, detail="Project not found")

@app.post("/projects/{name}/load")
async def load_project_route(name: str):
    project_data = project_service.load_project(name)
    if project_data:
        vp = project_data.get("config", {}).get("vault_path")
        if vp:
            vault_service.set_vault_path(vp)
        return project_data
    raise HTTPException(status_code=404, detail="Project not found")


@app.get("/health")
async def health_check():
    """Check if the backend and Ollama are running."""
    ollama_status = await check_ollama_connection()
    return {
        "status": "online",
        "ollama": "connected" if ollama_status else "disconnected"
    }

@app.post("/chat")
async def chat(chat_request: ChatRequest, request: Request):
    """
    Stream chat response.
    """
    prompt = chat_request.prompt
    history = chat_request.history
    
    async def event_generator():
        event_queue = asyncio.Queue()
        stop_event = asyncio.Event()

        # Step 1: Mood Analysis Task
        async def run_mood():
            try:
                mood = await asyncio.to_thread(get_mood_from_text, prompt)
                await event_queue.put({"type": "mood", "content": mood})
            except Exception:
                pass

        # Step 2: Ollama Request Task
        async def run_ollama():
            tool_handlers = {
                "search_vault": kb_service.search,
                "web_search": web_search_service.web_search
            }

            task_prompt = ""
            if prompt.startswith("#task:fact_check"):
                task_prompt = (
                    "SYSTEM: You are a rigorous Fact Checker. "
                    "1. Analyze the user's text. "
                    "2. Identify every factual claim. "
                    "3. First, use the `search_vault` tool to find evidence in the local knowledge base. "
                    "4. For scientific or factual claims that need external verification, use the `web_search` tool to verify against current knowledge. "
                    "5. OUTPUT REPORT: List each claim and mark it [VERIFIED], [CONTRADICTED], or [NO EVIDENCE]. "
                    "Include citations from both vault sources and web sources (with URLs).\n\n"
                )
            elif prompt.startswith("#task:fix_grammar"):
                task_prompt = (
                    "SYSTEM: You are a Professional Editor. "
                    "Improve the grammar, flow, and clarity of the text. "
                    "Maintain the author's voice but remove redundancy. "
                    "Output ONLY the rewritten text, followed by a bullet list of changes made.\n\n"
                )

            current_prompt = task_prompt + prompt if task_prompt else prompt

            try:
                async for event_type, content in ask_ollama(current_prompt, history, stop_event, tool_handlers):
                    await event_queue.put({"type": event_type, "content": content})
            except Exception as e:
                await event_queue.put({"type": "error", "content": str(e)})
            finally:
                await event_queue.put({"type": "done"})

        # Launch tasks
        asyncio.create_task(run_mood())
        ollama_task = asyncio.create_task(run_ollama())

        try:
            while True:
                if await request.is_disconnected():
                    stop_event.set()
                    ollama_task.cancel()
                    break
                
                try:
                    item = await asyncio.wait_for(event_queue.get(), timeout=0.1)
                    yield json.dumps(item) + "\n"
                    if item.get("type") in ["done", "error"]:
                        break
                except asyncio.TimeoutError:
                    continue
        except asyncio.CancelledError:
            stop_event.set()
            ollama_task.cancel()
            raise

    return StreamingResponse(event_generator(), media_type="application/x-ndjson")

@app.post("/stop")
async def stop_generation():
    # Global stop is deprecated in favor of per-request cancellation via disconnect
    return {"status": "stopped", "message": "Global stop is deprecated. Requests are now cancelled on disconnect."}


# Vault Routes
@app.get("/config")
async def get_config():
    return {"vault_path": vault_service.vault_path}

@app.post("/config")
async def update_config(data: ConfigUpdate):
    if not data.vault_path:
        raise HTTPException(status_code=400, detail="Path required")
    
    if vault_service.set_vault_path(data.vault_path):
        return {"status": "updated", "vault_path": data.vault_path}
    raise HTTPException(status_code=500, detail="Failed to save")

@app.get("/vault/files")
async def get_vault_files():
    files = vault_service.list_files()
    if isinstance(files, dict) and "error" in files:
         raise HTTPException(status_code=400, detail=files["error"])
    return files

@app.post("/vault/read")
async def read_vault_file_route(data: VaultPathRequest):
    try:
        content = vault_service.read_file(data.path)
        if content is None:
            raise HTTPException(status_code=404, detail="File not found")
        return {"content": content}
    except ValueError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/vault/save")
async def save_vault_file_route(data: VaultSaveRequest):
    try:
        if vault_service.save_file(data.path, data.content):
            return {"status": "saved", "path": data.path}
        raise HTTPException(status_code=500, detail="Failed to save file")
    except ValueError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/vault/create")
async def create_vault_file_route(data: VaultPathRequest):
    success, result = vault_service.create_file(data.path)
    if success:
        return {"status": "created", "path": result}
    raise HTTPException(status_code=400, detail=result)

@app.post("/vault/fix-grammar")
async def fix_grammar_route(data: FixGrammarRequest):
    prompt = (
        "Correct the grammar, spelling, and punctuation of the following text. "
        "Maintain the original tone and style. "
        "IMPORTANT: RETURN ONLY THE CORRECTED TEXT. DO NOT EXPLAIN OR ADD CONVERSATIONAL FILLER.\n\n"
        "### TEXT TO CORRECT:\n"
        f"{data.content}"
    )

    corrected_text = ""
    try:
        async for event_type, content in ask_ollama(prompt, []):
            if event_type == "chunk":
                corrected_text += content
        
        return {"original": data.content, "fixed": corrected_text}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/vault/sync")
async def sync_vault_route():
    vault_path = vault_service.vault_path
    if not vault_path:
        raise HTTPException(status_code=400, detail="Vault path not set")

    async def generate_progress():
        async for progress in kb_service.sync_vault(vault_path):
            yield json.dumps(progress) + "\n"
            
    return StreamingResponse(generate_progress(), media_type="application/x-ndjson")


if __name__ == '__main__':
    import uvicorn
    port = int(os.getenv("BACKEND_PORT", 5000))
    uvicorn.run(app, host="0.0.0.0", port=port)
