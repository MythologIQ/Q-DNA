import sqlite3
import json
import hashlib
import time
import os

# Configuration
DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'ledger', 'qorelogic_soa_ledger.db')
SCHEMA_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'ledger', 'schema.sql')

def init_db():
    """Initialize the database with the schema."""
    print(f"Initializing Ledger at: {DB_PATH}")
    
    # Ensure directory exists
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Read and execute schema
    with open(SCHEMA_PATH, 'r') as f:
        schema_sql = f.read()
        cursor.executescript(schema_sql)
    
    conn.commit()
    print("✅ Schema applied successfully.")
    return conn

def create_genesis_block(conn):
    """Create the first entry in the ledger: The Genesis Axiom."""
    cursor = conn.cursor()
    
    # Check if ledger is empty
    cursor.execute("SELECT count(*) FROM soa_ledger")
    if cursor.fetchone()[0] > 0:
        print("⚠️ Ledger is not empty. Skipping Genesis Block creation.")
        return

    # The Genesis Payload
    axiom_payload = {
        "axiom": "Truth is earned, not assumed.",
        "project": "QoreLogic",
        "version": "1.0",
        "intent": "Establish a Root of Trust for Autonomous Accountability."
    }
    
    # Calculate Hash (Previous Hash is '0' for Genesis)
    prev_hash = "0" * 64
    timestamp = f"{time.time()}"
    did = "did:myth:overseer:genesis"
    payload_str = json.dumps(axiom_payload, sort_keys=True)
    
    # Entry Hash: SHA256(timestamp + did + payload + prev_hash)
    entry_data = f"{timestamp}{did}{payload_str}{prev_hash}".encode('utf-8')
    entry_hash = hashlib.sha256(entry_data).hexdigest()
    
    # Mock Signature (In real ops, this comes from identity_gen.py)
    signature = f"sig_genesis_{entry_hash[:8]}"
    
    # Insert
    cursor.execute("""
        INSERT INTO soa_ledger (agent_did, event_type, payload, entry_hash, prev_hash, signature, workspace_id)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (did, "GENESIS_AXIOM", payload_str, entry_hash, prev_hash, signature, "default"))
    
    conn.commit()
    print(f"✅ Genesis Block Created. Hash: {entry_hash}")

if __name__ == "__main__":
    try:
        connection = init_db()
        create_genesis_block(connection)
        connection.close()
        print("🚀 QoreLogic Sovereign Ledger is ready.")
    except Exception as e:
        print(f"❌ Initialization failed: {e}")
