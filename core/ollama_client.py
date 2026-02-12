"""
OpenClaw Ollama Client
Isolated LLM interface with strict JSON contracts
CRITICAL: AI suggests, never executes
"""
from typing import Dict, Any, Optional
import json
import time
from pathlib import Path

from core.logger import log


class OllamaClient:
    """Isolated interface to Ollama LLM - NO system access"""
    
    # Strict JSON schema for responses
    RESPONSE_SCHEMA = {
        "type": "object",
        "required": ["module", "operation", "args", "confidence"],
        "properties": {
            "module": {"type": "string"},
            "operation": {"type": "string"},
            "args": {"type": "object"},
            "confidence": {"type": "number", "minimum": 0, "maximum": 1},
            "intent": {"type": "string"},
            "risk_hint": {"type": "string", "enum": ["safe", "moderate", "dangerous"]}
        }
    }
    
    PROMPT_TEMPLATE = """You are a command parser for OpenClaw file automation system.

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

Rules:
- For delete operations, set risk_hint to "dangerous"
- For read/list operations, set risk_hint to "safe"  
- For create/write operations, set risk_hint to "moderate"
- confidence should be 0.9+ for clear commands, lower if ambiguous
- If unclear, set confidence to 0.5 or less

User request: "{user_input}"

Output ONLY the JSON:"""
    
    def __init__(self, 
                 model: str = "llama3.2",
                 base_url: str = "http://localhost:11434",
                 timeout: int = 30,
                 max_retries: int = 3):
        self.model = model
        self.base_url = base_url
        self.timeout = timeout
        self.max_retries = max_retries
        
        # Import ollama only when needed
        try:
            import ollama
            self.ollama = ollama
            self.available = True
        except ImportError:
            log.warning("Ollama package not installed")
            self.available = False
    
    def parse_command(self, user_input: str) -> Dict[str, Any]:
        """
        Parse natural language → structured command
        
        Args:
            user_input: Natural language command from user
        
        Returns:
            Parsed command dict with schema validation
        
        Raises:
            OllamaUnavailable: If Ollama not running
            ParsingError: If max retries exceeded or JSON invalid
        """
        if not self.available:
            raise OllamaUnavailable("Ollama package not installed")
        
        # Format prompt
        prompt = self.PROMPT_TEMPLATE.format(user_input=user_input)
        
        # Retry loop
        for attempt in range(self.max_retries):
            try:
                # Call Ollama with timeout
                response = self._call_ollama(prompt, timeout=self.timeout)
                
                # Parse JSON
                parsed = self._parse_json(response)
                
                # Validate schema
                if self._validate_schema(parsed):
                    log.info(f"Parsed command: {parsed['operation']} (confidence: {parsed['confidence']:.2f})")
                    return parsed
                else:
                    log.warning(f"Schema validation failed (attempt {attempt + 1})")
                    if attempt == self.max_retries - 1:
                        raise ParsingError("Response doesn't match schema")
                    continue
                    
            except json.JSONDecodeError as e:
                log.warning(f"JSON parse error (attempt {attempt + 1}): {e}")
                if attempt == self.max_retries - 1:
                    raise ParsingError(f"LLM output not valid JSON after {self.max_retries} retries")
                continue
            
            except Exception as e:
                log.error(f"Ollama error: {e}")
                if attempt == self.max_retries - 1:
                    raise OllamaUnavailable(f"Ollama error: {e}")
                time.sleep(1)  # Brief delay before retry
                continue
        
        raise ParsingError("Max retries exceeded")
    
    def _call_ollama(self, prompt: str, timeout: int) -> str:
        """Call Ollama API with timeout"""
        try:
            # Use generate for single-shot parsing with JSON format
            response = self.ollama.generate(
                model=self.model,
                prompt=prompt,
                format='json',  # Force JSON output
                options={
                    'temperature': 0.1,  # Low temp for consistent parsing
                    'top_p': 0.9,
                }
            )
            
            return response['response']
            
        except Exception as e:
            raise OllamaUnavailable(f"Ollama API error: {e}")
    
    def _parse_json(self, response: str) -> Dict[str, Any]:
        """Extract and parse JSON from response"""
        # LLMs sometimes wrap JSON in markdown
        response = response.strip()
        
        # Remove markdown code fences
        if response.startswith('```'):
            lines = response.split('\n')
            # Remove first and last lines
            response = '\n'.join(lines[1:-1])
        
        # Remove "json" language identifier
        response = response.replace('```json', '').replace('```', '').strip()
        
        # Ensure it's complete JSON (has closing brace)
        if not response.endswith('}'):
            response = response + '}'
        
        # Parse
        return json.loads(response)
    
    def _validate_schema(self, parsed: Dict[str, Any]) -> bool:
        """Validate parsed command matches schema"""
        # Check required fields
        required = ['module', 'operation', 'args', 'confidence']
        if not all(field in parsed for field in required):
            return False
        
        # Check types
        if not isinstance(parsed['module'], str):
            return False
        if not isinstance(parsed['operation'], str):
            return False
        if not isinstance(parsed['args'], dict):
            return False
        if not isinstance(parsed['confidence'], (int, float)):
            return False
        
        # Check confidence range
        if not 0 <= parsed['confidence'] <= 1:
            return False
        
        return True
    
    def check_availability(self) -> bool:
        """Check if Ollama is running and model is available"""
        if not self.available:
            return False
        
        try:
            models_response = self.ollama.list()
            
            # Handle ListResponse object (has models attribute)
            if hasattr(models_response, 'models'):
                models_list = models_response.models
            elif isinstance(models_response, dict):
                models_list = models_response.get('models', [])
            else:
                models_list = []
            
            # Extract model names from Model objects or dicts
            model_names = []
            for m in models_list:
                if hasattr(m, 'model'):
                    model_names.append(m.model)
                elif isinstance(m, dict):
                    model_names.append(m.get('name', m.get('model', '')))
            
            # Check if our model exists (llama3.2 or llama3.2:latest)
            if not any(self.model in name or name.startswith(self.model) for name in model_names):
                log.warning(f"Model {self.model} not found. Available: {model_names}")
                return False
            
            return True
            
        except Exception as e:
            log.error(f"Ollama availability check failed: {e}")
            return False


class OllamaUnavailable(Exception):
    """Raised when Ollama is not available"""
    pass


class ParsingError(Exception):
    """Raised when LLM output cannot be parsed"""
    pass


# Global instance (created but may not be available)
ollama_client = OllamaClient()
