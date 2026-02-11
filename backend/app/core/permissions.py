from typing import List
from ..models.user import UserRole


class Permission:
    """Permission definitions for RBAC"""
    
    # User management
    CREATE_USER = "create_user"
    UPDATE_USER = "update_user"
    DELETE_USER = "delete_user"
    VIEW_USERS = "view_users"
    
    # Service management
    CREATE_SERVICE = "create_service"
    UPDATE_SERVICE = "update_service"
    DELETE_SERVICE = "delete_service"
    
    # Pricing
    APPLY_DISCOUNT = "apply_discount"
    OVERRIDE_PRICE = "override_price"
    
    # Transactions
    VOID_TRANSACTION = "void_transaction"
    REFUND_TRANSACTION = "refund_transaction"
    VIEW_ALL_TRANSACTIONS = "view_all_transactions"
    
    # Reports
    VIEW_REPORTS = "view_reports"
    EXPORT_REPORTS = "export_reports"
    
    # Inventory
    MANAGE_INVENTORY = "manage_inventory"
    
    # Expenses
    MANAGE_EXPENSES = "manage_expenses"
    
    # Computers
    MANAGE_COMPUTERS = "manage_computers"
    
    # Shifts
    VIEW_ALL_SHIFTS = "view_all_shifts"


# Role-based permissions mapping
ROLE_PERMISSIONS = {
    UserRole.ADMIN: [
        # Full access to everything
        Permission.CREATE_USER,
        Permission.UPDATE_USER,
        Permission.DELETE_USER,
        Permission.VIEW_USERS,
        Permission.CREATE_SERVICE,
        Permission.UPDATE_SERVICE,
        Permission.DELETE_SERVICE,
        Permission.APPLY_DISCOUNT,
        Permission.OVERRIDE_PRICE,
        Permission.VOID_TRANSACTION,
        Permission.REFUND_TRANSACTION,
        Permission.VIEW_ALL_TRANSACTIONS,
        Permission.VIEW_REPORTS,
        Permission.EXPORT_REPORTS,
        Permission.MANAGE_INVENTORY,
        Permission.MANAGE_EXPENSES,
        Permission.MANAGE_COMPUTERS,
        Permission.VIEW_ALL_SHIFTS,
    ],
    UserRole.MANAGER: [
        # Most access except user management
        Permission.VIEW_USERS,
        Permission.CREATE_SERVICE,
        Permission.UPDATE_SERVICE,
        Permission.DELETE_SERVICE,
        Permission.APPLY_DISCOUNT,
        Permission.OVERRIDE_PRICE,
        Permission.VOID_TRANSACTION,
        Permission.REFUND_TRANSACTION,
        Permission.VIEW_ALL_TRANSACTIONS,
        Permission.VIEW_REPORTS,
        Permission.EXPORT_REPORTS,
        Permission.MANAGE_INVENTORY,
        Permission.MANAGE_EXPENSES,
        Permission.MANAGE_COMPUTERS,
        Permission.VIEW_ALL_SHIFTS,
    ],
    UserRole.ATTENDANT: [
        # Basic POS operations only
        Permission.VIEW_REPORTS,  # Own reports only
    ],
}


def has_permission(user_role: UserRole, permission: str) -> bool:
    """Check if a role has a specific permission"""
    return permission in ROLE_PERMISSIONS.get(user_role, [])


def has_any_permission(user_role: UserRole, permissions: List[str]) -> bool:
    """Check if a role has any of the specified permissions"""
    role_perms = ROLE_PERMISSIONS.get(user_role, [])
    return any(perm in role_perms for perm in permissions)


def has_all_permissions(user_role: UserRole, permissions: List[str]) -> bool:
    """Check if a role has all of the specified permissions"""
    role_perms = ROLE_PERMISSIONS.get(user_role, [])
    return all(perm in role_perms for perm in permissions)
