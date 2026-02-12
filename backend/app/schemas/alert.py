"""
Pydantic schemas for Alert model
"""
from typing import Optional, Dict, Any, List
from datetime import datetime
from pydantic import BaseModel, Field
from enum import Enum


class AlertTypeEnum(str, Enum):
    """Alert types"""
    VOID_ABUSE = "void_abuse"
    DISCOUNT_ABUSE = "discount_abuse"
    CASH_DISCREPANCY = "cash_discrepancy"
    INVENTORY_MANIPULATION = "inventory_manipulation"
    PRICE_TAMPERING = "price_tampering"


class AlertSeverityEnum(str, Enum):
    """Alert severity levels"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class AlertStatusEnum(str, Enum):
    """Alert status"""
    OPEN = "open"
    ACKNOWLEDGED = "acknowledged"
    RESOLVED = "resolved"


class AlertCreate(BaseModel):
    """Schema for creating an alert"""
    type: AlertTypeEnum
    severity: AlertSeverityEnum
    message: str
    description: Optional[str] = None
    related_entity: Optional[Dict[str, Any]] = None
    metadata: Optional[Dict[str, Any]] = None
    assigned_to: Optional[str] = None


class AlertUpdate(BaseModel):
    """Schema for updating an alert"""
    assigned_to: Optional[str] = None
    resolution_notes: Optional[str] = None


class AlertAcknowledge(BaseModel):
    """Schema for acknowledging an alert"""
    notes: Optional[str] = None


class AlertResolve(BaseModel):
    """Schema for resolving an alert"""
    resolution_notes: str


class AlertResponse(BaseModel):
    """Schema for alert response"""
    id: str
    type: AlertTypeEnum
    severity: AlertSeverityEnum
    status: AlertStatusEnum
    message: str
    description: Optional[str]
    related_entity: Optional[Dict[str, Any]]
    metadata: Optional[Dict[str, Any]]
    assigned_to: Optional[str]
    acknowledged_by: Optional[str]
    acknowledged_at: Optional[datetime]
    resolved_by: Optional[str]
    resolved_at: Optional[datetime]
    resolution_notes: Optional[str]
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class AlertListResponse(BaseModel):
    """Schema for paginated alert list"""
    items: List[AlertResponse]
    total: int
    page: int
    page_size: int
    pages: int


class AlertStats(BaseModel):
    """Schema for alert statistics"""
    total_open: int
    total_acknowledged: int
    total_resolved: int
    by_severity: Dict[str, int]
    by_type: Dict[str, int]
    critical_open: int
    high_open: int
