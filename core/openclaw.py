"""
Baronet Core Controller
Main command processor and execution engine
HARDENED: Crash recovery, execution timing, watchdog
"""
from typing import Dict, Any
import json
from pathlib import Path
import uuid
import time

from core.logger import log
from core.safety import safety, PermissionLevel
from modules.file_ops import file_ops


class Baronet:
    """Central nervous system of Baronet automation - HARDENED VERSION"""
    
    def __init__(self):
        self.version = "0.1.0-phase1-hardened"
        self.modules = {
            'file': file_ops
        }
        log.info(f"Baronet v{self.version} initialized")
    
    def execute(self, command: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute a command - HARDENED with timing and error codes
        
        Args:
            command: {
                'module': 'file',
                'operation': 'create',
                'args': {...}
            }
        
        Returns:
            Result dictionary with execution_time and failure codes
        """
        task_id = str(uuid.uuid4())
        start_time = time.time()
        
        # HARDENING: Start execution tracking
        can_start, start_error = safety.start_execution(task_id)
        if not can_start:
            return {
                'success': False,
                'error': start_error,
                'code': 'SAFETY_BLOCKED'
            }
        
        try:
            module_name = command.get('module')
            operation = command.get('operation')
            args = command.get('args', {})
            
            log.debug(f"Executing: {module_name}.{operation}")
            
            # Validate module exists
            if module_name not in self.modules:
                error_msg = f"Unknown module: {module_name}"
                log.error(error_msg)
                return {
                    'success': False,
                    'error': error_msg,
                    'code': 'UNKNOWN_MODULE'
                }
            
            module = self.modules[module_name]
            
            # Validate operation exists
            if not hasattr(module, operation):
                error_msg = f"Unknown operation: {module_name}.{operation}"
                log.error(error_msg)
                return {
                    'success': False,
                    'error': error_msg,
                    'code': 'UNKNOWN_OPERATION'
                }
            
            # Execute operation
            func = getattr(module, operation)
            result = func(**args)
            
            # HARDENING: Add execution time
            execution_time = time.time() - start_time
            result['execution_time_ms'] = round(execution_time * 1000, 2)
            
            # Log command execution with timing
            status = "✓" if result.get('success') else "✗"
            error_code = result.get('code', '')
            code_str = f" [{error_code}]" if error_code else ""
            log.command(
                f"{module_name}.{operation}({args})",
                f"{status}{code_str} {result.get('error', 'OK')} ({execution_time*1000:.1f}ms)"
            )
            
            return result
            
        except Exception as e:
            execution_time = time.time() - start_time
            error_msg = f"Execution failed: {type(e).__name__}: {e}"
            log.error(error_msg)
            return {
                'success': False,
                'error': error_msg,
                'code': 'EXCEPTION',
                'exception_type': type(e).__name__,
                'execution_time_ms': round(execution_time * 1000, 2)
            }
        
        finally:
            # HARDENING: End execution tracking
            safety.end_execution(task_id)
    
    def get_status(self) -> Dict[str, Any]:
        """Get system status"""
        return {
            'version': self.version,
            'modules': list(self.modules.keys()),
            'safety': safety.get_status(),
            'workspace': str(file_ops.workspace)
        }
    
    def get_help(self) -> Dict[str, Any]:
        """Get available commands"""
        commands = {}
        
        for module_name, module in self.modules.items():
            module_commands = []
            for attr in dir(module):
                if not attr.startswith('_') and callable(getattr(module, attr)):
                    module_commands.append(attr)
            commands[module_name] = module_commands
        
        return {
            'version': self.version,
            'available_modules': commands
        }


# Global Baronet instance
baronet = Baronet()
