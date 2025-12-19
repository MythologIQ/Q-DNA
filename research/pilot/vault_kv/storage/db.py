import sqlite3
import os
from typing import Optional, Any
from cryptography.fernet import Fernet
import json
import logging

# Protected Build: Audit logging active
logger = logging.getLogger("vault.storage")

class SecureStorage:
    """
    Encrypted Key-Value Store backed by SQLite.
    Enforces encryption at rest.
    """
    
    def __init__(self, db_path: str = "vault.db", encryption_key: Optional[bytes] = None):
        self.db_path = db_path
        if not encryption_key:
            # In a real scenario, this would come from a KMS.
            # For the pilot, we check env or generate one (warning: ephemeral).
            env_key = os.environ.get("VAULT_KEY")
            if env_key:
                self.key = env_key.encode()
            else:
                self.key = Fernet.generate_key()
                logger.warning("No VAULT_KEY found. Generated ephemeral key.")
        else:
            self.key = encryption_key
            
        self.cipher = Fernet(self.key)
        self._init_db()

    def _init_db(self):
        """Initialize the database schema."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        # Sentinel Check: Ensure schema is simple and safe
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS secrets (
                key TEXT PRIMARY KEY,
                value BLOB NOT NULL,
                metadata TEXT
            )
        ''')
        conn.commit()
        conn.close()

    def put(self, key: str, value: str, metadata: dict = None):
        """
        Encrypts and stores a value.
        """
        if not key or not value:
            raise ValueError("Key and Value must be provided.")
            
        encrypted_val = self.cipher.encrypt(value.encode())
        meta_json = json.dumps(metadata) if metadata else "{}"
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        try:
            # Sentinel Check: Parameterized query to prevent SQL Injection
            cursor.execute(
                "INSERT OR REPLACE INTO secrets (key, value, metadata) VALUES (?, ?, ?)",
                (key, encrypted_val, meta_json)
            )
            conn.commit()
            logger.info(f"Secret stored for key: {key}")
        except sqlite3.Error as e:
            logger.error(f"Database error: {e}")
            raise
        finally:
            conn.close()

    def get(self, key: str) -> Optional[str]:
        """
        Retrieves and decrypts a value.
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        try:
            cursor.execute("SELECT value FROM secrets WHERE key = ?", (key,))
            row = cursor.fetchone()
            if row:
                encrypted_val = row[0]
                return self.cipher.decrypt(encrypted_val).decode()
            return None
        finally:
            conn.close()
