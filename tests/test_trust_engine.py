from local_fortress.mcp_server.trust_engine import TrustEngine, TrustContext

def test_trust_engine():
    engine = TrustEngine()
    
    # 1. Lambda Selection
    assert engine.get_lambda(TrustContext.HIGH_RISK) == 0.94
    assert engine.get_lambda(TrustContext.LOW_RISK) == 0.97
    print("✅ Lambda selection verified")
    
    # 2. EWMA Calculation (Manual Check)
    # Start 0.5, Outcome 1.0, High Risk (0.94)
    # New = 0.5 * 0.94 + 1.0 * 0.06 = 0.47 + 0.06 = 0.53
    new_score = engine.calculate_ewma_update(0.5, 1.0, TrustContext.HIGH_RISK)
    assert abs(new_score - 0.53) < 0.0001
    print(f"✅ EWMA High Risk verified: {new_score}")
    
    # 3. Transitive Trust
    # Path [0.9, 0.9] -> 0.9 * 0.9 * 0.5 = 0.81 * 0.5 = 0.405
    transitive = engine.calculate_transitive_trust([0.9, 0.9])
    assert abs(transitive - 0.405) < 0.0001
    print(f"✅ Transitive trust verified: {transitive}")
    
    print("🎉 All Trust Engine sanity checks passed!")

if __name__ == "__main__":
    test_trust_engine()
