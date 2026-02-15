"""
Baronet Multi-Step Planner
Generates and validates multi-step automation plans
CRITICAL: Plans go through ALL safety validators
"""
from typing import List, Dict, Any, Optional, Tuple
from pathlib import Path

from core.logger import log
from core.ollama_client import ollama_client, OllamaUnavailable, ParsingError
from core.schema_validator import schema_validator
from core.semantic_guard import semantic_guard
from core.risk_classifier import risk_classifier, RiskLevel
from core.dependency_validator import create_dependency_validator


class MultiStepPlanner:
    """Plans and validates multi-step automation tasks"""
    
    def __init__(self, workspace: Path):
        self.workspace = workspace
        self.dependency_validator = create_dependency_validator(workspace)
        self.max_plan_steps = 20
    
    def create_plan(self, user_goal: str) -> Dict[str, Any]:
        """
        Create multi-step plan from user goal
        
        Args:
            user_goal: Natural language description of complex task
        
        Returns:
            {
                'steps': List[Dict],  # Parsed commands
                'safe': bool,
                'overall_risk': RiskLevel,
                'validation_errors': List[str],
                'summary': str
            }
        """
        result = {
            'steps': [],
            'safe': False,
            'overall_risk': RiskLevel.MODERATE,
            'validation_errors': [],
            'summary': ''
        }
        
        # Step 1: Generate plan using AI
        try:
            plan_steps = self._generate_plan_steps(user_goal)
        except (OllamaUnavailable, ParsingError) as e:
            result['validation_errors'].append(f"Plan generation failed: {e}")
            return result
        
        if not plan_steps:
            result['validation_errors'].append("No steps generated")
            return result
        
        result['steps'] = plan_steps
        
        # Step 2: Validate each step through schema validator
        for i, step in enumerate(plan_steps):
            valid, error = schema_validator.validate(step)
            if not valid:
                result['validation_errors'].append(f"Step {i+1} schema error: {error}")
        
        if result['validation_errors']:
            return result
        
        # Step 3: Check semantic safety for entire plan
        safe, reason = semantic_guard.check_plan(plan_steps, user_goal)
        if not safe:
            result['validation_errors'].append(f"Semantic check failed: {reason}")
            return result
        
        # Step 4: Classify overall plan risk
        plan_risk = risk_classifier.classify_plan(plan_steps)
        result['overall_risk'] = plan_risk['overall_risk']
        result['risk_details'] = plan_risk
        
        # Step 5: Validate dependencies
        valid, error = self.dependency_validator.validate_plan(plan_steps)
        if not valid:
            result['validation_errors'].append(f"Dependency error: {error}")
            return result
        
        # Step 6: Check sequencing
        valid, error = self.dependency_validator.check_plan_sequencing(plan_steps)
        if not valid:
            result['validation_errors'].append(f"Sequencing error: {error}")
            return result
        
        # All checks passed!
        result['safe'] = True
        result['summary'] = self._generate_plan_summary(plan_steps, plan_risk)
        
        return result
    
    def _generate_plan_steps(self, user_goal: str) -> List[Dict[str, Any]]:
        """
        Use AI to break down goal into steps
        
        This is a simplified version - in production, we'd use a more
        sophisticated prompting strategy with examples
        """
        # For now, since we only have file operations, we'll use the
        # single-command parser and let the user specify multi-step manually
        # TODO: Implement multi-step plan generation with AI
        
        # Placeholder: parse as single command
        try:
            parsed = ollama_client.parse_command(user_goal)
            return [parsed]
        except Exception as e:
            log.error(f"Plan generation error: {e}")
            return []
    
    def _generate_plan_summary(self, steps: List[Dict], risk_details: Dict) -> str:
        """Generate human-readable plan summary"""
        lines = []
        lines.append(f"Plan with {len(steps)} step(s):")
        
        for i, step in enumerate(steps):
            op = step['operation']
            args_str = ', '.join(f"{k}={v}" for k, v in step['args'].items())
            lines.append(f"  {i+1}. {op}({args_str})")
        
        lines.append(f"\nOverall Risk: {risk_details['risk_name']}")
        lines.append(f"Affected Files: {risk_details['affected_files']}")
        lines.append(f"Dangerous Operations: {risk_details['dangerous_operations']}")
        
        return '\n'.join(lines)
    
    def execute_plan(self, plan_steps: List[Dict[str, Any]], 
                    on_step_start=None, on_step_complete=None) -> Dict[str, Any]:
        """
        Execute validated plan with logging and rollback support
        
        Args:
            plan_steps: Validated list of commands
            on_step_start: Callback(step_num, step) before each step
            on_step_complete: Callback(step_num, result) after each step
        
        Returns:
            {
                'success': bool,
                'completed_steps': int,
                'results': List[Dict],
                'error': Optional[str]
            }
        """
        from core.baronet import baronet
        
        execution_result = {
            'success': False,
            'completed_steps': 0,
            'results': [],
            'error': None
        }
        
        for i, step in enumerate(plan_steps):
            step_num = i + 1
            
            # Notify step start
            if on_step_start:
                on_step_start(step_num, step)
            
            log.info(f"Executing step {step_num}/{len(plan_steps)}: {step['operation']}")
            
            # Execute step
            try:
                result = baronet.execute(step)
                execution_result['results'].append(result)
                
                # Notify step complete
                if on_step_complete:
                    on_step_complete(step_num, result)
                
                # Check if step failed
                if not result.get('success'):
                    execution_result['error'] = f"Step {step_num} failed: {result.get('error')}"
                    log.error(execution_result['error'])
                    return execution_result
                
                execution_result['completed_steps'] += 1
                
            except Exception as e:
                execution_result['error'] = f"Step {step_num} exception: {e}"
                log.error(execution_result['error'])
                return execution_result
        
        # All steps completed
        execution_result['success'] = True
        return execution_result


# Factory function
def create_planner(workspace: Path) -> MultiStepPlanner:
    """Create planner instance"""
    return MultiStepPlanner(workspace)
