from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime, date
from uuid import UUID
from decimal import Decimal
from ..models.expense import ExpenseCategory


class ExpenseBase(BaseModel):
    category: ExpenseCategory
    description: str = Field(..., min_length=1, max_length=500)
    amount: Decimal = Field(..., gt=0)
    expense_date: date


class ExpenseCreate(ExpenseBase):
    pass


class ExpenseUpdate(BaseModel):
    category: Optional[ExpenseCategory] = None
    description: Optional[str] = Field(None, min_length=1, max_length=500)
    amount: Optional[Decimal] = Field(None, gt=0)
    expense_date: Optional[date] = None


class ExpenseResponse(ExpenseBase):
    id: UUID
    recorded_by: UUID
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True
