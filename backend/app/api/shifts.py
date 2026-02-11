from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
from uuid import UUID
from decimal import Decimal
from ..database import get_db
from ..schemas.shift import ShiftOpen, ShiftClose, ShiftResponse
from ..models.shift import Shift, ShiftStatus
from ..models.user import User
from ..api.deps import get_current_user

router = APIRouter(prefix="/shifts", tags=["Shifts"])


@router.get("/", response_model=List[ShiftResponse])
async def list_shifts(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """List shifts"""
    query = db.query(Shift)
    
    # Attendants can only see their own shifts
    if current_user.role.value == "attendant":
        query = query.filter(Shift.user_id == current_user.id)
    
    shifts = query.order_by(Shift.opened_at.desc()).offset(skip).limit(limit).all()
    return shifts


@router.get("/current", response_model=Optional[ShiftResponse])
async def get_current_shift(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get current open shift for user"""
    shift = db.query(Shift).filter(
        Shift.user_id == current_user.id,
        Shift.status == ShiftStatus.OPEN
    ).first()
    
    return shift


@router.post("/open", response_model=ShiftResponse)
async def open_shift(
    shift_data: ShiftOpen,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Open a new shift"""
    # Check if user already has an open shift
    existing_shift = db.query(Shift).filter(
        Shift.user_id == current_user.id,
        Shift.status == ShiftStatus.OPEN
    ).first()
    
    if existing_shift:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You already have an open shift"
        )
    
    shift = Shift(
        user_id=current_user.id,
        opening_cash=shift_data.opening_cash,
        expected_cash=shift_data.opening_cash,
        status=ShiftStatus.OPEN,
        total_sales=Decimal(0),
        total_mpesa=Decimal(0),
        total_refunds=Decimal(0)
    )
    
    db.add(shift)
    db.commit()
    db.refresh(shift)
    
    return shift


@router.post("/close", response_model=ShiftResponse)
async def close_shift(
    shift_data: ShiftClose,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Close current shift"""
    shift = db.query(Shift).filter(
        Shift.user_id == current_user.id,
        Shift.status == ShiftStatus.OPEN
    ).first()
    
    if not shift:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No open shift found"
        )
    
    from datetime import datetime
    
    shift.closed_at = datetime.utcnow()
    shift.closed_by = current_user.id
    shift.close_notes = shift_data.close_notes
    shift.counted_cash = shift_data.counted_cash
    shift.cash_difference = shift_data.counted_cash - (shift.expected_cash or Decimal(0))
    shift.status = ShiftStatus.CLOSED
    
    db.commit()
    db.refresh(shift)
    
    return shift


@router.get("/{shift_id}", response_model=ShiftResponse)
async def get_shift(
    shift_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get shift by ID"""
    shift = db.query(Shift).filter(Shift.id == shift_id).first()
    if not shift:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Shift not found"
        )
    
    # Attendants can only see their own shifts
    if current_user.role.value == "attendant" and shift.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )
    
    return shift
