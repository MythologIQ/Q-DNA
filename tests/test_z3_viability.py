import unittest
from local_fortress.mcp_server.contract_verifier import ContractVerifier

class TestZ3Viability(unittest.TestCase):
    """
    Phase 9.1: Viability Validation using Formal Verification (Z3).
    """

    def setUp(self):
        self.verifier = ContractVerifier(enable_z3=True)

    def test_z3_valid_trust_score(self):
        """Verify that a standard trust score (0.0-1.0) is satisfiable."""
        if not self.verifier.z3_available:
            self.skipTest("Z3 not installed")
            
        constraints = {
            "trust_score": (0.0, 1.0)
        }
        is_sat, msg = self.verifier.verify_with_z3(constraints)
        self.assertTrue(is_sat, f"Should be satisfiable: {msg}")

    def test_z3_impossible_contradiction(self):
        """Verify that a logical contradiction is detected (UNSAT)."""
        if not self.verifier.z3_available:
            self.skipTest("Z3 not installed")

        # Constraint: Score must be > 1.0 AND < 0.0 (Impossible)
        constraints = {
            "impossible_score": (1.1, -0.1) 
        }
        # Note: My simple implementation does min <= var <= max.
        # If min > max, Z3 should say UNSAT.
        
        is_sat, msg = self.verifier.verify_with_z3(constraints)
        self.assertFalse(is_sat, "Should be unsatisfiable")
        self.assertIn("Unsatisfiable", msg)

    def test_z3_lambda_parameters(self):
        """Verify RiskMetrics lambda parameters are distinct and valid."""
        if not self.verifier.z3_available:
            self.skipTest("Z3 not installed")
            
        constraints = {
            "lambda_high": (0.94, 0.94),
            "lambda_low": (0.97, 0.97)
        }
        is_sat, msg = self.verifier.verify_with_z3(constraints)
        self.assertTrue(is_sat)

if __name__ == '__main__':
    unittest.main()
