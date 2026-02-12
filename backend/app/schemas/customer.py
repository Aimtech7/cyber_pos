"""
Customer Pydantic Schemas
"""
from pydantic import BaseModel, Field, EmailStr
from typing import Optional, List
from datetime import datetime
from decimal import Decimal
from uuid import UUID


class CustomerCreate(BaseModel):
    """Create customer request"""
    name: str = Field(..., min_length=1, max_length=255)
    phone: Optional[str] = Field(None, max_length=20)
    email: Optional[EmailStr] = None
    type: str = Field(..., pattern="^(individual|institution)$")
    notes: Optional[str] = None
    credit_limit: Decimal = Field(default=Decimal("0"), ge=0)


class CustomerUpdate(BaseModel):
    """Update customer request"""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    phone: Optional[str] = Field(None, max_length=20)
    email: Optional[EmailStr] = None
    type: Optional[str] = Field(None, pattern="^(individual|institution)$")
    notes: Optional[str] = None
    credit_limit: Optional[Decimal] = Field(None, ge=0)
    is_active: Optional[bool] = None


class CustomerResponse(BaseModel):
    """Customer details response"""
    id: UUID
    customer_number: str
    name: str
    phone: Optional[str]
    email: Optional[str]
    type: str
    notes: Optional[str]
    credit_limit: Decimal
    current_balance: Decimal
    available_credit: float
    is_active: bool
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class CustomerListResponse(BaseModel):
    """List customers response"""
    items: List[CustomerResponse]
    total: int
    page: int
    page_size: int


class CreditCheckRequest(BaseModel):
    """Check credit availability request"""
    amount: Decimal = Field(..., gt=0)


class CreditCheckResponse(BaseModel):
    """Credit check response"""
    customer_id: UUID
    customer_name: str
    credit_limit: Decimal
    current_balance: Decimal
    available_credit: Decimal
    requested_amount: Decimal
    can_proceed: bool
    message: str


class InvoiceSummary(BaseModel):
    """Invoice summary for customer statement"""
    id: UUID
    invoice_number: str
    status: str
    issue_date: Optional[datetime]
    due_date: Optional[datetime]
    total_amount: Decimal
    paid_amount: Decimal
    balance: Decimal
    days_overdue: int
    
    class Config:
        from_attributes = True


class PaymentSummary(BaseModel):
    """Payment summary for customer statement"""
    id: UUID
    invoice_number: str
    payment_date: datetime
    amount: Decimal
    payment_method: str
    reference: Optional[str]
    
    class Config:
        from_attributes = True


class CustomerStatement(BaseModel):
    """Customer statement with invoices and payments"""
    customer: CustomerResponse
    invoices: List[InvoiceSummary]
    total_outstanding: Decimal
    total_overdue: Decimal
    oldest_invoice_days: int
