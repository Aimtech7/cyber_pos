from sqlalchemy import Column, String, Numeric, DateTime, Boolean, Enum as SQLEnum, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from datetime import datetime
import uuid
import enum
from ..database import Base


class CustomerType(str, enum.Enum):
    INDIVIDUAL = "individual"
    INSTITUTION = "institution"


class Customer(Base):
    __tablename__ = "customers"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    customer_number = Column(String(50), unique=True, nullable=False, index=True)
    
    # Customer details
    name = Column(String(255), nullable=False, index=True)
    phone = Column(String(20), nullable=True)
    email = Column(String(255), nullable=True)
    type = Column(SQLEnum(CustomerType), nullable=False, default=CustomerType.INDIVIDUAL)
    notes = Column(Text, nullable=True)
    
    # Credit management
    credit_limit = Column(Numeric(10, 2), nullable=False, default=0)
    current_balance = Column(Numeric(10, 2), nullable=False, default=0)  # Outstanding amount
    
    # Status
    is_active = Column(Boolean, default=True, nullable=False, index=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # Relationships
    invoices = relationship("Invoice", back_populates="customer")
    transactions = relationship("Transaction", back_populates="customer")
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Auto-generate customer number if not provided
        if not self.customer_number:
            self.customer_number = f"CUST{datetime.utcnow().strftime('%Y%m%d%H%M%S')}{str(uuid.uuid4())[:4].upper()}"
    
    @property
    def available_credit(self) -> float:
        """Calculate available credit"""
        return float(self.credit_limit - self.current_balance)
    
    @property
    def has_outstanding_balance(self) -> bool:
        """Check if customer has outstanding balance"""
        return self.current_balance > 0
