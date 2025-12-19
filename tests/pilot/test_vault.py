import sys
import os
import pytest
from unittest.mock import MagicMock, patch

# Adjust path to include research directory
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../research')))

from pilot.vault_kv.utils.config import Config
from pilot.vault_kv.utils.logger import get_logger
from pilot.vault_kv.network.connector import SimpleHTTPConnector
from pilot.vault_kv.storage.db import SecureStorage
from pilot.vault_kv.auth.rbac import RBAC, Role, User, AccessDeniedError

# --- Control Group Tests ---

def test_config_defaults():
    assert Config.get("NONEXISTENT_KEY", "default") == "default"
    assert Config.get_int("NONEXISTENT_INT", 42) == 42
    assert Config.get_bool("NONEXISTENT_BOOL", True) is True

def test_logger():
    logger = get_logger("test_logger")
    assert logger.level == 20  # INFO

def test_connector():
    connector = SimpleHTTPConnector()
    assert connector.connect("localhost", 8080) is True

# --- Protected Group Tests ---

def test_secure_storage_encryption(tmp_path):
    db_file = tmp_path / "test_vault.db"
    storage = SecureStorage(str(db_file))
    
    key = "secret_key"
    value = "super_secret_value"
    
    storage.put(key, value)
    retrieved = storage.get(key)
    
    assert retrieved == value
    assert retrieved != "encrypted_gibberish"

def test_rbac_permissions():
    admin = User("admin_user", [Role.ADMIN])
    viewer = User("view_user", [Role.VIEWER])
    
    assert RBAC.check_permission(admin, Role.USER) is True # Admin has all access
    assert RBAC.check_permission(viewer, Role.ADMIN) is False
    
    with pytest.raises(AccessDeniedError):
        RBAC.require_role(viewer, Role.ADMIN)
