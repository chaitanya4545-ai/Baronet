"""
Dependency Edge Case Tests
Tests unusual dependency scenarios
"""
import pytest
from pathlib import Path
import tempfile
import shutil
from core.dependency_validator import create_dependency_validator


class TestDependencyEdgeCases:
    """Test unusual and edge case dependency scenarios"""
    
    @pytest.fixture
    def workspace(self):
        """Create temp workspace"""
        temp_dir = Path(tempfile.mkdtemp())
        yield temp_dir
        shutil.rmtree(temp_dir)
    
    @pytest.fixture
    def validator(self, workspace):
        """Create validator"""
        return create_dependency_validator(workspace)
    
    def test_circular_dependencies(self, validator):
        """Detect circular operation dependencies"""
        # Not really circular in file ops, but test sequencing
        plan = [
            {'module': 'file', 'operation': 'create', 'args': {'filename': 'a.txt'}},
            {'module': 'file', 'operation': 'create', 'args': {'filename': 'b.txt'}},
            {'module': 'file', 'operation': 'delete', 'args': {'filename': 'a.txt'}},
            {'module': 'file', 'operation': 'read', 'args': {'filename': 'a.txt'}}  # Deleted!
        ]
        
        valid, error = validator.validate_plan(plan)
        assert valid is False
        assert 'not created yet' in error or 'deleted' in error
    
    def test_double_delete(self, validator):
        """Catch double delete attempts"""
        plan = [
            {'module': 'file', 'operation': 'create', 'args': {'filename': 'temp.txt'}},
            {'module': 'file', 'operation': 'delete', 'args': {'filename': 'temp.txt'}},
            {'module': 'file', 'operation': 'delete', 'args': {'filename': 'temp.txt'}}
        ]
        
        valid, error = validator.validate_plan(plan)
        assert valid is False
        assert 'delete' in error.lower() or 'deleted' in error.lower()
    
    def test_create_write_sequence(self, validator):
        """Allow create followed by write"""
        plan = [
            {'module': 'file', 'operation': 'create', 'args': {'filename': 'new.txt', 'content': 'initial'}},
            {'module': 'file', 'operation': 'write', 'args': {'filename': 'new.txt', 'content': 'updated'}}
        ]
        
        valid, error = validator.validate_plan(plan)
        assert valid is True
    
    def test_missing_intermediate_create(self, validator):
        """Catch missing file creation in multi-step"""
        plan = [
            {'module': 'file', 'operation': 'create', 'args': {'filename': 'a.txt'}},
            # Missing: create b.txt
            {'module': 'file', 'operation': 'write', 'args': {'filename': 'b.txt', 'content': 'data'}}
        ]
        
        valid, error = validator.validate_plan(plan)
        assert valid is False
        assert 'not created yet' in error or 'does not exist' in error
    
    def test_empty_filename(self, validator):
        """Handle empty filename gracefully"""
        command = {
            'module': 'file',
            'operation': 'create',
            'args': {'filename': '', 'content': 'test'}
        }
        
        # Should handle gracefully (will be caught by schema validator normally)
        valid, error = validator.validate_command(command)
        # Should pass or return True (empty check is schema validator's job)
        assert isinstance(valid, bool)
    
    def test_nonexistent_directory_create(self, validator):
        """Allow creating file in nonexistent subdirectory"""
        command = {
            'module': 'file',
            'operation': 'create',
            'args': {'filename': 'subdir/new.txt', 'content': 'test'}
        }
        
        # Should be allowed (file_ops creates parent dirs)
        valid, error = validator.validate_command(command)
        assert valid is True


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
