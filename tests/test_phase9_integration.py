import unittest
from local_fortress.mcp_server.sentinel_engine import SentinelEngine, FailureMode

class TestPhase9Integration(unittest.TestCase):
    """
    Verify Phase 9.1 Z3 Integration into Sentinel Engine.
    """
    
    def test_z3_integration_extraction(self):
        """
        Verify that SentinelEngine extracts constraints and calls Z3.
        """
        sentinel = SentinelEngine()
        
        # Code with a contradictory contract
        # x >= 0.0 AND x <= -1.0 is impossible
        contradictory_code = """
        import deal
        
        @deal.pre(lambda x: 0.0 <= x <= -1.0)
        def impossible_fn(x):
            return x
        """
        
        findings = sentinel.check_formal_contracts(contradictory_code)
        
        # Should find LOGICAL_CONTRADICTION
        has_contradiction = any("LOGICAL_CONTRADICTION" in f for f in findings)
        self.assertTrue(has_contradiction, f"Should detect contradiction. Findings: {findings}")

    def test_z3_valid_contract(self):
        """
        Verify that valid contracts pass without findings.
        """
        sentinel = SentinelEngine()
        
        # Code with valid contract
        valid_code = """
        import deal
        
        @deal.pre(lambda x: 0.0 <= x <= 1.0)
        def valid_fn(x):
            return x
        """
        
        findings = sentinel.check_formal_contracts(valid_code)
        self.assertEqual(len(findings), 0, f"Valid contract should have no findings. Got: {findings}")

if __name__ == '__main__':
    unittest.main()
