from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from uuid import UUID
from decimal import Decimal
from ..models.session import SessionStatus


class SessionStart(BaseModel):
    computer_id: UUID


class SessionStop(BaseModel):
    session_id: UUID


class SessionResponse(BaseModel):
    id: UUID
    computer_id: UUID
    started_by: UUID
    start_time: datetime
    end_time: Optional[datetime]
    duration_minutes: Optional[int]
    amount_charged: Optional[Decimal]
    transaction_id: Optional[UUID]
    status: SessionStatus
    
    class Config:
        from_attributes = True
