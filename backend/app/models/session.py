from sqlalchemy import Column, String, DateTime, Numeric, Enum, ForeignKey, Integer
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
import uuid
import enum
from ..database import Base


class SessionStatus(str, enum.Enum):
    ACTIVE = "active"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class Session(Base):
    __tablename__ = "sessions"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    computer_id = Column(UUID(as_uuid=True), ForeignKey("computers.id"), nullable=False, index=True)
    started_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    start_time = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    end_time = Column(DateTime(timezone=True), nullable=True)
    duration_minutes = Column(Integer, nullable=True)
    amount_charged = Column(Numeric(10, 2), nullable=True)
    transaction_id = Column(UUID(as_uuid=True), ForeignKey("transactions.id"), nullable=True)
    status = Column(Enum(SessionStatus), nullable=False, default=SessionStatus.ACTIVE)
    
    # Future Hooks
    tenant_id = Column(String(50), nullable=True, index=True)
    
    # Relationships
    computer = relationship("Computer", foreign_keys=[computer_id], back_populates="sessions")
    user = relationship("User")
    transaction = relationship("Transaction", back_populates="sessions")
