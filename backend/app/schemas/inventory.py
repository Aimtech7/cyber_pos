from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from uuid import UUID
from decimal import Decimal
from ..models.inventory import MovementType


class InventoryItemBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    unit: str = Field(..., min_length=1, max_length=50)
    min_stock_level: Decimal = Field(..., ge=0)
    unit_cost: Decimal = Field(..., ge=0)


class InventoryItemCreate(InventoryItemBase):
    current_stock: Decimal = Field(default=Decimal(0), ge=0)


class InventoryItemUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    unit: Optional[str] = Field(None, min_length=1, max_length=50)
    min_stock_level: Optional[Decimal] = Field(None, ge=0)
    unit_cost: Optional[Decimal] = Field(None, ge=0)


class InventoryItemResponse(InventoryItemBase):
    id: UUID
    current_stock: Decimal
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class StockMovementCreate(BaseModel):
    item_id: UUID
    movement_type: MovementType
    quantity: Decimal
    reference_id: Optional[str] = Field(None, max_length=255)
    notes: Optional[str] = Field(None, max_length=500)


class StockMovementResponse(StockMovementCreate):
    id: UUID
    created_by: UUID
    created_at: datetime
    
    class Config:
        from_attributes = True
