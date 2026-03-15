"""
Baronet Remote LLM Client (Groq)
Replacement for Ollama for cloud deployment
"""
import os
import json
import requests
from typing import Dict, Any, Optional
from core.logger import log

class RemoteLLMClient:
    def __init__(self, api_key: str, model: str = "llama-3.3-70b-versatile"):
        self.api_key = api_key
        self.model = model
        self.api_url = "https://api.groq.com/openai/v1/chat/completions"

    def parse_command(self, user_input: str) -> Dict[str, Any]:
        prompt = f"""You are a command parser for Baronet file automation system.
Your ONLY job is to parse natural language into structured commands.
You MUST output ONLY valid JSON, no explanations, no markdown.

Available modules and operations:
- file: create, read, write, delete, list_files, get_info

Output Schema (exactly this format):
{{
  "module": "file",
  "operation": "create|read|write|delete|list_files|get_info",
  "args": {{"filename": "example.txt", "content": "optional"}},
  "confidence": 0.0-1.0,
  "intent": "brief description of user goal",
  "risk_hint": "safe|moderate|dangerous"
}}

User request: "{user_input}"
Output ONLY the JSON:"""

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": self.model,
            "messages": [{"role": "user", "content": prompt}],
            "response_format": {"type": "json_object"},
            "temperature": 0.1
        }

        try:
            response = requests.post(self.api_url, headers=headers, json=payload, timeout=30)
            response.raise_for_status()
            data = response.json()
            content = data['choices'][0]['message']['content']
            parsed = json.loads(content)
            log.info(f"Remote LLM parsed: {parsed.get('operation')} (confidence: {parsed.get('confidence', 0):.2f})")
            return parsed
        except Exception as e:
            log.error(f"Remote LLM error: {e}")
            raise Exception(f"LLM parsing failed: {e}")

    def check_availability(self) -> bool:
        return bool(self.api_key)

# Initialize with environment variable or fallback
# In production, this will be set via Render env vars
remote_llm = RemoteLLMClient(os.getenv("GROQ_API_KEY", ""))
