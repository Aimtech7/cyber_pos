from sqlalchemy import Column, String, Numeric, DateTime, ForeignKey, JSON, Boolean
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid
from ..database import Base

class MpesaPayment(Base):
    __tablename__ = "mpesa_payments"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # M-Pesa transaction details
    mpesa_receipt_number = Column(String(50), nullable=False, unique=True, index=True)
    amount = Column(Numeric(10, 2), nullable=False)
    phone_number = Column(String(15), nullable=False)
    transaction_date = Column(DateTime(timezone=True), nullable=False, index=True)
    sender_name = Column(String(200), nullable=True)
    
    # Matching status
    is_matched = Column(Boolean, default=False, nullable=False, index=True)
    matched_transaction_id = Column(UUID(as_uuid=True), ForeignKey("transactions.id"), nullable=True, index=True)
    matched_intent_id = Column(UUID(as_uuid=True), ForeignKey("payment_intents.id"), nullable=True)
    matched_at = Column(DateTime(timezone=True), nullable=True)
    matched_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    
    # Raw data
    raw_callback_data = Column(JSON, nullable=True)  # Full callback payload for debugging
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=lambda: datetime.utcnow(), nullable=False)
    
    # Relationships
    matched_transaction = relationship("Transaction", foreign_keys=[matched_transaction_id])
    matched_intent = relationship("PaymentIntent", foreign_keys=[matched_intent_id])
    matcher = relationship("User", foreign_keys=[matched_by])
    
    @property
    def is_unmatched(self) -> bool:
        """Check if payment is unmatched"""
        return not self.is_matched
