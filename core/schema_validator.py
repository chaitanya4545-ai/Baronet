"""
OpenClaw Schema Validator
Deterministic validation layer - NO AI judgment
CRITICAL: Confidence is NOT safety
"""
from typing import Optional, Dict, Any, List
from pathlib import Path
import re


class CommandSchema:
    """Deterministic command validation"""
    
    # Known modules and their operations
    VALID_MODULES = {
        'file': ['create', 'read', 'write', 'delete', 'list_files', 'get_info'],
        # Future: 'system', 'web', 'data'
    }
    
    # Operations that are inherently dangerous
    DANGEROUS_OPERATIONS = {'delete', 'remove', 'unlink', 'drop', 'purge'}
    
    # Patterns that escalate risk
    WILDCARD_PATTERNS = ['*', '**', '.*', '?']
    TRAVERSAL_PATTERNS = ['..', '~', '../', '..\\']
    
    def __init__(self):
        self.MIN_CONFIDENCE = 0.7
        self.MAX_PLAN_STEPS = 20
    
    def validate(self, parsed_command: dict) -> tuple[bool, Optional[str]]:
        """
        Deterministic validation - rejects if ANY check fails
        
        Args:
            parsed_command: {
                'module': str,
                'operation': str,
                'args': dict,
                'confidence': float,
                'intent': str (optional),
                'risk_hint': str (optional)
            }
        
        Returns:
            (valid: bool, error_reason: Optional[str])
        """
        # 1. Check structure
        if not isinstance(parsed_command, dict):
            return False, "Command must be dict"
        
        # 2. Check required fields
        required = ['module', 'operation', 'args']
        for field in required:
            if field not in parsed_command:
                return False, f"Missing required field: {field}"
        
        # 3. Check module exists
        module = parsed_command['module']
        if module not in self.VALID_MODULES:
            return False, f"Unknown module: {module}"
        
        # 4. Check operation exists in module
        operation = parsed_command['operation']
        if operation not in self.VALID_MODULES[module]:
            return False, f"Unknown operation '{operation}' for module '{module}'"
        
        # 5. Check args is dict
        args = parsed_command.get('args', {})
        if not isinstance(args, dict):
            return False, "Args must be dict"
        
        # 6. Check confidence level
        confidence = parsed_command.get('confidence', 0.0)
        if confidence < self.MIN_CONFIDENCE:
            return False, f"Confidence {confidence:.2f} below minimum {self.MIN_CONFIDENCE}"
        
        # 7. Check for wildcard + dangerous combo
        if operation in self.DANGEROUS_OPERATIONS:
            args_str = str(args)
            for wildcard in self.WILDCARD_PATTERNS:
                if wildcard in args_str:
                    return False, f"Wildcard '{wildcard}' not allowed with {operation}"
        
        # 8. Check for path traversal
        args_str = str(args)
        for traversal in self.TRAVERSAL_PATTERNS:
            if traversal in args_str:
                # Will be caught by file_ops validation, but catch early
                return False, f"Path traversal pattern '{traversal}' detected"
        
        # 9. Validate args completeness (module-specific)
        valid_args, error = self._validate_module_args(module, operation, args)
        if not valid_args:
            return False, error
        
        return True, None
    
    def _validate_module_args(self, module: str, operation: str, args: dict) -> tuple[bool, Optional[str]]:
        """Module-specific arg validation"""
        
        if module == 'file':
            # All file operations need 'filename' or 'directory'
            if operation in ['create', 'read', 'write', 'delete', 'get_info']:
                if 'filename' not in args:
                    return False, f"Operation '{operation}' requires 'filename' arg"
            
            elif operation == 'list_files':
                # directory is optional, defaults to '.'
                pass
            
            # Check content for create/write
            if operation in ['create', 'write']:
                # content can be empty string, but should exist
                if 'content' not in args and operation == 'write':
                    return False, "Operation 'write' requires 'content' arg"
        
        return True, None
    
    def validate_plan(self, plan_steps: List[dict]) -> tuple[bool, Optional[str]]:
        """Validate entire multi-step plan"""
        
        # 1. Check step count
        if len(plan_steps) > self.MAX_PLAN_STEPS:
            return False, f"Plan has {len(plan_steps)} steps, max is {self.MAX_PLAN_STEPS}"
        
        # 2. Check each step individually
        for i, step in enumerate(plan_steps):
            valid, error = self.validate(step)
            if not valid:
                return False, f"Step {i+1} invalid: {error}"
        
        # 3. Check for suspicious patterns
        delete_count = sum(1 for step in plan_steps if step.get('operation') == 'delete')
        if delete_count > 10:
            return False, f"Plan contains {delete_count} delete operations (suspicious)"
        
        return True, None


# Global instance
schema_validator = CommandSchema()
