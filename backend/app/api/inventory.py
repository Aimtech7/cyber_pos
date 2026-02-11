from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from uuid import UUID
from ..database import get_db
from ..schemas.inventory import (
    InventoryItemCreate,
    InventoryItemUpdate,
    InventoryItemResponse,
    StockMovementCreate,
    StockMovementResponse
)
from ..models.inventory import InventoryItem, StockMovement
from ..models.user import User
from ..core.permissions import Permission
from ..api.deps import get_current_user, require_permission

router = APIRouter(prefix="/inventory", tags=["Inventory"])


@router.get("/", response_model=List[InventoryItemResponse])
async def list_inventory_items(
    skip: int = 0,
    limit: int = 100,
    low_stock_only: bool = False,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """List inventory items"""
    query = db.query(InventoryItem)
    
    if low_stock_only:
        query = query.filter(InventoryItem.current_stock <= InventoryItem.min_stock_level)
    
    items = query.offset(skip).limit(limit).all()
    return items


@router.post("/", response_model=InventoryItemResponse, status_code=status.HTTP_201_CREATED)
async def create_inventory_item(
    item_data: InventoryItemCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission(Permission.MANAGE_INVENTORY))
):
    """Create a new inventory item"""
    item = InventoryItem(**item_data.model_dump())
    db.add(item)
    db.commit()
    db.refresh(item)
    return item


@router.patch("/{item_id}", response_model=InventoryItemResponse)
async def update_inventory_item(
    item_id: UUID,
    item_data: InventoryItemUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission(Permission.MANAGE_INVENTORY))
):
    """Update inventory item"""
    item = db.query(InventoryItem).filter(InventoryItem.id == item_id).first()
    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Inventory item not found"
        )
    
    update_data = item_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(item, field, value)
    
    db.commit()
    db.refresh(item)
    return item


@router.post("/movements", response_model=StockMovementResponse)
async def create_stock_movement(
    movement_data: StockMovementCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission(Permission.MANAGE_INVENTORY))
):
    """Create a stock movement (purchase or adjustment)"""
    item = db.query(InventoryItem).filter(InventoryItem.id == movement_data.item_id).first()
    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Inventory item not found"
        )
    
    # Update stock
    item.current_stock += movement_data.quantity
    
    # Create movement record
    movement = StockMovement(
        **movement_data.model_dump(),
        created_by=current_user.id
    )
    db.add(movement)
    db.commit()
    db.refresh(movement)
    
    return movement


@router.get("/movements/{item_id}", response_model=List[StockMovementResponse])
async def get_stock_movements(
    item_id: UUID,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get stock movements for an item"""
    movements = db.query(StockMovement).filter(
        StockMovement.item_id == item_id
    ).order_by(StockMovement.created_at.desc()).offset(skip).limit(limit).all()
    
    return movements
