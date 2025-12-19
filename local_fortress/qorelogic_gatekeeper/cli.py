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
    parser.add_argument("file", nargs="?", help="Path to the file to audit (Optional if running dashboard)")
    parser.add_argument("--monitor", action="store_true", help="Run in silent monitoring mode (Audit Only, do not block)")
    parser.add_argument("--dashboard", action="store_true", help="Launch the QoreLogic Dashboard Server")
    args = parser.parse_args()
    
    if args.dashboard:
        print("🚀 Starting QoreLogic Dashboard on http://0.0.0.0:8000")
        try:
            # Import backend main app
            # Assuming it's installed in the python path under 'dashboard.backend' or similar
            # But since we copied it to /app/dashboard/backend and set PYTHONPATH...
            # We might need to adjust sys.path if not installed as a package.
            
            # For the Docker build, we copied dashboard/backend to /app/dashboard/backend
            # So let's try to add that to path if needed.
            sys.path.append("/app/dashboard/backend")
            import uvicorn
            # We import the 'app' object from main.py
            # Since main.py is in /app/dashboard/backend/main.py
            from main import app as dashboard_app
            
            uvicorn.run(dashboard_app, host="0.0.0.0", port=8000)
            sys.exit(0)
        except Exception as e:
            print(f"Error launching dashboard: {e}")
            sys.exit(1)

    if not args.file:
        parser.print_help()
        sys.exit(1)

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

        mode_label = "[MONITOR MODE]" if args.monitor else "[ACTIVE BLOCKING]"
        if not args.monitor:
             print(f"Running Sentinel Gatekeeper {mode_label} on {file_path}...")
        
        result_json = audit_code(str(file_path), content)
        result = json.loads(result_json)
        
        verdict = result.get('verdict')
        risk = result.get('risk_grade')
        rationale = result.get('rationale')
        
        if not args.monitor:
            print(f"Verdict: {verdict}")
            print(f"Risk: {risk}")
            print(f"Reason: {rationale}")
        
        if verdict == "FAIL":
            if args.monitor:
                # Silent failure recording
                sys.exit(0)
            else:
                print("❌ COMMIT REJECTED: Critical Vulnerability Detected.")
                sys.exit(1)
            
        if verdict == "L3_REQUIRED":
            if args.monitor:
                 # Silent L3 recording
                 sys.exit(0)
            else:
                print("⚠️ COMMIT BLOCKED: L3 Approval Required.")
                sys.exit(1)
            
        if not args.monitor:
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
