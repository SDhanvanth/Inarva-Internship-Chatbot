"""
Role-Based Access Control (RBAC) implementation.
"""
from enum import Enum
from typing import List, Optional, Set
from functools import wraps

from app.models.user import UserRole


class Permission(str, Enum):
    """System permissions."""
    # User permissions
    READ_PROFILE = "read:profile"
    UPDATE_PROFILE = "update:profile"
    
    # Chat permissions
    CREATE_CHAT = "create:chat"
    READ_CHAT = "read:chat"
    DELETE_CHAT = "delete:chat"
    
    # Marketplace permissions
    BROWSE_MARKETPLACE = "browse:marketplace"
    ENABLE_APP = "enable:app"
    DISABLE_APP = "disable:app"
    
    # Developer permissions
    CREATE_APP = "create:app"
    UPDATE_APP = "update:app"
    DELETE_APP = "delete:app"
    VIEW_APP_STATS = "view:app_stats"
    
    # Admin permissions
    MANAGE_USERS = "manage:users"
    MODERATE_APPS = "moderate:apps"
    VIEW_SYSTEM = "view:system"
    VIEW_LOGS = "view:logs"
    MANAGE_CONFIG = "manage:config"


# Role to permissions mapping
ROLE_PERMISSIONS: dict[UserRole, Set[Permission]] = {
    UserRole.USER: {
        Permission.READ_PROFILE,
        Permission.UPDATE_PROFILE,
        Permission.CREATE_CHAT,
        Permission.READ_CHAT,
        Permission.DELETE_CHAT,
        Permission.BROWSE_MARKETPLACE,
        Permission.ENABLE_APP,
        Permission.DISABLE_APP,
    },
    UserRole.DEVELOPER: {
        # All user permissions
        Permission.READ_PROFILE,
        Permission.UPDATE_PROFILE,
        Permission.CREATE_CHAT,
        Permission.READ_CHAT,
        Permission.DELETE_CHAT,
        Permission.BROWSE_MARKETPLACE,
        Permission.ENABLE_APP,
        Permission.DISABLE_APP,
        # Developer-specific
        Permission.CREATE_APP,
        Permission.UPDATE_APP,
        Permission.DELETE_APP,
        Permission.VIEW_APP_STATS,
    },
    UserRole.ADMIN: {
        # All permissions
        Permission.READ_PROFILE,
        Permission.UPDATE_PROFILE,
        Permission.CREATE_CHAT,
        Permission.READ_CHAT,
        Permission.DELETE_CHAT,
        Permission.BROWSE_MARKETPLACE,
        Permission.ENABLE_APP,
        Permission.DISABLE_APP,
        Permission.CREATE_APP,
        Permission.UPDATE_APP,
        Permission.DELETE_APP,
        Permission.VIEW_APP_STATS,
        Permission.MANAGE_USERS,
        Permission.MODERATE_APPS,
        Permission.VIEW_SYSTEM,
        Permission.VIEW_LOGS,
        Permission.MANAGE_CONFIG,
    },
}


def get_permissions(role: UserRole) -> Set[Permission]:
    """Get all permissions for a role."""
    return ROLE_PERMISSIONS.get(role, set())


def has_permission(role: UserRole, permission: Permission) -> bool:
    """Check if a role has a specific permission."""
    return permission in get_permissions(role)


def has_any_permission(role: UserRole, permissions: List[Permission]) -> bool:
    """Check if a role has any of the given permissions."""
    role_perms = get_permissions(role)
    return any(p in role_perms for p in permissions)


def has_all_permissions(role: UserRole, permissions: List[Permission]) -> bool:
    """Check if a role has all of the given permissions."""
    role_perms = get_permissions(role)
    return all(p in role_perms for p in permissions)


class RBACChecker:
    """RBAC checker for use in FastAPI dependencies."""
    
    def __init__(
        self,
        required_permissions: Optional[List[Permission]] = None,
        required_roles: Optional[List[UserRole]] = None,
        require_all: bool = False
    ):
        self.required_permissions = required_permissions or []
        self.required_roles = required_roles or []
        self.require_all = require_all
    
    def check(self, user_role: UserRole) -> bool:
        """Check if user has required access."""
        # Check role requirement
        if self.required_roles and user_role not in self.required_roles:
            return False
        
        # Check permission requirements
        if self.required_permissions:
            if self.require_all:
                return has_all_permissions(user_role, self.required_permissions)
            else:
                return has_any_permission(user_role, self.required_permissions)
        
        return True


# Pre-defined checkers for common use cases
require_user = RBACChecker(required_roles=[UserRole.USER, UserRole.DEVELOPER, UserRole.ADMIN])
require_developer = RBACChecker(required_roles=[UserRole.DEVELOPER, UserRole.ADMIN])
require_admin = RBACChecker(required_roles=[UserRole.ADMIN])

require_chat_access = RBACChecker(required_permissions=[Permission.CREATE_CHAT])
require_marketplace_access = RBACChecker(required_permissions=[Permission.BROWSE_MARKETPLACE])
require_app_management = RBACChecker(required_permissions=[Permission.CREATE_APP])
require_system_access = RBACChecker(required_permissions=[Permission.VIEW_SYSTEM])
