from sqlalchemy import Column, String, DateTime, Numeric, Enum, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
import uuid
import enum
from ..database import Base


class MovementType(str, enum.Enum):
    PURCHASE = "purchase"
    USAGE = "usage"
    ADJUSTMENT = "adjustment"


class InventoryItem(Base):
    __tablename__ = "inventory_items"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False, index=True)
    unit = Column(String(50), nullable=False)
    current_stock = Column(Numeric(10, 2), nullable=False, default=0)
    min_stock_level = Column(Numeric(10, 2), nullable=False, default=0)
    unit_cost = Column(Numeric(10, 2), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # Future Hooks
    tenant_id = Column(String(50), nullable=True, index=True)
    
    # Relationships
    movements = relationship("StockMovement", back_populates="item")
    services = relationship("Service", back_populates="stock_item")


class StockMovement(Base):
    __tablename__ = "stock_movements"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    item_id = Column(UUID(as_uuid=True), ForeignKey("inventory_items.id"), nullable=False)
    movement_type = Column(Enum(MovementType), nullable=False)
    quantity = Column(Numeric(10, 2), nullable=False)
    reference_id = Column(String(255), nullable=True)
    notes = Column(String(500))
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)
    
    # Future Hooks
    tenant_id = Column(String(50), nullable=True, index=True)
    
    # Relationships
    item = relationship("InventoryItem", back_populates="movements")
    user = relationship("User")
