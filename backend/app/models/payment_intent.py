from sqlalchemy import Column, String, Numeric, DateTime, Enum as SQLEnum, ForeignKey, JSON, Boolean
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from datetime import datetime, timedelta
import uuid
import enum
from ..database import Base

class PaymentIntentStatus(str, enum.Enum):
    PENDING = "pending"
    CONFIRMED = "confirmed"
    FAILED = "failed"
    EXPIRED = "expired"
    CANCELLED = "cancelled"

class PaymentIntent(Base):
    __tablename__ = "payment_intents"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    transaction_id = Column(UUID(as_uuid=True), ForeignKey("transactions.id"), nullable=False, index=True)
    
    # Payment details
    amount = Column(Numeric(10, 2), nullable=False)
    phone_number = Column(String(15), nullable=False)  # 254XXXXXXXXX format
    
    # Status tracking
    status = Column(SQLEnum(PaymentIntentStatus), nullable=False, default=PaymentIntentStatus.PENDING, index=True)
    
    # M-Pesa STK Push tracking
    mpesa_request_id = Column(String(100), nullable=True)  # From initiate response
    mpesa_checkout_request_id = Column(String(100), nullable=True, unique=True, index=True)  # For callback matching
    
    # M-Pesa confirmation data
    mpesa_receipt_number = Column(String(50), nullable=True, index=True)  # Final receipt number
    mpesa_transaction_date = Column(DateTime(timezone=True), nullable=True)
    
    # Additional data
    callback_data = Column(JSON, nullable=True)  # Full callback payload
    failure_reason = Column(String(500), nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=lambda: datetime.utcnow(), nullable=False)
    expires_at = Column(DateTime(timezone=True), nullable=False, index=True)  # 90 seconds from creation
    confirmed_at = Column(DateTime(timezone=True), nullable=True)
    
    # Audit
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    
    # Relationships
    transaction = relationship("Transaction", back_populates="payment_intents")
    creator = relationship("User", foreign_keys=[created_by])
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Auto-set expiry to 90 seconds from now if not provided
        if not self.expires_at:
            self.expires_at = datetime.utcnow() + timedelta(seconds=90)
    
    @property
    def is_expired(self) -> bool:
        """Check if payment intent has expired"""
        return datetime.utcnow() > self.expires_at and self.status == PaymentIntentStatus.PENDING
    
    @property
    def is_pending(self) -> bool:
        """Check if payment is still pending"""
        return self.status == PaymentIntentStatus.PENDING and not self.is_expired
