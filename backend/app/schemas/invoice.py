"""
Invoice Pydantic Schemas
"""
from pydantic import BaseModel, Field
from typing import Optional, List, Dict
from datetime import datetime, date
from decimal import Decimal
from uuid import UUID


class InvoiceItemCreate(BaseModel):
    """Create invoice item"""
    transaction_id: Optional[UUID] = None
    description: str = Field(..., min_length=1, max_length=500)
    quantity: Decimal = Field(..., gt=0)
    unit_price: Decimal = Field(..., ge=0)
    total_price: Decimal = Field(..., ge=0)


class InvoiceItemResponse(BaseModel):
    """Invoice item response"""
    id: UUID
    invoice_id: UUID
    transaction_id: Optional[UUID]
    description: str
    quantity: Decimal
    unit_price: Decimal
    total_price: Decimal
    
    class Config:
        from_attributes = True


class InvoiceCreate(BaseModel):
    """Create invoice request"""
    customer_id: UUID
    items: List[InvoiceItemCreate]
    due_days: int = Field(default=30, ge=0)  # Days until due
    notes: Optional[str] = None
    issue_immediately: bool = False  # If True, issue invoice immediately


class InvoiceUpdate(BaseModel):
    """Update invoice request"""
    due_date: Optional[date] = None
    notes: Optional[str] = None


class InvoiceResponse(BaseModel):
    """Invoice details response"""
    id: UUID
    invoice_number: str
    customer_id: UUID
    status: str
    issue_date: Optional[date]
    due_date: Optional[date]
    subtotal: Decimal
    tax_amount: Decimal
    total_amount: Decimal
    paid_amount: Decimal
    balance: float
    notes: Optional[str]
    created_by: UUID
    created_at: datetime
    updated_at: datetime
    is_overdue: bool
    days_overdue: int
    items: List[InvoiceItemResponse] = []
    
    class Config:
        from_attributes = True


class InvoiceListResponse(BaseModel):
    """List invoices response"""
    items: List[InvoiceResponse]
    total: int
    page: int
    page_size: int


class InvoicePaymentCreate(BaseModel):
    """Record invoice payment request"""
    amount: Decimal = Field(..., gt=0)
    payment_method: str = Field(..., pattern="^(cash|mpesa|bank_transfer)$")
    reference: Optional[str] = Field(None, max_length=100)
    notes: Optional[str] = None


class InvoicePaymentResponse(BaseModel):
    """Invoice payment response"""
    id: UUID
    invoice_id: UUID
    payment_date: datetime
    amount: Decimal
    payment_method: str
    reference: Optional[str]
    notes: Optional[str]
    recorded_by: UUID
    created_at: datetime
    
    class Config:
        from_attributes = True


class CreateInvoiceFromTransactions(BaseModel):
    """Create invoice from existing transactions"""
    customer_id: UUID
    transaction_ids: List[UUID] = Field(..., min_items=1)
    due_days: int = Field(default=30, ge=0)
    notes: Optional[str] = None
    issue_immediately: bool = True


class AgingBucket(BaseModel):
    """Aging report bucket"""
    range_label: str  # e.g., "0-30 days"
    count: int
    total_amount: Decimal


class AgingReportResponse(BaseModel):
    """Aging report response"""
    customer_id: Optional[UUID] = None
    customer_name: Optional[str] = None
    buckets: Dict[str, AgingBucket]  # Keys: "0-30", "31-60", "61-90", "90+"
    total_outstanding: Decimal
    total_invoices: int


class IssueInvoiceRequest(BaseModel):
    """Issue invoice request (DRAFT -> ISSUED)"""
    pass  # Empty, action only


class CancelInvoiceRequest(BaseModel):
    """Cancel invoice request"""
    reason: Optional[str] = None
