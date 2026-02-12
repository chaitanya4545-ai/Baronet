"""
Unit tests for Multi-Step Planner
Tests plan generation, validation, and execution
"""
import pytest
from pathlib import Path
import tempfile
import shutil
from core.planner import MultiStepPlanner


class TestMultiStepPlanner:
    """Test multi-step planning and execution"""
    
    @pytest.fixture
    def workspace(self):
        """Create temp workspace"""
        temp_dir = Path(tempfile.mkdtemp())
        yield temp_dir
        shutil.rmtree(temp_dir)
    
    @pytest.fixture
    def planner(self, workspace):
        """Create planner with temp workspace"""
        return MultiStepPlanner(workspace)
    
    def test_single_step_plan(self, planner):
        """Single-step plan should work"""
        plan_result = planner.create_plan("list all files")
        
        assert plan_result['safe'] is True
        assert len(plan_result['steps']) >= 1
        assert plan_result['overall_risk'].name == 'SAFE'
    
    def test_plan_validation_catches_dependency_error(self, planner):
        """Plan validation should catch dependency issues"""
        # Manually create invalid plan (read before create)
        steps = [
            {'module': 'file', 'operation': 'read', 'args': {'filename': 'test.txt'}, 'confidence': 0.9},
            {'module': 'file', 'operation': 'create', 'args': {'filename': 'test.txt'}, 'confidence': 0.9}
        ]
        
        # Validate through dependency validator directly
        from core.dependency_validator import create_dependency_validator
        validator = create_dependency_validator(planner.workspace)
        
        valid, error = validator.validate_plan(steps)
        assert valid is False
        assert 'not created yet' in error
    
    def test_plan_summary_generation(self, planner):
        """Plan summary should be readable"""
        plan_result = planner.create_plan("create a test file")
        
        if plan_result['safe']:
            summary = plan_result['summary']
            assert 'step' in summary.lower()
            assert 'risk' in summary.lower()


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
