from sqlalchemy import Column, String, DateTime, Enum, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
import uuid
import enum
from ..database import Base


class ComputerStatus(str, enum.Enum):
    AVAILABLE = "available"
    IN_USE = "in_use"
    OFFLINE = "offline"
    MAINTENANCE = "maintenance"


class Computer(Base):
    __tablename__ = "computers"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(50), nullable=False, unique=True, index=True)
    status = Column(Enum(ComputerStatus), nullable=False, default=ComputerStatus.AVAILABLE)
    current_session_id = Column(UUID(as_uuid=True), ForeignKey("sessions.id"), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # Relationships
    current_session = relationship("Session", foreign_keys=[current_session_id], post_update=True)
    sessions = relationship("Session", foreign_keys="Session.computer_id", back_populates="computer")
