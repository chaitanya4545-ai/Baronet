"""
Unit tests for Risk Classifier
Tests rule-based risk assessment
"""
import pytest
from core.risk_classifier import risk_classifier, RiskLevel, PlanRiskClassifier


class TestRiskClassifier:
    """Test deterministic risk classification"""
    
    def test_safe_operations(self):
        """Read operations should be SAFE"""
        risk = risk_classifier.classify_operation('read', {'filename': 'test.txt'})
        assert risk == RiskLevel.SAFE
        
        risk = risk_classifier.classify_operation('list_files', {})
        assert risk == RiskLevel.SAFE
    
    def test_moderate_operations(self):
        """Create/write operations should be MODERATE"""
        risk = risk_classifier.classify_operation('create', {'filename': 'test.txt'})
        assert risk == RiskLevel.MODERATE
        
        risk = risk_classifier.classify_operation('write', {'filename': 'test.txt', 'content': 'hello'})
        assert risk == RiskLevel.MODERATE
    
    def test_dangerous_operations(self):
        """Delete operations should be DANGEROUS"""
        risk = risk_classifier.classify_operation('delete', {'filename': 'test.txt'})
        assert risk == RiskLevel.DANGEROUS
    
    def test_wildcard_escalates_risk(self):
        """Wildcard should escalate to DANGEROUS"""
        risk = risk_classifier.classify_operation('create', {'filename': '*.txt'})
        assert risk == RiskLevel.DANGEROUS
    
    def test_path_traversal_escalates_risk(self):
        """Path traversal should escalate to DANGEROUS"""
        risk = risk_classifier.classify_operation('read', {'filename': '../secret.txt'})
        assert risk == RiskLevel.DANGEROUS
    
    def test_recursive_escalates_risk(self):
        """Recursive operations should escalate to ELEVATED"""
        risk = risk_classifier.classify_operation('delete', {'filename': 'folder', 'recursive': True})
        # Recursive should be at least ELEVATED
        assert risk.value >= RiskLevel.ELEVATED.value
    
    def test_plan_classification(self):
        """Plan classification should aggregate risks"""
        steps = [
            {'operation': 'list_files', 'args': {}},
            {'operation': 'create', 'args': {'filename': 'test.txt'}},
            {'operation': 'read', 'args': {'filename': 'test.txt'}}
        ]
        
        profile = risk_classifier.classify_plan(steps)
        
        assert profile['overall_risk'] == RiskLevel.MODERATE
        assert profile['step_count'] == 3
        assert profile['dangerous_operations'] == 0
    
    def test_plan_with_deletes(self):
        """Plan with deletes should be DANGEROUS"""
        steps = [
            {'operation': 'list_files', 'args': {}},
            {'operation': 'delete', 'args': {'filename': 'old.txt'}},
        ]
        
        profile = risk_classifier.classify_plan(steps)
        
        assert profile['overall_risk'] == RiskLevel.DANGEROUS
        assert profile['dangerous_operations'] == 1
        assert profile['requires_backup'] is True
    
    def test_mass_operations_escalate(self):
        """Mass operations should escalate risk"""
        # 150 files affected
        steps = [{'operation': 'create', 'args': {'filename': '*.txt'}} for _ in range(3)]
        
        profile = risk_classifier.classify_plan(steps)
        
        # Should escalate to DANGEROUS due to mass threshold
        assert profile['overall_risk'] == RiskLevel.DANGEROUS
        assert profile['affected_files'] > 100


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
