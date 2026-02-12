from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from uuid import UUID
from decimal import Decimal
from ..models.transaction import PaymentMethod, TransactionStatus


class TransactionItemCreate(BaseModel):
    service_id: Optional[UUID] = None
    session_id: Optional[UUID] = None
    description: str = Field(..., min_length=1, max_length=500)
    quantity: Decimal = Field(..., gt=0)
    unit_price: Decimal = Field(..., ge=0)


class TransactionItemResponse(TransactionItemCreate):
    id: UUID
    transaction_id: UUID
    total_price: Decimal
    
    class Config:
        from_attributes = True


class TransactionCreate(BaseModel):
    items: List[TransactionItemCreate]
    payment_method: PaymentMethod
    mpesa_code: Optional[str] = Field(None, max_length=50)
    customer_id: Optional[UUID] = None  # Required if payment_method is ACCOUNT
    discount_amount: Decimal = Field(default=Decimal(0), ge=0)


class TransactionResponse(BaseModel):
    id: UUID
    transaction_number: int
    created_by: UUID
    shift_id: UUID
    total_amount: Decimal
    discount_amount: Decimal
    final_amount: Decimal
    payment_method: PaymentMethod
    mpesa_code: Optional[str]
    customer_id: Optional[UUID]
    invoice_id: Optional[UUID]
    status: TransactionStatus
    created_at: datetime
    updated_at: datetime
    items: List[TransactionItemResponse]
    
    class Config:
        from_attributes = True


class TransactionVoid(BaseModel):
    reason: str = Field(..., min_length=1, max_length=500)
