from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from pathlib import Path
import os
import time

from core.openclaw import baronet
from core.ai_handler import create_ai_handler

app = FastAPI(title="Baronet API", description="AI-Powered File Automation with 6-Layer Safety")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

WORKSPACE_PATH = Path(os.getenv("WORKSPACE_PATH", "./workspace")).resolve()
WORKSPACE_PATH.mkdir(parents=True, exist_ok=True)
ai_handler = create_ai_handler(WORKSPACE_PATH)

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

class CommandRequest(BaseModel):
    command: str

@app.get("/")
async def root():
    return FileResponse("static/index.html")

@app.get("/api/status")
async def status():
    return {
        "status": "online",
        "service": "Baronet",
        "version": "0.2.0",
        "workspace": str(WORKSPACE_PATH)
    }

@app.get("/health")
async def health():
    return {
        "status": "healthy",
        "ai_ready": ai_handler.check_availability() or bool(os.getenv("GROQ_API_KEY")),
        "timestamp": time.time()
    }

@app.post("/command")
async def execute_ai_command(req: CommandRequest):
    # Sanitize and Validate via Safety Pipeline
    result = ai_handler.parse_and_validate(req.command)
    
    if not result['safe']:
        return {
            "success": False,
            "error": result['error'],
            "risk": result['risk'].name if result['risk'] else "UNKNOWN"
        }
    
    # Execute the command
    exec_result = baronet.execute(result['command'])
    return {
        "success": exec_result.get('success', False),
        "command": result['command'],
        "risk": result['risk'].name,
        "result": exec_result
    }

@app.get("/files")
async def list_files():
    exec_result = baronet.execute({
        "module": "file",
        "operation": "list_files",
        "args": {}
    })
    return exec_result

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
