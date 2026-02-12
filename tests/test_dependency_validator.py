"""
Unit tests for Dependency Validator
Tests prerequisite checking and plan simulation
"""
import pytest
from pathlib import Path
import tempfile
import shutil
from core.dependency_validator import DependencyValidator


class TestDependencyValidator:
    """Test operation dependency validation"""
    
    @pytest.fixture
    def workspace(self):
        """Create temp workspace"""
        temp_dir = Path(tempfile.mkdtemp())
        yield temp_dir
        shutil.rmtree(temp_dir)
    
    @pytest.fixture
    def validator(self, workspace):
        """Create validator with temp workspace"""
        return DependencyValidator(workspace)
    
    def test_read_nonexistent_file(self, validator):
        """Reading non-existent file should fail"""
        command = {
            'module': 'file',
            'operation': 'read',
            'args': {'filename': 'nonexistent.txt'}
        }
        
        valid, error = validator.validate_command(command)
        assert valid is False
        assert 'does not exist' in error
    
    def test_write_nonexistent_file(self, validator):
        """Writing to non-existent file should fail"""
        command = {
            'module': 'file',
            'operation': 'write',
            'args': {'filename': 'nonexistent.txt', 'content': 'test'}
        }
        
        valid, error = validator.validate_command(command)
        assert valid is False
        assert 'does not exist' in error
    
    def test_delete_nonexistent_file(self, validator):
        """Deleting non-existent file should fail"""
        command = {
            'module': 'file',
            'operation': 'delete',
            'args': {'filename': 'nonexistent.txt'}
        }
        
        valid, error = validator.validate_command(command)
        assert valid is False
        assert 'does not exist' in error
    
    def test_create_existing_file(self, validator, workspace):
        """Creating existing file should fail"""
        # Create file first
        (workspace / 'existing.txt').write_text('test')
        
        command = {
            'module': 'file',
            'operation': 'create',
            'args': {'filename': 'existing.txt', 'content': 'new'}
        }
        
        valid, error = validator.validate_command(command)
        assert valid is False
        assert 'already exists' in error
    
    def test_valid_create(self, validator):
        """Creating new file should succeed"""
        command = {
            'module': 'file',
            'operation': 'create',
            'args': {'filename': 'new.txt', 'content': 'test'}
        }
        
        valid, error = validator.validate_command(command)
        assert valid is True
    
    def test_plan_create_then_read(self, validator):
        """Plan: create → read should be valid"""
        plan = [
            {'module': 'file', 'operation': 'create', 'args': {'filename': 'test.txt'}},
            {'module': 'file', 'operation': 'read', 'args': {'filename': 'test.txt'}}
        ]
        
        valid, error = validator.validate_plan(plan)
        assert valid is True
    
    def test_plan_read_before_create(self, validator):
        """Plan: read → create should fail"""
        plan = [
            {'module': 'file', 'operation': 'read', 'args': {'filename': 'test.txt'}},
            {'module': 'file', 'operation': 'create', 'args': {'filename': 'test.txt'}}
        ]
        
        valid, error = validator.validate_plan(plan)
        assert valid is False
        assert 'not created yet' in error
    
    def test_plan_double_create(self, validator):
        """Plan with double create should fail"""
        plan = [
            {'module': 'file', 'operation': 'create', 'args': {'filename': 'test.txt'}},
            {'module': 'file', 'operation': 'create', 'args': {'filename': 'test.txt'}}
        ]
        
        valid, error = validator.validate_plan(plan)
        assert valid is False
        assert 'already exists' in error
    
    def test_plan_create_delete_immediate(self, validator):
        """Plan: create → delete (pointless) should fail sequencing"""
        plan = [
            {'module': 'file', 'operation': 'create', 'args': {'filename': 'test.txt'}},
            {'module': 'file', 'operation': 'delete', 'args': {'filename': 'test.txt'}}
        ]
        
        valid, error = validator.check_plan_sequencing(plan)
        assert valid is False
        assert 'Suspicious' in error
    
    def test_plan_with_existing_files(self, validator, workspace):
        """Plan should account for pre-existing files"""
        # Create existing file
        (workspace / 'existing.txt').write_text('test')
        
        plan = [
            {'module': 'file', 'operation': 'read', 'args': {'filename': 'existing.txt'}},
            {'module': 'file', 'operation': 'delete', 'args': {'filename': 'existing.txt'}}
        ]
        
        valid, error = validator.validate_plan(plan)
        assert valid is True


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
