import sys
import os
import json
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

# Import tools directly
from local_fortress.mcp_server.server import audit_code

def check_file(rel_path):
    full_path = PROJECT_ROOT / rel_path
    if not full_path.exists():
        print(f"File not found: {rel_path}")
        return False

    with open(full_path, 'r', encoding='utf-8') as f:
        content = f.read()

    print(f"Running Sentinel Gatekeeper on {rel_path}...")
    try:
        result_json = audit_code(str(rel_path), content)
        result = json.loads(result_json)
        
        verdict = result.get('verdict')
        risk = result.get('risk_grade')
        rationale = result.get('rationale')
        
        print(f"Verdict: {verdict}")
        print(f"Risk: {risk}")
        print(f"Reason: {rationale}")
        
        if verdict == "FAIL":
            print("❌ COMMIT REJECTED: Critical Vulnerability Detected.")
            return False
            
        if verdict == "L3_REQUIRED":
            print("⚠️ COMMIT BLOCKED: L3 Approval Required.")
            return False
            
        print("✅ PASS")
        return True
        
    except Exception as e:
        print(f"Error auditing {rel_path}: {e}")
        return False

def main():
    if len(sys.argv) < 2:
        print("Usage: python pre_commit.py <file_path>")
        sys.exit(1)
        
    target_file = sys.argv[1]
    success = check_file(target_file)
    
    if not success:
        sys.exit(1)
    
    sys.exit(0)

if __name__ == "__main__":
    main()
