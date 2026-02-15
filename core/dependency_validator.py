"""
Baronet Dependency Validator
Checks if operations have unmet prerequisites
CRITICAL: Prevents logical contradictions in AI plans
"""
from typing import Dict, Any, List, Optional, Tuple
from pathlib import Path


class DependencyValidator:
    """Validates operation dependencies and prerequisites"""
    
    def __init__(self, workspace: Path):
        self.workspace = workspace
    
    def validate_command(self, command: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
        """
        Check if single command has met prerequisites
        
        Args:
            command: Parsed command dict with module, operation, args
        
        Returns:
            (valid: bool, error_reason: Optional[str])
        """
        module = command.get('module')
        operation = command.get('operation')
        args = command.get('args', {})
        
        if module == 'file':
            return self._validate_file_operation(operation, args)
        
        # Future: other modules
        return True, None
    
    def _validate_file_operation(self, operation: str, args: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
        """Validate file operation dependencies"""
        
        filename = args.get('filename', args.get('directory', ''))
        if not filename:
            return True, None  # Will be caught by schema validator
        
        # Resolve path
        target_path = self.workspace / filename
        exists = target_path.exists()
        
        # Operation-specific checks
        if operation == 'read':
            if not exists:
                return False, f"Cannot read '{filename}': file does not exist"
        
        elif operation == 'write':
            if not exists:
                return False, f"Cannot write to '{filename}': file does not exist (use 'create' first)"
        
        elif operation == 'delete':
            if not exists:
                return False, f"Cannot delete '{filename}': file does not exist"
        
        elif operation == 'get_info':
            if not exists:
                return False, f"Cannot get info for '{filename}': file does not exist"
        
        elif operation == 'create':
            if exists:
                return False, f"Cannot create '{filename}': file already exists (use 'write' to modify)"
        
        # list_files doesn't require file to exist
        
        return True, None
    
    def validate_plan(self, plan_steps: List[Dict[str, Any]]) -> Tuple[bool, Optional[str]]:
        """
        Validate entire plan for dependency issues
        
        Checks:
        - Step-by-step state simulation
        - Each step's prerequisites based on previous steps
        - No contradictory operations
        
        Returns:
            (valid: bool, error_reason: Optional[str])
        """
        # Simulate workspace state
        simulated_files = set()
        
        # Get actual workspace state
        if self.workspace.exists():
            for item in self.workspace.iterdir():
                if item.is_file():
                    simulated_files.add(item.name)
        
        # Check each step against simulated state
        for i, step in enumerate(plan_steps):
            module = step.get('module')
            operation = step.get('operation')
            args = step.get('args', {})
            
            if module != 'file':
                continue  # Skip non-file operations for now
            
            filename = args.get('filename', '')
            if not filename:
                continue
            
            # Check prerequisites based on simulated state
            exists_in_sim = filename in simulated_files
            
            if operation == 'read' and not exists_in_sim:
                return False, f"Step {i+1}: Cannot read '{filename}' - not created yet"
            
            elif operation == 'write' and not exists_in_sim:
                return False, f"Step {i+1}: Cannot write to '{filename}' - not created yet"
            
            elif operation == 'delete' and not exists_in_sim:
                return False, f"Step {i+1}: Cannot delete '{filename}' - already deleted or never created"
            
            elif operation == 'create' and exists_in_sim:
                return False, f"Step {i+1}: Cannot create '{filename}' - already exists or created earlier"
            
            # Update simulated state
            if operation == 'create':
                simulated_files.add(filename)
            elif operation == 'delete':
                simulated_files.discard(filename)
        
        return True, None
    
    def check_plan_sequencing(self, plan_steps: List[Dict[str, Any]]) -> Tuple[bool, Optional[str]]:
        """
        Check if plan has proper operation sequencing
        
        Detects patterns like:
        - Create → Read → Delete (pointless)
        - Write → Delete (wasteful)
        - Multiple creates of same file
        """
        file_operations = {}  # filename -> list of operations
        
        for step in plan_steps:
            if step.get('module') != 'file':
                continue
            
            filename = step.get('args', {}).get('filename', '')
            operation = step.get('operation')
            
            if not filename:
                continue
            
            if filename not in file_operations:
                file_operations[filename] = []
            file_operations[filename].append(operation)
        
        # Check for suspicious patterns
        for filename, ops in file_operations.items():
            # Create → Delete with nothing in between
            if ops == ['create', 'delete']:
                return False, f"Suspicious: create then immediately delete '{filename}'"
            
            # Multiple creates
            if ops.count('create') > 1:
                return False, f"Invalid: multiple create operations for '{filename}'"
            
            # Multiple deletes
            if ops.count('delete') > 1:
                return False, f"Invalid: multiple delete operations for '{filename}'"
        
        return True, None


# Global instance (needs workspace to be set)
def create_dependency_validator(workspace: Path) -> DependencyValidator:
    """Factory function to create validator with workspace"""
    return DependencyValidator(workspace)
