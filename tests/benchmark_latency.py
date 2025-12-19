import sys
import os
import time
import statistics

# Add project root
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../')))

from local_fortress.mcp_server.sentinel_engine import SentinelEngine

def benchmark_latency():
    print("running Benchmark: Sentinel Audit Latency")
    engine = SentinelEngine()
    
    # Sample content (Safe python code)
    content = """
    def calculate_sum(a, b):
        return a + b
        
    class DataProcessor:
        def process(self, data):
            results = []
            for item in data:
                if item > 0:
                    results.append(item * 2)
            return results
    """
    
    latencies = []
    print("Executing 50 iterations...")
    
    start_global = time.time()
    for i in range(50):
        # Audit
        result = engine.audit("test_file.py", content)
        latencies.append(result.latency_ms)
        
    total_time = time.time() - start_global
    
    avg_lat = statistics.mean(latencies)
    p95_lat = sorted(latencies)[int(len(latencies) * 0.95)]
    
    print("-" * 30)
    print(f"Total Time: {total_time:.2f}s")
    print(f"Iterations: {len(latencies)}")
    print(f"Avg Latency: {avg_lat:.2f} ms")
    print(f"P95 Latency: {p95_lat:.2f} ms")
    print("-" * 30)
    
    # Target: < 5000ms (~5s) - actually we want much faster for pre-commit (e.g. 500ms)
    # SAST_ACCURACY.md target says < 5 seconds.
    # Our internal goal for simple files should be < 500ms.
    
    if p95_lat < 5000:
        print("✅ PASS: Latency within 5s budget")
    else:
        print("❌ FAIL: Latency exceeds 5s budget")

    # Save artifact for user
    with open("BENCHMARK_RESULTS.txt", "w") as f:
        f.write(f"Avg: {avg_lat:.2f}ms\nP95: {p95_lat:.2f}ms\nPass: {p95_lat < 5000}")

if __name__ == "__main__":
    benchmark_latency()
