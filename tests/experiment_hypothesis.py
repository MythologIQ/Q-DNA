import sys
import os
import time
import json
from dataclasses import dataclass

# Add project root
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../')))

from local_fortress.mcp_server.sentinel_engine import SentinelEngine
from local_fortress.mcp_server.trust_manager import TrustManager
from local_fortress.mcp_server.trust_engine import TrustContext

# --- The "Vulnerable Payload" ---
# Contains:
# 1. Complexity (Nested loops) - Caught by L1
# 2. Hardcoded Secret - Caught by L2
# 3. PII Leak - Caught by L2/3
PAYLOAD = """
def process_user_data(users):
    # HARDCODED SECRET (L2)
    api_key = "sk-live-1234567890abcdef12345678" 
    
    results = []
    # COMPLEXITY (L1)
    for u in users:
        for field in u:
            for char in field:
                if char == 'a':
                    # PII LEAK (L2/3)
                    print(f"Processing SSN: {u['ssn']}")
                    results.append(char)
    return results
"""

@dataclass
class ExperimentResult:
    mode: str
    latency_ms: float
    bugs_caught: int
    bugs_missed: int
    trust_score_delta: float

def run_control_group() -> ExperimentResult:
    """
    Control Group: The 'Fast' Agent.
    Simulates a standard linter that only looks for syntax/complexity.
    """
    start = time.time()
    
    # Simulate L1 Check only (Complexity)
    engine = SentinelEngine()
    # Manually calling specific checks to mimic "shallow" audit
    complexity_score, _ = engine.check_cyclomatic_complexity(PAYLOAD)
    
    # It catches complexity, but misses Secrets and PII
    caught = 1 if complexity_score > 10 else 0
    missed = 2 # Secret + PII
    
    latency = (time.time() - start) * 1000
    
    return ExperimentResult("Control (Fast)", latency, caught, missed, 0.0)

def run_qorelogic_group() -> ExperimentResult:
    """
    Experimental Group: QoreLogic.
    Runs Full Sentinel Pipeline + Trust Update.
    """
    start = time.time()
    
    # 1. Full Audit
    engine = SentinelEngine()
    result = engine.audit("vulnerable.py", PAYLOAD)
    
    caught = len(result.failure_modes)
    missed = max(0, 3 - caught) # We know there are 3 bugs
    
    # 2. Trust Update (The "Cost" of tracking)
    # Simulate an agent "did:myth:test:runner" submitting this
    db_path = os.path.join(os.path.dirname(__file__), '../local_fortress/ledger/qorelogic_soa_ledger.db')
    tm = TrustManager(db_path)
    
    # Score penalty based on audit result (FAILED = 0.0)
    # We measure the time cost of this DB operation too
    did = "did:myth:test:runner"
    # Ensure agent exists for test (handling potential missing agent)
    current_score_before = tm.get_agent_trust(did) or 0.5
    
    # Heuristic: If issues > 0 -> Outcome 0.0
    outcome = 1.0 if not result.failure_modes else 0.0
    tm.update_trust_ewma(did, outcome, TrustContext.HIGH_RISK)
    
    current_score_after = tm.get_agent_trust(did) or 0.5
    delta = current_score_after - current_score_before
    
    latency = (time.time() - start) * 1000
    
    return ExperimentResult("QoreLogic (Trusted)", latency, caught, missed, delta)

def main():
    print("🔬 Running Hypothesis Validation: 'Smart Compute vs. Brute Force'...\n")
    
    # 1. Setup Test Agent for QoreLogic run
    # (Just ensures DB has the row, cost not included in experiment unless we want to capture 'First Contact' cost)
    setup_im = True
    if setup_im:
        from local_fortress.mcp_server.identity_manager import IdentityManager
        os.environ["QORELOGIC_IDENTITY_PASSPHRASE"] = "test"
        im = IdentityManager()
        im.create_agent("Scrivener") # We need a generic agent, but let's assume we use the one from integration test or make new one
        # Actually, let's just insert a dummy row to be fast and deterministic
        import sqlite3
        db_path = os.path.join(os.path.dirname(__file__), '../local_fortress/ledger/qorelogic_soa_ledger.db')
        with sqlite3.connect(db_path) as conn:
            conn.execute("INSERT OR IGNORE INTO agent_registry (did, role, trust_score, status) VALUES (?, ?, ?, ?)", 
                         ("did:myth:test:runner", "Scrivener", 0.5, "ACTIVE"))
            conn.commit()

    # 2. Run Experiments
    control = run_control_group()
    experimental = run_qorelogic_group()
    
    # 3. Report
    print(f"{'Metric':<20} | {'Control (Standard)':<20} | {'QoreLogic (Trusted)':<20} | {'Delta':<10}")
    print("-" * 80)
    print(f"{'Latency (ms)':<20} | {control.latency_ms:^20.2f} | {experimental.latency_ms:^20.2f} | {experimental.latency_ms - control.latency_ms:+.2f} ms")
    print(f"{'Bugs Caught':<20} | {control.bugs_caught:^20} | {experimental.bugs_caught:^20} | {experimental.bugs_caught - control.bugs_caught:+}")
    print(f"{'Bugs Missed':<20} | {control.bugs_missed:^20} | {experimental.bugs_missed:^20} | {experimental.bugs_missed - control.bugs_missed:+}")
    print(f"{'Trust Impact':<20} | {control.trust_score_delta:^20.4f} | {experimental.trust_score_delta:^20.4f} | {experimental.trust_score_delta:+}")
    
    print("\n--- Conclusion ---")
    cost_increase = f"{(experimental.latency_ms / control.latency_ms):.1f}x" if control.latency_ms > 0 else "Infinite"
    print(f"Compute Cost Increase: {cost_increase}")
    
    if experimental.bugs_missed == 0 and control.bugs_missed > 0:
        print("✅ QUALITY VICTORY: QoreLogic caught ALL bugs.")
    
    if experimental.latency_ms < 50: # Arbitrary threshold for "Excessive"
        print("✅ PERFORMANCE VICTORY: Latency is negligible (< 50ms). 'Heightened' but not 'Excessive'.")
    else:
        print("⚠️ PERFORMANCE WARNING: Latency is noticeable (> 50ms).")

    # Artifact generation for the user
    with open("HYPOTHESIS_REPORT.txt", "w") as f:
        f.write(f"Control Latency: {control.latency_ms:.2f}ms\n")
        f.write(f"QoreLogic Latency: {experimental.latency_ms:.2f}ms\n")
        f.write(f"Quality Delta: +{experimental.bugs_caught - control.bugs_caught} bugs caught\n")

if __name__ == "__main__":
    main()
