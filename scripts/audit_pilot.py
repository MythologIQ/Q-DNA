import sys
import os
import json
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from local_fortress.mcp_server.server import audit_code, log_event

def audit_file(rel_path):
    full_path = PROJECT_ROOT / rel_path
    if not full_path.exists():
        print(f"File not found: {rel_path}")
        return

    with open(full_path, 'r', encoding='utf-8') as f:
        content = f.read()

    print(f"Auditing {rel_path}...")
    try:
        # We call the tool function directly.
        # Since we are running in a script, we might be bypassing the FastMCP wrapper context,
        # but the logic inside audit_code imports SentinelEngine and uses the DB, so it should work.
        # Note: server.py initializes 'mcp' global but functional logic is inside the def.
        
        result_json = audit_code(str(rel_path), content)
        result = json.loads(result_json)
        print(f"Verdict: {result.get('verdict')}")
        print(f"Risk Grade: {result.get('risk_grade')}")
        print(f"Rationale: {result.get('rationale')}")
        print("-" * 40)
    except Exception as e:
        print(f"Error auditing {rel_path}: {e}")

def main():
    files_to_audit = [
        "research/pilot/vault_kv/utils/config.py",
        "research/pilot/vault_kv/utils/logger.py",
        "research/pilot/vault_kv/network/connector.py",
        "research/pilot/vault_kv/storage/db.py",
        "research/pilot/vault_kv/auth/rbac.py"
    ]

    print("--- Starting Retroactive Daemon Audit ---")
    for f in files_to_audit:
        audit_file(f)
    print("--- Audit Complete ---")

if __name__ == "__main__":
    main()
