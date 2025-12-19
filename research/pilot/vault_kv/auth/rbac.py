from enum import Enum
from typing import List, NamedTuple
import logging

logger = logging.getLogger("vault.auth")

class Role(Enum):
    ADMIN = "admin"
    USER = "user"
    VIEWER = "viewer"

class User(NamedTuple):
    username: str
    roles: List[Role]

class AccessDeniedError(Exception):
    pass

class RBAC:
    """
    Role-Based Access Control enforcer.
    """
    
    @staticmethod
    def check_permission(user: User, required_role: Role) -> bool:
        """
        Verifies if the user has the required role.
        """
        if required_role in user.roles:
            return True
        
        # Sentinel Check: Admin super-permissions
        if Role.ADMIN in user.roles:
            return True
            
        logger.warning(f"Access denied for user {user.username}. Required: {required_role}")
        return False

    @staticmethod
    def require_role(user: User, required_role: Role):
        """
        Raises exception if permission denied.
        """
        if not RBAC.check_permission(user, required_role):
            raise AccessDeniedError(f"User {user.username} lacks required role: {required_role.value}")
