from sqlalchemy import Column, String, Boolean, DateTime, Numeric, Enum, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
import uuid
import enum
from ..database import Base


class PricingMode(str, enum.Enum):
    PER_PAGE = "per_page"
    PER_MINUTE = "per_minute"
    PER_JOB = "per_job"
    BUNDLE = "bundle"


class Service(Base):
    __tablename__ = "services"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False, index=True)
    pricing_mode = Column(Enum(PricingMode), nullable=False)
    base_price = Column(Numeric(10, 2), nullable=False)
    description = Column(String(500))
    is_active = Column(Boolean, default=True, nullable=False)
    requires_stock = Column(Boolean, default=False, nullable=False)
    stock_item_id = Column(UUID(as_uuid=True), ForeignKey("inventory_items.id"), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # Relationships
    stock_item = relationship("InventoryItem", back_populates="services")
