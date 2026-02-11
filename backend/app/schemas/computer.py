from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from uuid import UUID
from ..models.computer import ComputerStatus


class ComputerBase(BaseModel):
    name: str


class ComputerCreate(ComputerBase):
    pass


class ComputerUpdate(BaseModel):
    name: Optional[str] = None
    status: Optional[ComputerStatus] = None


class ComputerResponse(ComputerBase):
    id: UUID
    status: ComputerStatus
    current_session_id: Optional[UUID]
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True
