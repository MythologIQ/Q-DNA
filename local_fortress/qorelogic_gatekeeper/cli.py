import sys
import os
import json
import argparse
from pathlib import Path

# In a real packaged environment, we would import from the installed package.
# For now, we assume this file is part of the 'local_fortress' package context
# or that PYTHONPATH includes the package root.

def main():
    parser = argparse.ArgumentParser(description="QoreLogic Gatekeeper - Active Hook")
    parser.add_argument("file", help="Path to the file to audit")
    args = parser.parse_args()
    
    file_path = Path(args.file)
    if not file_path.exists():
        print(f"Error: File not found: {file_path}")
        sys.exit(1)
        
    try:
        # Import the tool function. 
        # Note: This requires the 'mcp_server' module to be in the python path.
        # When installed via setup.py, 'mcp_server' should be a top-level package or subpackage.
        # We might need to adjust imports based on how find_packages() sees the dir structure.
        from mcp_server.server import audit_code
        
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        print(f"Running Sentinel Gatekeeper on {file_path}...")
        result_json = audit_code(str(file_path), content)
        result = json.loads(result_json)
        
        verdict = result.get('verdict')
        risk = result.get('risk_grade')
        rationale = result.get('rationale')
        
        print(f"Verdict: {verdict}")
        print(f"Risk: {risk}")
        print(f"Reason: {rationale}")
        
        if verdict == "FAIL":
            print("❌ COMMIT REJECTED: Critical Vulnerability Detected.")
            sys.exit(1)
            
        if verdict == "L3_REQUIRED":
            print("⚠️ COMMIT BLOCKED: L3 Approval Required.")
            sys.exit(1)
            
        print("✅ PASS")
        sys.exit(0)
        
    except ImportError:
        print("Error: QoreLogic Server module not found. Is the package installed?")
        sys.exit(1)
    except Exception as e:
        print(f"System Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
