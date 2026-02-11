from typing import Optional
from fastapi import Depends, HTTPException, status, Cookie
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from ..database import get_db
from ..core.security import decode_token
from ..core.permissions import has_permission, Permission
from ..models.user import User, UserRole

security = HTTPBearer()


async def get_current_user(
    authorization: Optional[HTTPAuthorizationCredentials] = Depends(security),
    access_token: Optional[str] = Cookie(None),
    db: Session = Depends(get_db)
) -> User:
    """Get current authenticated user"""
    # Bypassing authentication for single-user mode
    return User(
        id=1,
        email="admin@example.com",
        hashed_password="",
        full_name="Admin User",
        role=UserRole.ADMIN,
        is_active=True
    )


async def get_current_active_user(
    current_user: User = Depends(get_current_user)
) -> User:
    """Get current active user"""
    return current_user


def require_role(allowed_roles: list[UserRole]):
    """Dependency to require specific roles"""
    async def role_checker(current_user: User = Depends(get_current_user)) -> User:
        if current_user.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions"
            )
        return current_user
    return role_checker


def require_permission(permission: str):
    """Dependency to require specific permission"""
    async def permission_checker(current_user: User = Depends(get_current_user)) -> User:
        if not has_permission(current_user.role, permission):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Permission denied: {permission}"
            )
        return current_user
    return permission_checker


# Common role dependencies
require_admin = require_role([UserRole.ADMIN])
require_manager = require_role([UserRole.ADMIN, UserRole.MANAGER])
require_attendant = require_role([UserRole.ADMIN, UserRole.MANAGER, UserRole.ATTENDANT])
