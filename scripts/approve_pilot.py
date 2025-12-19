import sys
import os
import json
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from local_fortress.mcp_server.server import get_pending_approvals, approve_l3

def approve_all():
    pending_json = get_pending_approvals()
    pending = json.loads(pending_json)
    
    print(f"Found {len(pending)} pending approvals.")
    
    for p in pending:
        q_id = p['queue_id']
        reason = p['reason']
        print(f"Approving [ID: {q_id}] Reason: {reason}")
        
        result = approve_l3(q_id, True, "Pilot deployment approved by Overseer.")
        print(f"Result: {result}")

if __name__ == "__main__":
    approve_all()
