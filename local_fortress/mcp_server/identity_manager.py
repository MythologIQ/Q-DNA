"""
QoreLogic Identity Manager

Provides cryptographic identity management:
- Ed25519 key generation and storage
- Digital signature creation and verification
- Key rotation with audit trail
- Secure keyfile encryption
"""

import os
import json
import time
import hashlib
import sqlite3
from typing import Optional, Tuple, Dict
from dataclasses import dataclass
from pathlib import Path

from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey, Ed25519PublicKey
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.backends import default_backend
from cryptography.fernet import Fernet
import base64

# Argon2id support (Research: CRYPTOGRAPHIC_STANDARDS.md §7.2)
try:
    from argon2.low_level import hash_secret_raw, Type
    ARGON2_AVAILABLE = True
except ImportError:
    ARGON2_AVAILABLE = False

# Configuration
KEYSTORE_DIR = Path(__file__).parent.parent / "keystore"
DB_PATH = Path(__file__).parent.parent / "ledger" / "qorelogic_soa_ledger.db"
KEY_ROTATION_DAYS = 30
LEGACY_SALT = b"qorelogic-salt-v1"  # For backward compatibility

# Argon2id parameters (OWASP recommendations for password hashing)
ARGON2_TIME_COST = 3       # Number of iterations
ARGON2_MEMORY_COST = 65536 # 64 MB
ARGON2_PARALLELISM = 4     # Threads
ARGON2_HASH_LEN = 32       # Output length for Fernet key

@dataclass
class AgentIdentity:
    """Represents a cryptographic identity for an agent."""
    did: str
    role: str
    public_key_hex: str
    created_at: float
    expires_at: float
    
    def is_expired(self) -> bool:
        return time.time() > self.expires_at


class IdentityManager:
    """
    Manages cryptographic identities for QoreLogic agents.
    
    Security Model:
    - Ed25519 for signing (fast, secure, deterministic)
    - Fernet for keyfile encryption (AES-128-CBC)
    - Argon2id for key derivation (GPU-resistant) - NEW keys
    - PBKDF2 for key derivation (legacy compatibility)
    
    Key Derivation (Research: CRYPTOGRAPHIC_STANDARDS.md §7.2):
    - New keys: Use Argon2id (memory-hard, GPU-resistant)
    - Legacy keys: Auto-detected via 'kdf_algorithm' field, use PBKDF2
    - Rotation: Auto-upgrades legacy keys to Argon2id
    """
    
    def __init__(self, passphrase: str = None):
        """
        Initialize the identity manager.
        
        Args:
            passphrase: Optional passphrase for encrypting keyfiles.
                       If None, checks QORELOGIC_IDENTITY_PASSPHRASE env var,
                       then falls back to default (NOT SECURE for production).
        """
        env_pass = os.environ.get("QORELOGIC_IDENTITY_PASSPHRASE")
        
        # Secure storage path
        user_profile = os.environ.get("USERPROFILE") or os.environ.get("HOME")
        self.secret_dir = Path(user_profile) / ".qorelogic" / "security"
        self.secret_path = self.secret_dir / "identity.secret"
        
        if passphrase:
            self.passphrase = passphrase
        elif env_pass:
            self.passphrase = env_pass
        else:
            # Try load or generate
            if self.secret_path.exists():
                try:
                    with open(self.secret_path, 'r') as f:
                        self.passphrase = f.read().strip()
                except Exception as e:
                    print(f"❌ Error reading identity secret: {e}")
                    raise
            else:
                print("🔒 Initializing Identity Fortress...")
                self._generate_and_save_secret()
            
        # Ensure keystore exists
        KEYSTORE_DIR.mkdir(parents=True, exist_ok=True)

    def _generate_and_save_secret(self):
        """Generate a strong random passphrase and save it securely."""
        import secrets
        new_phrase = secrets.token_hex(32)
        
        try:
            self.secret_dir.mkdir(parents=True, exist_ok=True)
            # Set restrictive permissions if possible (Windows/Linux vary)
            with open(self.secret_path, 'w') as f:
                f.write(new_phrase)
            
            self.passphrase = new_phrase
            print(f"✅ Secure identity key generated at {self.secret_path}")
        except Exception as e:
            print(f"❌ Failed to save identity secret: {e}")
            # Fallback to in-memory only (ephemeral)
            self.passphrase = new_phrase
    
    def _get_cipher(self, salt: bytes, use_argon2: bool = True) -> Fernet:
        """
        Create Fernet cipher from passphrase and specific salt.
        
        Args:
            salt: Random salt for key derivation
            use_argon2: If True and available, use Argon2id (GPU-resistant).
                       Falls back to PBKDF2 if Argon2 unavailable or for legacy keys.
        
        Security Note (CRYPTOGRAPHIC_STANDARDS.md §7.2):
        Argon2id is memory-hard, providing resistance against GPU/ASIC attacks.
        PBKDF2 is retained for backward compatibility with existing keyfiles.
        """
        if use_argon2 and ARGON2_AVAILABLE:
            # Argon2id - GPU-resistant key derivation
            derived_key = hash_secret_raw(
                secret=self.passphrase.encode(),
                salt=salt,
                time_cost=ARGON2_TIME_COST,
                memory_cost=ARGON2_MEMORY_COST,
                parallelism=ARGON2_PARALLELISM,
                hash_len=ARGON2_HASH_LEN,
                type=Type.ID  # Argon2id variant
            )
            key = base64.urlsafe_b64encode(derived_key)
        else:
            # PBKDF2 fallback (legacy or when argon2 unavailable)
            kdf = PBKDF2HMAC(
                algorithm=hashes.SHA256(),
                length=32,
                salt=salt,
                iterations=100000,
                backend=default_backend()
            )
            key = base64.urlsafe_b64encode(kdf.derive(self.passphrase.encode()))
        
        return Fernet(key)
    
    def generate_did(self, role: str) -> str:
        """
        Generate a Decentralized Identifier.
        
        Note (Research: CRYPTOGRAPHIC_STANDARDS.md §6.1):
        We use 'did:myth' namespace instead of W3C 'did:key' for:
        1. Role-based identification (Sentinel, Judge, etc.)
        2. Human-readable debugging
        3. No external DID resolver dependency
        
        Format: did:myth:{role}:{nonce}
        Example: did:myth:sentinel:a1b2c3d4e5f6
        """
        nonce = hashlib.sha256(f"{role}{time.time()}".encode()).hexdigest()[:12]
        return f"did:myth:{role.lower()}:{nonce}"
    
    def generate_keypair(self) -> Tuple[Ed25519PrivateKey, Ed25519PublicKey]:
        """Generate a new Ed25519 keypair."""
        private_key = Ed25519PrivateKey.generate()
        public_key = private_key.public_key()
        return private_key, public_key
    
    def serialize_private_key(self, private_key: Ed25519PrivateKey) -> bytes:
        """Serialize private key to bytes."""
        return private_key.private_bytes(
            encoding=serialization.Encoding.Raw,
            format=serialization.PrivateFormat.Raw,
            encryption_algorithm=serialization.NoEncryption()
        )
    
    def serialize_public_key(self, public_key: Ed25519PublicKey) -> bytes:
        """Serialize public key to bytes."""
        return public_key.public_bytes(
            encoding=serialization.Encoding.Raw,
            format=serialization.PublicFormat.Raw
        )
    
    def load_private_key(self, key_bytes: bytes) -> Ed25519PrivateKey:
        """Load private key from bytes."""
        return Ed25519PrivateKey.from_private_bytes(key_bytes)
    
    def load_public_key(self, key_bytes: bytes) -> Ed25519PublicKey:
        """Load public key from bytes."""
        return Ed25519PublicKey.from_public_bytes(key_bytes)
    
    def create_agent(self, role: str) -> AgentIdentity:
        """
        Create a new agent identity with cryptographic keys.
        
        Args:
            role: Agent role (Scrivener, Sentinel, Judge, Overseer)
            
        Returns:
            AgentIdentity with DID and public key
        """
        did = self.generate_did(role)
        private_key, public_key = self.generate_keypair()
        
        # Serialize keys
        private_bytes = self.serialize_private_key(private_key)
        public_bytes = self.serialize_public_key(public_key)
        
        # Encrypt private key with fresh salt
        salt = os.urandom(16)
        cipher = self._get_cipher(salt)
        encrypted_private = cipher.encrypt(private_bytes)
        
        # Create identity
        now = time.time()
        identity = AgentIdentity(
            did=did,
            role=role,
            public_key_hex=public_bytes.hex(),
            created_at=now,
            expires_at=now + (KEY_ROTATION_DAYS * 24 * 60 * 60)
        )
        
        # Save encrypted keyfile
        keyfile_path = KEYSTORE_DIR / f"{did.replace(':', '_')}.key"
        keyfile_data = {
            "did": did,
            "role": role,
            "public_key": public_bytes.hex(),
            "private_key_encrypted": encrypted_private.decode(),
            "salt": base64.b64encode(salt).decode(),
            "kdf_algorithm": "argon2id" if ARGON2_AVAILABLE else "pbkdf2",  # Track KDF version
            "created_at": now,
            "expires_at": identity.expires_at
        }
        
        with open(keyfile_path, 'w') as f:
            json.dump(keyfile_data, f, indent=2)
        
        # Register in database
        self._register_in_db(identity, public_bytes.hex())
        
        return identity
    
    def _register_in_db(self, identity: AgentIdentity, public_key_hex: str):
        """Register agent in the database."""
        conn = sqlite3.connect(DB_PATH)
        # Check if table has trust_stage (it might if schema update worked, else ignore)
        # We just want to update keys and timestamps.
        
        try:
            # UPSERT syntax (SQLite 3.24+)
            conn.execute("""
                INSERT INTO agent_registry 
                (did, public_key, role, influence_weight, status, created_at, updated_at)
                VALUES (?, ?, ?, 1.0, 'ACTIVE', datetime('now'), datetime('now'))
                ON CONFLICT(did) DO UPDATE SET
                    public_key=excluded.public_key,
                    updated_at=excluded.updated_at
            """, (identity.did, public_key_hex, identity.role))
            conn.commit()
        finally:
            conn.close()
    
    def load_agent(self, did: str) -> Tuple[AgentIdentity, Ed25519PrivateKey]:
        """
        Load an agent identity and its private key.
        
        Args:
            did: The agent's DID
            
        Returns:
            Tuple of (AgentIdentity, Ed25519PrivateKey)
        """
        keyfile_path = KEYSTORE_DIR / f"{did.replace(':', '_')}.key"
        
        if not keyfile_path.exists():
            raise FileNotFoundError(f"Keyfile not found for {did}")
        
        with open(keyfile_path, 'r') as f:
            data = json.load(f)
        
        # Determine salt
        if "salt" in data:
            salt = base64.b64decode(data["salt"])
        else:
            salt = LEGACY_SALT
        
        # Detect KDF algorithm (legacy keys use PBKDF2, new keys use Argon2id)
        kdf_algorithm = data.get("kdf_algorithm", "pbkdf2")
        use_argon2 = (kdf_algorithm == "argon2id")
            
        # Decrypt private key using detected algorithm
        cipher = self._get_cipher(salt, use_argon2=use_argon2)
        encrypted_private = data["private_key_encrypted"].encode()
        private_bytes = cipher.decrypt(encrypted_private)
        private_key = self.load_private_key(private_bytes)
        
        identity = AgentIdentity(
            did=data["did"],
            role=data["role"],
            public_key_hex=data["public_key"],
            created_at=data["created_at"],
            expires_at=data["expires_at"]
        )
        
        return identity, private_key
    
    def sign(self, did: str, data: bytes) -> str:
        """
        Sign data with an agent's private key.
        
        Args:
            did: The signing agent's DID
            data: Data to sign
            
        Returns:
            Hex-encoded signature
        """
        identity, private_key = self.load_agent(did)
        
        if identity.is_expired():
            raise ValueError(f"Key for {did} has expired. Rotation required.")
        
        signature = private_key.sign(data)
        return signature.hex()
    
    def verify(self, did: str, data: bytes, signature_hex: str) -> bool:
        """
        Verify a signature.
        
        Args:
            did: The alleged signer's DID
            data: The signed data
            signature_hex: Hex-encoded signature
            
        Returns:
            True if valid, False otherwise
        """
        # Get public key from database
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT public_key FROM agent_registry WHERE did = ?", (did,))
        row = cursor.fetchone()
        conn.close()
        
        if not row:
            return False
        
        public_key_bytes = bytes.fromhex(row[0])
        public_key = self.load_public_key(public_key_bytes)
        
        try:
            public_key.verify(bytes.fromhex(signature_hex), data)
            return True
        except Exception:
            return False
    
    def rotate_key(self, did: str) -> AgentIdentity:
        """
        Rotate an agent's key (generate new keypair).
        
        Args:
            did: The agent's DID
            
        Returns:
            Updated AgentIdentity
        """
        # Load existing identity
        identity, old_private = self.load_agent(did)
        
        # Generate new keypair
        new_private, new_public = self.generate_keypair()
        
        # Update keyfile
        now = time.time()
        new_identity = AgentIdentity(
            did=did,
            role=identity.role,
            public_key_hex=self.serialize_public_key(new_public).hex(),
            created_at=now,
            expires_at=now + (KEY_ROTATION_DAYS * 24 * 60 * 60)
        )
        
        # Encrypt new private key with fresh salt
        salt = os.urandom(16)
        cipher = self._get_cipher(salt)
        encrypted_private = cipher.encrypt(self.serialize_private_key(new_private))
        
        keyfile_path = KEYSTORE_DIR / f"{did.replace(':', '_')}.key"
        keyfile_data = {
            "did": did,
            "role": identity.role,
            "public_key": new_identity.public_key_hex,
            "private_key_encrypted": encrypted_private.decode(),
            "salt": base64.b64encode(salt).decode(),
            "kdf_algorithm": "argon2id" if ARGON2_AVAILABLE else "pbkdf2",  # Track KDF version
            "created_at": now,
            "expires_at": new_identity.expires_at,
            "rotated_from": identity.public_key_hex  # Audit trail
        }
        
        with open(keyfile_path, 'w') as f:
            json.dump(keyfile_data, f, indent=2)
        
        # Update database
        self._register_in_db(new_identity, new_identity.public_key_hex)
        
        return new_identity
    
    def check_rotation_needed(self, did: str) -> bool:
        """Check if an agent's key needs rotation."""
        try:
            identity, _ = self.load_agent(did)
            return identity.is_expired()
        except FileNotFoundError:
            return True  # No key = needs creation


def initialize_agents():
    """Initialize the standard agent identities."""
    manager = IdentityManager()
    
    roles = ["Scrivener", "Sentinel", "Judge", "Overseer"]
    identities = []
    
    for role in roles:
        # Check if already exists
        existing_files = list(KEYSTORE_DIR.glob(f"did_myth_{role.lower()}_*.key"))
        
        if existing_files:
            # Load existing
            did = existing_files[0].stem.replace('_', ':')
            identity, _ = manager.load_agent(did)
            
            # Check rotation
            if identity.is_expired():
                print(f"⚠️ Rotating expired key for {role}...")
                identity = manager.rotate_key(did)
            else:
                print(f"✅ Loaded existing identity for {role}: {did}")
        else:
            # Create new
            identity = manager.create_agent(role)
            print(f"🔑 Created new identity for {role}: {identity.did}")
        
        identities.append(identity)
    
    return identities


if __name__ == "__main__":
    print("QoreLogic Identity Manager - Initialization")
    print("=" * 50)
    
    identities = initialize_agents()
    
    print("\n" + "=" * 50)
    print("Testing Signatures")
    print("=" * 50)
    
    manager = IdentityManager()
    
    # Test signing and verification
    test_data = b"This is a test message for QoreLogic verification."
    
    for identity in identities:
        sig = manager.sign(identity.did, test_data)
        valid = manager.verify(identity.did, test_data, sig)
        status = "✅" if valid else "❌"
        print(f"{status} {identity.role}: Signature {'valid' if valid else 'INVALID'}")
    
    print("\n🔐 Identity system initialized with Ed25519 cryptography.")
