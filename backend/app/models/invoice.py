from sqlalchemy import Column, String, Numeric, DateTime, Enum as SQLEnum, ForeignKey, Date, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from datetime import datetime, date, timedelta
import uuid
import enum
from ..database import Base


class InvoiceStatus(str, enum.Enum):
    DRAFT = "draft"
    ISSUED = "issued"
    PART_PAID = "part_paid"
    PAID = "paid"
    OVERDUE = "overdue"
    CANCELLED = "cancelled"


class InvoicePaymentMethod(str, enum.Enum):
    CASH = "cash"
    MPESA = "mpesa"
    BANK_TRANSFER = "bank_transfer"


class Invoice(Base):
    __tablename__ = "invoices"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    invoice_number = Column(String(50), unique=True, nullable=False, index=True)
    
    # Customer link
    customer_id = Column(UUID(as_uuid=True), ForeignKey("customers.id"), nullable=False, index=True)
    
    # Status and dates
    status = Column(SQLEnum(InvoiceStatus), nullable=False, default=InvoiceStatus.DRAFT, index=True)
    issue_date = Column(Date, nullable=True)
    due_date = Column(Date, nullable=True)
    
    # Amounts
    subtotal = Column(Numeric(10, 2), nullable=False, default=0)
    tax_amount = Column(Numeric(10, 2), nullable=False, default=0)
    total_amount = Column(Numeric(10, 2), nullable=False, default=0)
    paid_amount = Column(Numeric(10, 2), nullable=False, default=0)
    
    # Notes
    notes = Column(Text, nullable=True)
    
    # Audit
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # Relationships
    customer = relationship("Customer", back_populates="invoices")
    items = relationship("InvoiceItem", back_populates="invoice", cascade="all, delete-orphan")
    payments = relationship("InvoicePayment", back_populates="invoice", cascade="all, delete-orphan")
    creator = relationship("User", foreign_keys=[created_by])
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Auto-generate invoice number if not provided
        if not self.invoice_number:
            self.invoice_number = f"INV{datetime.utcnow().strftime('%Y%m%d%H%M%S')}{str(uuid.uuid4())[:4].upper()}"
    
    @property
    def balance(self) -> float:
        """Calculate outstanding balance"""
        return float(self.total_amount - self.paid_amount)
    
    @property
    def is_overdue(self) -> bool:
        """Check if invoice is overdue"""
        if self.due_date and self.status in [InvoiceStatus.ISSUED, InvoiceStatus.PART_PAID]:
            return date.today() > self.due_date
        return False
    
    @property
    def days_overdue(self) -> int:
        """Calculate days overdue"""
        if self.is_overdue:
            return (date.today() - self.due_date).days
        return 0


class InvoiceItem(Base):
    __tablename__ = "invoice_items"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    invoice_id = Column(UUID(as_uuid=True), ForeignKey("invoices.id"), nullable=False, index=True)
    
    # Optional transaction link (if created from transaction)
    transaction_id = Column(UUID(as_uuid=True), ForeignKey("transactions.id"), nullable=True)
    
    # Item details
    description = Column(String(500), nullable=False)
    quantity = Column(Numeric(10, 2), nullable=False)
    unit_price = Column(Numeric(10, 2), nullable=False)
    total_price = Column(Numeric(10, 2), nullable=False)
    
    # Relationships
    invoice = relationship("Invoice", back_populates="items")
    transaction = relationship("Transaction", foreign_keys=[transaction_id])


class InvoicePayment(Base):
    __tablename__ = "invoice_payments"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    invoice_id = Column(UUID(as_uuid=True), ForeignKey("invoices.id"), nullable=False, index=True)
    
    # Payment details
    payment_date = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    amount = Column(Numeric(10, 2), nullable=False)
    payment_method = Column(SQLEnum(InvoicePaymentMethod), nullable=False)
    reference = Column(String(100), nullable=True)  # M-Pesa code, bank ref, etc.
    notes = Column(Text, nullable=True)
    
    # Audit
    recorded_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    
    # Relationships
    invoice = relationship("Invoice", back_populates="payments")
    recorder = relationship("User", foreign_keys=[recorded_by])
