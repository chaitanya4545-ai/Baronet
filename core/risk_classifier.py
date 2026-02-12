"""
OpenClaw Risk Classifier
Rule-based risk assessment - NOT AI judgment
CRITICAL: AI cannot judge its own risk level
"""
from typing import Dict, Any, List
from enum import Enum


class RiskLevel(Enum):
    """Risk levels for operations and plans"""
    SAFE = 0        # Read-only, no modifications
    MODERATE = 1    # Create, modify in workspace
    ELEVATED = 2    # Batch operations, system commands
    DANGEROUS = 3   # Delete, external access, wildcards


class PlanRiskClassifier:
    """Deterministic risk classification based on rules"""
    
    # Operation risk mapping
    OPERATION_RISKS = {
        # SAFE operations
        'read': RiskLevel.SAFE,
        'list_files': RiskLevel.SAFE,
        'get_info': RiskLevel.SAFE,
        'info': RiskLevel.SAFE,
        'list': RiskLevel.SAFE,
        
        # MODERATE operations
        'create': RiskLevel.MODERATE,
        'write': RiskLevel.MODERATE,
        'move': RiskLevel.MODERATE,
        'copy': RiskLevel.MODERATE,
        'rename': RiskLevel.MODERATE,
        
        # DANGEROUS operations
        'delete': RiskLevel.DANGEROUS,
        'remove': RiskLevel.DANGEROUS,
        'unlink': RiskLevel.DANGEROUS,
        'drop': RiskLevel.DANGEROUS,
        'purge': RiskLevel.DANGEROUS,
    }
    
    def __init__(self):
        self.BATCH_THRESHOLD = 10
        self.MASS_THRESHOLD = 100
    
    def classify_operation(self, operation: str, args: Dict[str, Any]) -> RiskLevel:
        """
        Classify single operation risk level
        
        Returns: RiskLevel enum
        """
        # Get base risk from operation
        base_risk = self.OPERATION_RISKS.get(operation, RiskLevel.MODERATE)
        
        # Escalate based on args
        args_str = str(args).lower()
        
        # 1. Wildcard = DANGEROUS
        if '*' in args_str or '?' in args_str:
            return RiskLevel.DANGEROUS
        
        # 2. Path traversal = DANGEROUS
        if '..' in args_str or '~' in args_str:
            return RiskLevel.DANGEROUS
        
        # 3. Recursive operations = ELEVATED
        if args.get('recursive', False) or args.get('recurse', False):
            return max(base_risk, RiskLevel.ELEVATED)
        
        # 4. External paths = ELEVATED
        if self._has_external_path(args):
            return max(base_risk, RiskLevel.ELEVATED)
        
        return base_risk
    
    def classify_plan(self, plan_steps: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Classify entire plan and return risk profile
        
        Returns: {
            'overall_risk': RiskLevel,
            'affected_files': int (estimate),
            'dangerous_operations': int,
            'irreversible_count': int,
            'estimated_time': float (seconds),
            'requires_backup': bool
        }
        """
        # Count operations by risk
        risk_counts = {level: 0 for level in RiskLevel}
        dangerous_ops = []
        total_files_affected = 0
        
        for step in plan_steps:
            operation = step.get('operation', '')
            args = step.get('args', {})
            
            risk = self.classify_operation(operation, args)
            risk_counts[risk] += 1
            
            if risk == RiskLevel.DANGEROUS:
                dangerous_ops.append(operation)
            
            # Estimate affected files
            if '*' in str(args):
                total_files_affected += 50  # Wildcard estimate
            else:
                total_files_affected += 1
        
        # Determine overall risk
        if risk_counts[RiskLevel.DANGEROUS] > 0:
            overall_risk = RiskLevel.DANGEROUS
        elif risk_counts[RiskLevel.ELEVATED] > 0:
            overall_risk = RiskLevel.ELEVATED
        elif risk_counts[RiskLevel.MODERATE] > 0:
            overall_risk = RiskLevel.MODERATE
        else:
            overall_risk = RiskLevel.SAFE
        
        # Escalate if batch operations
        if total_files_affected > self.MASS_THRESHOLD:
            overall_risk = RiskLevel.DANGEROUS
        elif total_files_affected > self.BATCH_THRESHOLD:
            overall_risk = max(overall_risk, RiskLevel.ELEVATED)
        
        # Estimate runtime (very rough)
        estimated_time = len(plan_steps) * 0.5  # 0.5s per step baseline
        if total_files_affected > 10:
            estimated_time += total_files_affected * 0.1
        
        return {
            'overall_risk': overall_risk,
            'risk_name': overall_risk.name,
            'affected_files': total_files_affected,
            'dangerous_operations': len(dangerous_ops),
            'irreversible_count': risk_counts[RiskLevel.DANGEROUS],
            'estimated_time': round(estimated_time, 1),
            'requires_backup': len(dangerous_ops) > 0,
            'step_count': len(plan_steps),
            'risk_breakdown': {
                'safe': risk_counts[RiskLevel.SAFE],
                'moderate': risk_counts[RiskLevel.MODERATE],
                'elevated': risk_counts[RiskLevel.ELEVATED],
                'dangerous': risk_counts[RiskLevel.DANGEROUS]
            }
        }
    
    def _has_external_path(self, args: Dict[str, Any]) -> bool:
        """Check if args reference paths outside workspace"""
        args_str = str(args).lower()
        
        # Windows system paths
        system_paths = [
            'c:\\windows', 'c:\\program files', 'c:\\system',
            'c:/windows', 'c:/program files', 'c:/system'
        ]
        
        for path in system_paths:
            if path in args_str:
                return True
        
        # Absolute path indicators
        if args_str.count(':\\') > 0 or args_str.count(':/') > 0:
            # Has drive letter
            if 'c:\\openclaw' not in args_str:
                return True
        
        return False
    
    def get_risk_icon(self, risk: RiskLevel) -> str:
        """Get emoji icon for risk level"""
        icons = {
            RiskLevel.SAFE: '🟢',
            RiskLevel.MODERATE: '🟡',
            RiskLevel.ELEVATED: '🟠',
            RiskLevel.DANGEROUS: '🔴'
        }
        return icons.get(risk, '⚪')
    
    def get_risk_color(self, risk: RiskLevel) -> str:
        """Get color name for rich console"""
        colors = {
            RiskLevel.SAFE: 'green',
            RiskLevel.MODERATE: 'yellow',
            RiskLevel.ELEVATED: 'orange1',
            RiskLevel.DANGEROUS: 'red'
        }
        return colors.get(risk, 'white')


# Global instance
risk_classifier = PlanRiskClassifier()
