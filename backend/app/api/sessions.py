from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from uuid import UUID
from datetime import datetime
from decimal import Decimal
from ..database import get_db
from ..schemas.session import SessionStart, SessionStop, SessionResponse
from ..models.session import Session as SessionModel, SessionStatus
from ..models.computer import Computer, ComputerStatus
from ..models.service import Service, PricingMode
from ..models.user import User
from ..utils.calculations import calculate_session_charge
from ..api.deps import get_current_user

router = APIRouter(prefix="/sessions", tags=["Sessions"])


@router.get("/", response_model=List[SessionResponse])
async def list_sessions(
    active_only: bool = False,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """List sessions"""
    query = db.query(SessionModel)
    if active_only:
        query = query.filter(SessionModel.status == SessionStatus.ACTIVE)
    
    sessions = query.offset(skip).limit(limit).all()
    return sessions


@router.post("/start", response_model=SessionResponse)
async def start_session(
    session_data: SessionStart,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Start a computer session"""
    computer = db.query(Computer).filter(Computer.id == session_data.computer_id).first()
    if not computer:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Computer not found"
        )
    
    if computer.status != ComputerStatus.AVAILABLE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Computer is {computer.status.value}"
        )
    
    # Create session
    session = SessionModel(
        computer_id=computer.id,
        started_by=current_user.id,
        status=SessionStatus.ACTIVE
    )
    db.add(session)
    
    # Update computer status
    computer.status = ComputerStatus.IN_USE
    computer.current_session_id = session.id
    
    db.commit()
    db.refresh(session)
    
    return session


@router.post("/stop", response_model=SessionResponse)
async def stop_session(
    session_data: SessionStop,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Stop a computer session"""
    session = db.query(SessionModel).filter(SessionModel.id == session_data.session_id).first()
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found"
        )
    
    if session.status != SessionStatus.ACTIVE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Session is not active"
        )
    
    # Get browsing service rate (assuming there's a service for browsing)
    browsing_service = db.query(Service).filter(
        Service.name.ilike("%browsing%"),
        Service.pricing_mode == PricingMode.PER_MINUTE
    ).first()
    
    rate_per_minute = browsing_service.base_price if browsing_service else Decimal("1.00")
    
    # Calculate charge
    end_time = datetime.utcnow()
    duration_minutes, amount_charged = calculate_session_charge(
        session.start_time,
        end_time,
        rate_per_minute
    )
    
    # Update session
    session.end_time = end_time
    session.duration_minutes = duration_minutes
    session.amount_charged = amount_charged
    session.status = SessionStatus.COMPLETED
    
    # Update computer status
    computer = db.query(Computer).filter(Computer.id == session.computer_id).first()
    computer.status = ComputerStatus.AVAILABLE
    computer.current_session_id = None
    
    db.commit()
    db.refresh(session)
    
    return session


@router.get("/{session_id}", response_model=SessionResponse)
async def get_session(
    session_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get session by ID"""
    session = db.query(SessionModel).filter(SessionModel.id == session_id).first()
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found"
        )
    return session
