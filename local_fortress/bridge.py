"""
QoreLogic UI Bridge
Acts as the interface between the PowerShell Launcher/UI and the Python Backend.
Takes JSON input commands and returns JSON responses.
"""

import sys
import os
import json
import argparse
import traceback
from pathlib import Path

# Add local_fortress to path
sys.path.insert(0, os.path.dirname(__file__))

from mcp_server.agent_config import get_agent_config, AgentConfigLoader
from mcp_server.verification_config import get_verification_config, set_verification_mode, VerificationMode
from mcp_server.identity_manager import IdentityManager
from mcp_server.trust_engine import TrustEngine
import sqlite3

def handle_get_verification_config(args):
    config = get_verification_config()
    return {"success": True, "config": config.to_dict()}

def handle_set_verification_config(args):
    payload = json.loads(args.payload)
    mode_str = payload.get("mode", "lite").lower()
    
    try:
        mode = VerificationMode(mode_str)
        success = set_verification_mode(mode)
        return {"success": success, "mode": mode.value}
    except ValueError:
        return {"success": False, "error": f"Invalid mode: {mode_str}"}

def handle_get_trust_status(args):
    # Retrieve trust status for an agent (default sentinel)
    agent = "did:myth:sentinel" # Default for single-agent view
    if args.payload:
        data = json.loads(args.payload)
        agent = data.get("did", agent)
        
    engine = TrustEngine()
    score = engine.get_limit(agent, 1.0) # Actually get_limit calculates trust indirectly? 
    # TrustEngine doesn't have a simple "get_score" method exposed directly in previous diffs?
    # Checking trust_engine source...
    # It has get_trust_score(did)
    
    score = engine.get_trust_score(agent)
    stage_info = engine.get_trust_stage(agent)
    
    return {
        "success": True,
        "did": agent,
        "score": score,
        "stage": stage_info[0].name if stage_info else "UNKNOWN",
        "stage_multiplier": stage_info[1] if stage_info else 1.0
    }

def handle_list_identities(args):
    # Scan keystore
    keystore_dir = Path(__file__).parent / "keystore"
    identities = []
    
    if keystore_dir.exists():
        for keyfile in keystore_dir.glob("*.key"):
            try:
                with open(keyfile, 'r') as f:
                    data = json.load(f)
                    identities.append({
                        "did": data.get("did"),
                        "role": data.get("role"),
                        "created_at": data.get("created_at"),
                        "expires_at": data.get("expires_at"),
                        "algorithm": data.get("kdf_algorithm", "pbkdf2")
                    })
            except:
                pass
                
    return {"success": True, "identities": identities}

def handle_rotate_key(args):
    payload = json.loads(args.payload)
    did = payload.get("did")
    passphrase = payload.get("passphrase", "default-passphrase") # In real app, prompt user
    
    mgr = IdentityManager(passphrase=passphrase)
    try:
        new_id = mgr.rotate_key(did)
        return {"success": True, "new_public_key": new_id.public_key_hex}
    except Exception as e:
        return {"success": False, "error": str(e)}

def handle_query_ledger(args):
    db_path = Path(__file__).parent / "ledger" / "qorelogic_soa_ledger.db"
    if not db_path.exists():
        return {"success": False, "error": "Ledger DB not found"}
        
    try:
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()
        cur.execute("SELECT * FROM soa_ledger ORDER BY timestamp DESC LIMIT 50")
        rows = [dict(r) for r in cur.fetchall()]
        conn.close()
        return {"success": True, "events": rows}
    except Exception as e:
        return {"success": False, "error": str(e)}

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("action", help="Action to perform")
    parser.add_argument("--payload", help="JSON payload", default="{}")
    args = parser.parse_args()
    
    actions = {
        "get_verification_config": handle_get_verification_config,
        "set_verification_config": handle_set_verification_config,
        "get_trust_status": handle_get_trust_status,
        "list_identities": handle_list_identities,
        "rotate_key": handle_rotate_key,
        "query_ledger": handle_query_ledger
    }
    
    if args.action in actions:
        try:
            result = actions[args.action](args)
            print(json.dumps(result))
        except Exception as e:
            # traceback.print_exc()
            print(json.dumps({"success": False, "error": str(e)}))
    else:
        print(json.dumps({"success": False, "error": "Unknown action"}))

if __name__ == "__main__":
    main()
