"""
Baronet Safety System
Permission checks, rate limiting, and safety guardrails
"""
from enum import IntEnum
from typing import Callable, Optional
from datetime import datetime, timedelta
from collections import defaultdict
import json
from pathlib import Path


class PermissionLevel(IntEnum):
    """Permission levels for operations"""
    SAFE = 0        # Read-only, logging, status
    MODERATE = 1    # File ops in workspace only
    ELEVATED = 2    # System commands, web automation
    DANGEROUS = 3   # Delete operations, registry, network


class SafetyGuard:
    """Safety system for Baronet operations - HARDENED VERSION"""
    
    # HARDENING: Watchdog and execution limits
    MAX_EXECUTION_TIME = 300  # 5 minutes per command
    MAX_RECURSIVE_DEPTH = 5   # Prevent runaway recursion
    
    def __init__(self, config_path: str = "config/settings.json"):
        self.config_path = Path(config_path)
        self.load_config()
        
        # Rate limiting tracking
        self.operation_counts = defaultdict(list)
        
        # Emergency stop flag  
        self.emergency_stop = False
        
        # HARDENING: Execution tracking
        self.current_executions = {}  # task_id -> start_time
        self.execution_depth = 0      # Current recursion depth
    
    def load_config(self):
        """Load safety configuration - HARDENED with recovery"""
        try:
            if self.config_path.exists():
                with open(self.config_path, 'r') as f:
                    config = json.load(f)
                    self.max_auto_permission = config['safety']['max_auto_permission']
                    self.require_approval_for = config['safety']['require_approval_for']
                    self.rate_limits = config['rate_limits']
            else:
                # Create default config if missing
                self._create_default_config()
                
        except (json.JSONDecodeError, KeyError, FileNotFoundError) as e:
            # HARDENING: Config corrupted or invalid - use safe defaults and recover
            print(f"⚠️  Config error ({e}), using safe defaults and recovering...")
            self._create_default_config()
    
    def _create_default_config(self):
        """Create safe default configuration"""
        self.max_auto_permission = 1  # MODERATE
        self.require_approval_for = ['delete', 'system_command', 'network_request']
        self.rate_limits = {
            'file_operations_per_minute': 100,
            'max_task_depth': 10,
            'max_runtime_seconds': 3600
        }
        
        # Try to save default config
        try:
            self.config_path.parent.mkdir(parents=True, exist_ok=True)
            config_data = {
                "version": "0.1.0-phase1",
                "safety": {
                    "max_auto_permission": self.max_auto_permission,
                    "require_approval_for": self.require_approval_for
                },
                "rate_limits": self.rate_limits
            }
            with open(self.config_path, 'w') as f:
                json.dump(config_data, f, indent=2)
            print(f"✓ Created default config at {self.config_path}")
        except Exception as e:
            print(f"⚠️  Could not save config: {e}. Using in-memory defaults.")
    
    def check_permission(self, operation: str, permission_level: PermissionLevel) -> tuple[bool, Optional[str]]:
        """
        Check if operation is allowed
        Returns: (allowed: bool, reason: Optional[str])
        """
        # Emergency stop check
        if self.emergency_stop:
            return False, "EMERGENCY STOP ACTIVATED"
        
        # Permission level check
        if permission_level > self.max_auto_permission:
            return False, f"Permission level {permission_level.name} exceeds auto-approval limit"
        
        # Specific operation checks
        if operation in self.require_approval_for:
            return False, f"Operation '{operation}' requires manual approval"
        
        # Rate limiting
        if not self.check_rate_limit(operation):
            return False, f"Rate limit exceeded for {operation}"
        
        return True, None
    
    def check_rate_limit(self, operation: str) -> bool:
        """Check if operation is within rate limits"""
        now = datetime.now()
        one_minute_ago = now - timedelta(minutes=1)
        
        # Clean old entries
        self.operation_counts[operation] = [
            ts for ts in self.operation_counts[operation]
            if ts > one_minute_ago
        ]
        
        # Check limit
        limit = self.rate_limits.get('file_operations_per_minute', 100)
        if len(self.operation_counts[operation]) >= limit:
            return False
        
        # Record this operation
        self.operation_counts[operation].append(now)
        return True
    
    def start_execution(self, task_id: str) -> tuple[bool, Optional[str]]:
        """HARDENING: Start tracking command execution"""
        # Check recursion depth
        if self.execution_depth >= self.MAX_RECURSIVE_DEPTH:
            return False, f"Max recursion depth ({self.MAX_RECURSIVE_DEPTH}) exceeded"
        
        self.execution_depth += 1
        self.current_executions[task_id] = datetime.now()
        return True, None
    
    def end_execution(self, task_id: str) -> float:
        """HARDENING: End tracking and return execution time (BUG FIX: Always decrement depth)"""
        execution_time = 0.0
        
        if task_id in self.current_executions:
            start_time = self.current_executions.pop(task_id)
            execution_time = (datetime.now() - start_time).total_seconds()
        
        # BUG FIX: ALWAYS decrement depth, even if task_id not found
        # This prevents depth leaks on exceptions
        self.execution_depth = max(0, self.execution_depth - 1)
        
        return execution_time
    
    def check_execution_timeout(self, task_id: str) -> bool:
        """HARDENING: Check if execution has exceeded time limit"""
        if task_id in self.current_executions:
            start_time = self.current_executions[task_id]
            elapsed = (datetime.now() - start_time).total_seconds()
            if elapsed > self.MAX_EXECUTION_TIME:
                return True
        return False
    
    def safe_execute(self, 
                     operation: str, 
                     permission_level: PermissionLevel, 
                     func: Callable, 
                     *args, 
                     **kwargs):
        """
        Safely execute an operation with permission checks
        """
        # Check permission
        allowed, reason = self.check_permission(operation, permission_level)
        
        if not allowed:
            return {
                'success': False,
                'error': f'Operation blocked: {reason}',
                'permission_required': True
            }
        
        # Execute the operation
        try:
            result = func(*args, **kwargs)
            return {
                'success': True,
                'result': result,
                'operation': operation,
                'timestamp': datetime.now().isoformat()
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'operation': operation,
                'timestamp': datetime.now().isoformat()
            }
    
    def activate_emergency_stop(self):
        """Activate emergency stop - blocks all operations"""
        self.emergency_stop = True
    
    def deactivate_emergency_stop(self):
        """Deactivate emergency stop"""
        self.emergency_stop = False
    
    def get_status(self) -> dict:
        """Get current safety status - ENHANCED"""
        return {
            'emergency_stop': self.emergency_stop,
            'max_auto_permission': PermissionLevel(self.max_auto_permission).name,
            'operations_last_minute': {
                op: len(times) for op, times in self.operation_counts.items()
            },
            'active_executions': len(self.current_executions),
            'recursion_depth': self.execution_depth
        }


# Global safety guard
safety = SafetyGuard()
