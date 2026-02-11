from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from uuid import UUID
from decimal import Decimal
from ..models.shift import ShiftStatus


class ShiftOpen(BaseModel):
    opening_cash: Decimal = Field(..., ge=0)


class ShiftClose(BaseModel):
    counted_cash: Decimal = Field(..., ge=0)


class ShiftResponse(BaseModel):
    id: UUID
    user_id: UUID
    opened_at: datetime
    closed_at: Optional[datetime]
    opening_cash: Decimal
    expected_cash: Optional[Decimal]
    counted_cash: Optional[Decimal]
    cash_difference: Optional[Decimal]
    total_sales: Decimal
    total_mpesa: Decimal
    status: ShiftStatus
    
    class Config:
        from_attributes = True
