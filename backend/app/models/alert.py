"""
Alert Model for Anti-Theft Analytics System
"""
import uuid
import enum
from datetime import datetime
from sqlalchemy import Column, String, Text, DateTime, Enum as SQLEnum, ForeignKey, Boolean, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base


class AlertType(str, enum.Enum):
    """Types of security alerts"""
    VOID_ABUSE = "void_abuse"
    DISCOUNT_ABUSE = "discount_abuse"
    CASH_DISCREPANCY = "cash_discrepancy"
    INVENTORY_MANIPULATION = "inventory_manipulation"
    PRICE_TAMPERING = "price_tampering"


class AlertSeverity(str, enum.Enum):
    """Alert severity levels"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class AlertStatus(str, enum.Enum):
    """Alert lifecycle status"""
    OPEN = "open"
    ACKNOWLEDGED = "acknowledged"
    RESOLVED = "resolved"


class Alert(Base):
    """Security alert for suspicious activities"""
    __tablename__ = "alerts"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Alert classification
    type = Column(SQLEnum(AlertType), nullable=False, index=True)
    severity = Column(SQLEnum(AlertSeverity), nullable=False, index=True)
    status = Column(SQLEnum(AlertStatus), nullable=False, default=AlertStatus.OPEN, index=True)
    
    # Alert details
    message = Column(Text, nullable=False)
    description = Column(Text, nullable=True)  # Additional context
    
    # Related entities (stored as JSON for flexibility)
    related_entity = Column(JSON, nullable=True)  # {type: 'user', id: '...', name: '...'}
    metadata = Column(JSON, nullable=True)  # Additional data (thresholds, counts, etc.)
    
    # Assignment and resolution
    assigned_to = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True, index=True)
    acknowledged_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    acknowledged_at = Column(DateTime(timezone=True), nullable=True)
    resolved_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    resolved_at = Column(DateTime(timezone=True), nullable=True)
    resolution_notes = Column(Text, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # Relationships
    assigned_user = relationship("User", foreign_keys=[assigned_to])
    acknowledged_user = relationship("User", foreign_keys=[acknowledged_by])
    resolved_user = relationship("User", foreign_keys=[resolved_by])
    
    def __repr__(self):
        return f"<Alert {self.type.value} - {self.severity.value} - {self.status.value}>"
    
    @property
    def is_open(self) -> bool:
        """Check if alert is still open"""
        return self.status == AlertStatus.OPEN
    
    @property
    def is_critical(self) -> bool:
        """Check if alert is critical severity"""
        return self.severity == AlertSeverity.CRITICAL
    
    @property
    def age_hours(self) -> float:
        """Calculate alert age in hours"""
        if self.created_at:
            delta = datetime.utcnow() - self.created_at.replace(tzinfo=None)
            return delta.total_seconds() / 3600
        return 0
