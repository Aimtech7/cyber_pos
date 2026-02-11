from sqlalchemy import Column, DateTime, Numeric, Enum, ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
import uuid
import enum
from ..database import Base


class ShiftStatus(str, enum.Enum):
    OPEN = "open"
    CLOSED = "closed"


class Shift(Base):
    __tablename__ = "shifts"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    opened_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    closed_at = Column(DateTime(timezone=True), nullable=True)
    opening_cash = Column(Numeric(10, 2), nullable=False)
    expected_cash = Column(Numeric(10, 2), nullable=True)
    counted_cash = Column(Numeric(10, 2), nullable=True)
    cash_difference = Column(Numeric(10, 2), nullable=True)
    total_sales = Column(Numeric(10, 2), default=0, nullable=False)
    total_mpesa = Column(Numeric(10, 2), default=0, nullable=False)
    status = Column(Enum(ShiftStatus), nullable=False, default=ShiftStatus.OPEN)
    closed_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    close_notes = Column(String(500), nullable=True)
    total_refunds = Column(Numeric(10, 2), default=0, nullable=False)
    
    # Relationships
    user = relationship("User", foreign_keys=[user_id])
    closed_by_user = relationship("User", foreign_keys=[closed_by])
    transactions = relationship("Transaction", back_populates="shift")
