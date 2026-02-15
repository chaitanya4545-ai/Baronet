"""
Baronet AI Command Handler
Integrates AI parsing with safety pipeline
"""
from typing import Dict, Any, Optional
from pathlib import Path

from core.logger import log
from core.ollama_client import ollama_client, OllamaUnavailable, ParsingError
from core.schema_validator import schema_validator
from core.semantic_guard import semantic_guard
from core.risk_classifier import risk_classifier, RiskLevel
from core.dependency_validator import create_dependency_validator


class AICommandHandler:
    """Handles AI command parsing with full safety pipeline"""
    
    def __init__(self, workspace: Path):
        self.workspace = workspace
        self.dependency_validator = create_dependency_validator(workspace)
    
    def parse_and_validate(self, user_input: str) -> Dict[str, Any]:
        """
        Parse natural language → validated command
        
        Full safety pipeline:
        1. Sanitize input
        2. Parse with AI
        3. Validate schema
        4. Check semantics
        5. Classify risk
        6. Check dependencies
        
        Returns:
            {
                'command': {...},
                'risk': RiskLevel,
                'safe': bool,
                'error': Optional[str]
            }
        """
        result = {
            'command': None,
            'risk': RiskLevel.SAFE,
            'safe': False,
            'error': None
        }
        
        # Step 1: Sanitize input
        sanitized = semantic_guard.sanitize_user_input(user_input)
        if '[BLOCKED]' in sanitized:
            result['error'] = "🛡️  Input contains injection attempt - BLOCKED"
            return result
        
        # Step 2: Parse with AI
        try:
            parsed = ollama_client.parse_command(sanitized)
        except OllamaUnavailable as e:
            result['error'] = f"⚠️  Ollama not available: {e}"
            return result
        except ParsingError as e:
            result['error'] = f"⚠️  Failed to parse command: {e}"
            return result
        
        result['command'] = parsed
        
        # Step 3: Validate schema
        valid, error = schema_validator.validate(parsed)
        if not valid:
            result['error'] = f"❌ Schema validation failed: {error}"
            return result
        
        # Step 4: Check semantics
        safe, reason = semantic_guard.check_command(parsed, user_input)
        if not safe:
            result['error'] = semantic_guard.explain_block(reason)
            return result
        
        # Step 5: Classify risk
        risk = risk_classifier.classify_operation(
            parsed['operation'],
            parsed['args']
        )
        result['risk'] = risk
        
        # Step 6: Check dependencies
        valid, error = self.dependency_validator.validate_command(parsed)
        if not valid:
            result['error'] = f"⚠️  Dependency check failed: {error}"
            return result
        
        # All checks passed!
        result['safe'] = True
        return result
    
    def format_approval_prompt(self, result: Dict[str, Any]) -> str:
        """
        Format user approval prompt with full risk analysis
        
        Shows:
        - Parsed command details
        - Risk level with icon
        - Affected files/resources
        - Clear approve/reject prompt
        """
        command = result['command']
        risk = result['risk']
        
        # Risk icon and color
        risk_icon = risk_classifier.get_risk_icon(risk)
        
        # Build prompt
        lines = []
        lines.append("\n" + "="*60)
        lines.append("AI PARSED COMMAND - APPROVAL REQUIRED")
        lines.append("="*60)
        
        lines.append(f"\n📝 Your input:")
        lines.append(f"   (not shown - use command history)")
        
        lines.append(f"\n🤖 AI understood:")
        lines.append(f"   Module: {command['module']}")
        lines.append(f"   Operation: {command['operation']}")
        lines.append(f"   Args: {command['args']}")
        lines.append(f"   Confidence: {command['confidence']:.0%}")
        
        lines.append(f"\n{risk_icon} Risk Level: {risk.name}")
        
        # Show affected files
        if 'filename' in command['args']:
            lines.append(f"\n📁 Affected files:")
            lines.append(f"   - {command['args']['filename']}")
        
        lines.append("\n" + "="*60)
        lines.append("Proceed with this command? (y/n): ")
        
        return '\n'.join(lines)
    
    def check_availability(self) -> bool:
        """Check if AI parsing is available"""
        return ollama_client.check_availability()


# Global instance (created when workspace known)
def create_ai_handler(workspace: Path) -> AICommandHandler:
    """Factory function to create AI handler"""
    return AICommandHandler(workspace)
