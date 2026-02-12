"""
OpenClaw Semantic Guard
Prevents implicit dangerous expansions and prompt injections
CRITICAL: Block innocent-looking dangerous commands
"""
from typing import Dict, Any, List, Optional, Tuple


class SemanticGuard:
    """Prevent semantic prompt injection and implicit expansions"""
    
    # System paths that should NEVER be accessed implicitly
    FORBIDDEN_IMPLICIT_PATHS = [
        # Windows
        'C:\\Windows', 'C:\\Program Files', 'C:\\Program Files (x86)',
        'C:\\System', 'C:\\ProgramData', 'C:\\Users\\All Users',
        # Unix-style (future-proofing)
        '/', '/etc', '/usr', '/sys', '/bin', '/sbin', '/root',
        # Registry
        'HKEY_', 'HKLM', 'HKCU', 'registry',
        # Network
        '\\\\', 'smb://', 'ftp://', 'http://', 'https://'
    ]
    
    # Keywords that are dangerous when combined with destructive operations
    DANGEROUS_KEYWORDS_WITH_DELETE = [
        'system', 'all', 'everything', 'cleanup', 'purge',
        'clear', 'wipe', 'remove all', 'delete all',
        'unnecessary', 'unused', 'temporary', 'cache'
    ]
    
    # Keywords that suggest scope creep
    SCOPE_CREEP_KEYWORDS = [
        'but first', 'before that', 'also', 'additionally',
        'while you\'re at it', 'scan for', 'check for',
        'find and', 'search for'
    ]
    
    def __init__(self):
        self.workspace_path = 'C:\\OpenClaw\\workspace'
    
    def check_command(self, command: Dict[str, Any], user_input: str) -> Tuple[bool, Optional[str]]:
        """
        Check single command for semantic injection
        
        Args:
            command: Parsed command dict
            user_input: Original user input string
        
        Returns:
            (safe: bool, reason: Optional[str])
        """
        operation = command.get('operation', '')
        args = command.get('args', {})
        args_str = str(args).lower()
        user_input_lower = user_input.lower()
        
        # 1. Check for forbidden implicit paths
        for forbidden_path in self.FORBIDDEN_IMPLICIT_PATHS:
            if forbidden_path.lower() in args_str:
                # Was it explicitly mentioned by user?
                if forbidden_path.lower() not in user_input_lower:
                    return False, f"Command tries to access '{forbidden_path}' implicitly (not in user request)"
        
        # 2. Check dangerous keyword combos with delete
        if operation in ['delete', 'remove', 'unlink', 'purge']:
            for keyword in self.DANGEROUS_KEYWORDS_WITH_DELETE:
                if keyword in user_input_lower:
                    return False, f"Dangerous delete with ambiguous keyword '{keyword}'"
        
        # 3. Check for scope creep (but first, also, etc.)
        for creep in self.SCOPE_CREEP_KEYWORDS:
            if creep in user_input_lower:
                return False, f"Detected scope creep keyword '{creep}' - possible injection"
        
        # 4. Check for implicit wildcards
        if '*' in args_str or '.*' in args_str:
            if '*' not in user_input and 'all' not in user_input_lower:
                return False, "Command uses wildcard not explicitly requested"
        
        return True, None
    
    def check_plan(self, plan_steps: List[Dict[str, Any]], user_input: str) -> Tuple[bool, Optional[str]]:
        """
        Check entire plan for semantic injection
        
        Returns:
            (safe: bool, reason: Optional[str])
        """
        # 1. Check each step individually
        for i, step in enumerate(plan_steps):
            safe, reason = self.check_command(step, user_input)
            if not safe:
                return False, f"Step {i+1}: {reason}"
        
        # 2. Check for suspicious step patterns
        # Pattern: "organize files" shouldn't become "scan system"
        operations = [step.get('operation', '') for step in plan_steps]
        
        # If user said "organize" but plan includes "delete"
        if 'organize' in user_input.lower() or 'sort' in user_input.lower():
            if any(op in ['delete', 'remove'] for op in operations):
                # Unless user explicitly said "delete" or "remove"
                if 'delete' not in user_input.lower() and 'remove' not in user_input.lower():
                    return False, "Plan adds delete operations to organize request"
        
        # 3. Check step count proportionality
        # Simple request shouldn't become 20-step plan
        simple_keywords = ['create', 'read', 'list', 'show', 'get']
        if any(kw in user_input.lower() for kw in simple_keywords):
            if len(plan_steps) > 5:
                return False, f"Simple request expanded to {len(plan_steps)} steps (suspicious)"
        
        return True, None
    
    def sanitize_user_input(self, user_input: str) -> str:
        """
        Sanitize user input - BLOCK malicious patterns
        
        Returns input or '[BLOCKED]: reason'
        """
        # Check for shell command chaining
        if any(char in user_input for char in [';', '&&', '||', '|']):
            return f"[BLOCKED]: Shell metacharacters detected"
        
        # Check for nested command injection
        nested_patterns = [
            'but first',
            'and also',
            'then ',
            'while you',
            'after that',
           'before',
            'also ',
        ]
        
        user_lower = user_input.lower()
        for pattern in nested_patterns:
            if pattern in user_lower:
                # Check if it's followed by a dangerous word
                if any(danger in user_lower for danger in ['delete', 'remove', 'clean', 'scan', 'execute', 'run']):
                    return f"[BLOCKED]: Nested command injection detected ('{pattern}')"
        
        # Check for explicit injection patterns
        injection_patterns = [
            'ignore previous instructions',
            'ignore all previous',
            'disregard previous',
            'new instructions:',
            'system:',
            'override:',
            'admin mode',
            'debug mode'
        ]
        
        for pattern in injection_patterns:
            if pattern in user_input.lower():
                return f'[BLOCKED]: Injection pattern detected'
        
        return user_input
    
    def _has_scope_creep(self, user_input: str) -> bool:
        """Check if input has scope creep keywords"""
        user_lower = user_input.lower()
        for creep in self.SCOPE_CREEP_KEYWORDS:
            if creep in user_lower:
                return True
        return False
    
    def _has_dangerous_keywords_with_delete(self, user_input: str) -> bool:
        """Check if input has dangerous keywords with delete"""
        user_lower = user_input.lower()
        has_delete = any(word in user_lower for word in ['delete', 'remove', 'clean'])
        if not has_delete:
            return False
        
        for keyword in self.DANGEROUS_KEYWORDS_WITH_DELETE:
            if keyword in user_lower:
                return True
        return False
    
    def explain_block(self, reason: str) -> str:
        """
        Generate user-friendly explanation for why command was blocked
        """
        explanations = {
            'implicit': "🛡️  The AI tried to access system files you didn't mention. Blocked for safety.",
            'scope creep': "🛡️  The AI tried to do extra tasks beyond your request. Blocked for safety.",
            'dangerous keyword': "🛡️  Ambiguous command detected. Please be specific about what to delete.",
            'wildcard': "🛡️  The AI added a wildcard operation you didn't request. Blocked for safety.",
            'delete expansion': "🛡️  The AI tried to add delete operations to organize request. Blocked for safety.",
            'suspicious': "🛡️  The command seems more complex than expected. Blocked for review."
        }
        
        # Find matching explanation
        for key, explanation in explanations.items():
            if key in reason.lower():
                return explanation
        
        return f"🛡️  Semantic guard blocked: {reason}"


# Global instance
semantic_guard = SemanticGuard()
