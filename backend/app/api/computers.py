from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from uuid import UUID
from ..database import get_db
from ..schemas.computer import ComputerCreate, ComputerUpdate, ComputerResponse
from ..models.computer import Computer
from ..models.user import User
from ..core.permissions import Permission
from ..api.deps import get_current_user, require_permission

router = APIRouter(prefix="/computers", tags=["Computers"])


@router.get("/", response_model=List[ComputerResponse])
async def list_computers(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """List all computers"""
    computers = db.query(Computer).all()
    return computers


@router.get("/{computer_id}", response_model=ComputerResponse)
async def get_computer(
    computer_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get computer by ID"""
    computer = db.query(Computer).filter(Computer.id == computer_id).first()
    if not computer:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Computer not found"
        )
    return computer


@router.post("/", response_model=ComputerResponse, status_code=status.HTTP_201_CREATED)
async def create_computer(
    computer_data: ComputerCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission(Permission.MANAGE_COMPUTERS))
):
    """Create a new computer"""
    # Check if name exists
    if db.query(Computer).filter(Computer.name == computer_data.name).first():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Computer name already exists"
        )
    
    computer = Computer(**computer_data.model_dump())
    db.add(computer)
    db.commit()
    db.refresh(computer)
    return computer


@router.patch("/{computer_id}", response_model=ComputerResponse)
async def update_computer(
    computer_id: UUID,
    computer_data: ComputerUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission(Permission.MANAGE_COMPUTERS))
):
    """Update computer"""
    computer = db.query(Computer).filter(Computer.id == computer_id).first()
    if not computer:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Computer not found"
        )
    
    update_data = computer_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(computer, field, value)
    
    db.commit()
    db.refresh(computer)
    return computer


@router.delete("/{computer_id}")
async def delete_computer(
    computer_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission(Permission.MANAGE_COMPUTERS))
):
    """Delete a computer"""
    computer = db.query(Computer).filter(Computer.id == computer_id).first()
    if not computer:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Computer not found"
        )
    
    db.delete(computer)
    db.commit()
    
    return {"message": "Computer deleted successfully"}
