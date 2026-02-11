from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from uuid import UUID
from decimal import Decimal
from ..models.service import PricingMode


class ServiceBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    category: Optional[str] = Field(None, max_length=50)
    pricing_mode: PricingMode
    base_price: Decimal = Field(..., ge=0)
    description: Optional[str] = Field(None, max_length=500)
    requires_stock: bool = False
    stock_item_id: Optional[UUID] = None


class ServiceCreate(ServiceBase):
    pass


class ServiceUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    category: Optional[str] = Field(None, max_length=50)
    pricing_mode: Optional[PricingMode] = None
    base_price: Optional[Decimal] = Field(None, ge=0)
    description: Optional[str] = Field(None, max_length=500)
    is_active: Optional[bool] = None
    requires_stock: Optional[bool] = None
    stock_item_id: Optional[UUID] = None


class ServiceResponse(ServiceBase):
    id: UUID
    is_active: bool
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True
