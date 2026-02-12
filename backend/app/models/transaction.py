from sqlalchemy import Column, String, DateTime, Numeric, Enum, ForeignKey, Integer
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
import uuid
import enum
from ..database import Base


class PaymentMethod(str, enum.Enum):
    CASH = "cash"
    MPESA = "mpesa"
    ACCOUNT = "account"  # Customer account payment


class TransactionStatus(str, enum.Enum):
    COMPLETED = "completed"
    VOIDED = "voided"
    REFUNDED = "refunded"


class Transaction(Base):
    __tablename__ = "transactions"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    transaction_number = Column(Integer, nullable=False, unique=True, index=True)
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    shift_id = Column(UUID(as_uuid=True), ForeignKey("shifts.id"), nullable=False)
    total_amount = Column(Numeric(10, 2), nullable=False)
    discount_amount = Column(Numeric(10, 2), default=0, nullable=False)
    final_amount = Column(Numeric(10, 2), nullable=False)
    payment_method = Column(Enum(PaymentMethod), nullable=False)
    mpesa_code = Column(String(50), nullable=True)
    status = Column(Enum(TransactionStatus), nullable=False, default=TransactionStatus.COMPLETED)
    
    # Customer account payment
    customer_id = Column(UUID(as_uuid=True), ForeignKey("customers.id"), nullable=True, index=True)
    invoice_id = Column(UUID(as_uuid=True), ForeignKey("invoices.id"), nullable=True, index=True)
    
    # Offline mode support (for idempotency and sync)
    client_generated_id = Column(UUID(as_uuid=True), unique=True, nullable=True, index=True)  # Client UUID for idempotency
    offline_receipt_number = Column(String(50), nullable=True, index=True)  # Temporary offline receipt (OFF-YYYYMMDD-xxxx)
    synced_at = Column(DateTime(timezone=True), nullable=True)  # When offline transaction was synced
    
    # Security: Receipt tamper detection
    receipt_hash = Column(String(64), nullable=True, index=True)  # SHA-256 hash for tamper detection
    
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # Future Hooks (Single Tenant Default)
    tenant_id = Column(String(50), nullable=True, index=True)
    branch_id = Column(String(50), nullable=True, default="Main")
    
    # Relationships
    user = relationship("User", foreign_keys=[created_by])
    shift = relationship("Shift", back_populates="transactions")
    customer = relationship("Customer", back_populates="transactions")
    invoice = relationship("Invoice", foreign_keys=[invoice_id])
    transaction_items = relationship("TransactionItem", back_populates="transaction", cascade="all, delete-orphan")
    payment_intents = relationship("PaymentIntent", back_populates="transaction", cascade="all, delete-orphan")
    sessions = relationship("Session", back_populates="transaction")


class TransactionItem(Base):
    __tablename__ = "transaction_items"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    transaction_id = Column(UUID(as_uuid=True), ForeignKey("transactions.id"), nullable=False, index=True)
    service_id = Column(UUID(as_uuid=True), ForeignKey("services.id"), nullable=True)
    session_id = Column(UUID(as_uuid=True), ForeignKey("sessions.id"), nullable=True)
    description = Column(String(500), nullable=False)
    quantity = Column(Numeric(10, 2), nullable=False)
    unit_price = Column(Numeric(10, 2), nullable=False)
    total_price = Column(Numeric(10, 2), nullable=False)
    
    # Relationships
    transaction = relationship("Transaction", back_populates="items")
    service = relationship("Service")
    session = relationship("Session")
