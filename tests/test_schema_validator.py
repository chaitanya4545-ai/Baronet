"""
Unit tests for Schema Validator
Tests deterministic validation logic
"""
import pytest
from core.schema_validator import schema_validator, CommandSchema


class TestSchemaValidator:
    """Test deterministic command validation"""
    
    def test_valid_create_command(self):
        """Valid create command should pass"""
        command = {
            'module': 'file',
            'operation': 'create',
            'args': {'filename': 'test.txt', 'content': 'hello'},
            'confidence': 0.95
        }
        
        valid, error = schema_validator.validate(command)
        assert valid is True
        assert error is None
    
    def test_missing_required_field(self):
        """Missing required field should fail"""
        command = {
            'module': 'file',
            # missing 'operation'
            'args': {'filename': 'test.txt'},
            'confidence': 0.9
        }
        
        valid, error = schema_validator.validate(command)
        assert valid is False
        assert 'Missing required field' in error
    
    def test_unknown_module(self):
        """Unknown module should fail"""
        command = {
            'module': 'hacker',
            'operation': 'pwn',
            'args': {},
            'confidence': 0.9
        }
        
        valid, error = schema_validator.validate(command)
        assert valid is False
        assert 'Unknown module' in error
    
    def test_low_confidence(self):
        """Low confidence should fail"""
        command = {
            'module': 'file',
            'operation': 'create',
            'args': {'filename': 'test.txt'},
            'confidence': 0.5  # Below 0.7 threshold
        }
        
        valid, error = schema_validator.validate(command)
        assert valid is False
        assert 'Confidence' in error
    
    def test_wildcard_delete_blocked(self):
        """Wildcard + delete should fail"""
        command = {
            'module': 'file',
            'operation': 'delete',
            'args': {'filename': '*.txt'},
            'confidence': 0.95
        }
        
        valid, error = schema_validator.validate(command)
        assert valid is False
        assert 'Wildcard' in error
    
    def test_path_traversal_blocked(self):
        """Path traversal should fail"""
        command = {
            'module': 'file',
            'operation': 'read',
            'args': {'filename': '../../../etc/passwd'},
            'confidence': 0.95
        }
        
        valid, error = schema_validator.validate(command)
        assert valid is False
        assert 'traversal' in error.lower()
    
    def test_plan_too_many_steps(self):
        """Plan with too many steps should fail"""
        steps = [
            {'module': 'file', 'operation': 'create', 'args': {'filename': f'test{i}.txt'}, 'confidence': 0.9}
            for i in range(25)  # Exceeds MAX_PLAN_STEPS (20)
        ]
        
        valid, error = schema_validator.validate_plan(steps)
        assert valid is False
        assert 'max is 20' in error
    
    def test_plan_suspicious_delete_count(self):
        """Plan with too many deletes should fail"""
        steps = [
            {'module': 'file', 'operation': 'delete', 'args': {'filename': f'test{i}.txt'}, 'confidence': 0.9}
            for i in range(15)  # More than 10 deletes
        ]
        
        valid, error = schema_validator.validate_plan(steps)
        assert valid is False
        assert 'delete operations (suspicious)' in error


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
