import unittest
import json
from local_fortress.mcp_server.contract_verifier import ContractVerifier

class TestDynamicViability(unittest.TestCase):
    """
    Demonstrates "Dynamic Viability":
    Validation dependent on environmental context, not just static logic.
    """

    def test_context_dependent_validity(self):
        """
        Simulate a check where validity depends on an external dependency (Environment State).
        """
        # Scenario: We need a 'gpu_available' context.
        # Logic: If use_gpu=True, but gpu_available=False -> VALIDITY FAILURE (Contextual)
        
        # 1. Environment WITHOUT GPU
        context_no_gpu = {"gpu_available": False}
        is_valid_1, msg_1 = self.check_logic_viability(use_gpu=True, context=context_no_gpu)
        
        self.assertFalse(is_valid_1, "Should fail when GPU is required but missing")
        self.assertIn("dependency missing", msg_1)

        # 2. Environment WITH GPU
        context_with_gpu = {"gpu_available": True}
        is_valid_2, msg_2 = self.check_logic_viability(use_gpu=True, context=context_with_gpu)
        
        self.assertTrue(is_valid_2, "Should pass when GPU is available")

    def check_logic_viability(self, use_gpu: bool, context: dict) -> tuple[bool, str]:
        """
        Mock validation function that respects context.
        """
        if use_gpu and not context.get("gpu_available"):
            return False, "Environment dependency missing: GPU required"
        return True, "Logic viable in current context"

if __name__ == '__main__':
    unittest.main()
