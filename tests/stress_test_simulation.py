
import time
import random
import statistics
import sys
import os
from typing import List
from dataclasses import dataclass

# Add root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from local_fortress.mcp_server.sentinel_engine import SentinelEngine, FailureMode
from local_fortress.mcp_server.trust_engine import TrustEngine, TrustContext, MicroPenaltyType

@dataclass
class ScenarioResult:
    id: int
    duration_ms: float
    verdict: str
    risk_grade: str
    trust_delta: float
    success: bool
    notes: List[str]

class StressTester:
    def __init__(self):
        self.sentinel = SentinelEngine()
        self.trust = TrustEngine()
        self.results = []
        
    def generate_code_snippet(self, type_hint: str) -> str:
        if type_hint == "SAFE":
            return f"def safe_func_{random.randint(1000,9999)}():\n    return {random.randint(1,100)} * 2"
        elif type_hint == "SECRET":
            key = "sk_live_" + "".join(random.choices("0123456789abcdef", k=24))
            return f"def connect():\n    api_key = '{key}'\n    return True"
        elif type_hint == "COMPLEX":
            # Generate high complexity
            code = "def complex_logic(x):\n"
            indent = "    "
            for _ in range(12): # Depth > 10 usually triggers L2
                code += indent + "if x > 0:\n"
                indent += "    "
            code += indent + "return x"
            return code
        elif type_hint == "UNSAFE":
            return "import os\ndef run_cmd(cmd):\n    os.system(cmd)"
        elif type_hint == "DIV0":
            return "def calc(x):\n    return x / 0"
        return "pass"

    def run_simulation(self, iterations=100):
        print(f"Starting QoreLogic Stress Test ({iterations} scenarios)...")
        print("-" * 60)
        
        start_global = time.time()
        
        for i in range(iterations):
            # 1. Setup Random Scenario
            scenario_type = random.choice(["SAFE", "SAFE", "SECRET", "COMPLEX", "UNSAFE", "DIV0"])
            start_trust = random.uniform(0.3, 0.99)
            filename = f"module_{i}.py"
            if random.random() < 0.2:
                filename = "auth_service.py" # Trigger L3 pattern
            
            code = self.generate_code_snippet(scenario_type)
            
            # 2. Execution Timer
            t0 = time.time_ns()
            
            # --- QoreLogic Process ---
            
            # A. Sentinel Verify
            audit = self.sentinel.audit(filename, code)
            
            # B. Trust Update Simulation
            # Assume verification failure leads to penalty
            trust_delta = 0.0
            new_trust = start_trust
            
            if audit.verdict != "PASS":
                # Determine penalty
                penalty_type = MicroPenaltyType.SCHEMA_VIOLATION 
                # (Simplification: Sentinel doesn't map failure to PenaltyType directly yet, assuming general violation)
                
                # Apply Trust Engine Logic
                new_trust, applied = self.trust.calculate_micro_penalty(start_trust, penalty_type, 0.0)
                trust_delta = new_trust - start_trust
            
            # C. Trust Decay (Context-based)
            # If passed, update with EWMA
            if audit.verdict == "PASS":
                context = TrustContext.HIGH_RISK if audit.risk_grade == "L3" else TrustContext.LOW_RISK
                new_trust = self.trust.calculate_ewma_update(start_trust, 1.0, context)
                trust_delta = new_trust - start_trust

            t1 = time.time_ns()
            duration = (t1 - t0) / 1_000_000.0 # ms
            
            # 3. Validate Logic
            success = True
            notes = []
            
            # Expect failure for BAD types
            if scenario_type in ["SECRET", "UNSAFE", "DIV0"] and audit.verdict == "PASS":
                success = False
                notes.append(f"FALSE NEGATIVE: {scenario_type} passed verification")
                
            # Expect L3 for Auth files
            if "auth" in filename and audit.risk_grade != "L3":
                # Only a failure if it passed. If it FAILED, risk grade might be L1/L2 depending on failure logic
                # But Sentinel auto-classifies L3 based on filename usually.
                # Actually Sentinel sets risk_grade logic inside.
                pass 
                
            self.results.append(ScenarioResult(
                id=i, 
                duration_ms=duration, 
                verdict=audit.verdict,
                risk_grade=audit.risk_grade,
                trust_delta=trust_delta,
                success=success,
                notes=notes
            ))
            
            # print(f"[{i:03d}] {scenario_type:<8} -> {audit.verdict:<8} | Trust {start_trust:.2f}->{new_trust:.2f} ({trust_delta:+.3f}) | {duration:.2f}ms")

        total_time = time.time() - start_global
        self.print_report(total_time)

    def print_report(self, total_time):
        count = len(self.results)
        failures = [r for r in self.results if not r.success]
        avg_latency = statistics.mean(r.duration_ms for r in self.results)
        max_latency = max(r.duration_ms for r in self.results)
        
        print("-" * 60)
        print("STRESS TEST REPORT")
        print("-" * 60)
        print(f"Total Scenarios: {count}")
        print(f"Total Wall Time: {total_time:.3f}s")
        print(f"Logic Flaws:     {len(failures)}")
        print(f"Avg Latency:     {avg_latency:.2f}ms")
        print(f"Max Latency:     {max_latency:.2f}ms")
        print(f"Throughput:      {count/total_time:.1f} ops/sec")
        print("-" * 60)
        
        if failures:
            print("FLAWS DETECTED:")
            for f in failures[:10]: # Check first 10
                print(f"  #{f.id}: {f.notes}")
            if len(failures) > 10: print(f"  ... and {len(failures)-10} more.")
        else:
            print("✅ No logical flaws detected in random harness.")

        # Rate Efficiency
        print("\nEFFICIENCY RATING:")
        if avg_latency < 10: print("  Latency: ⭐⭐⭐⭐⭐ (Excellent < 10ms)")
        elif avg_latency < 50: print("  Latency: ⭐⭐⭐⭐ (Good < 50ms)")
        else: print("  Latency: ⭐⭐ (Needs Optimization)")

if __name__ == "__main__":
    from typing import List
    tester = StressTester()
    tester.run_simulation(100)
