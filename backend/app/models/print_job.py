from sqlalchemy import Column, String, Integer, Numeric, DateTime, Enum as SQLEnum, ForeignKey, Boolean
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from datetime import datetime
import uuid
import enum
from ..database import Base


class PrintJobStatus(str, enum.Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    PRINTED = "printed"
    CANCELLED = "cancelled"


class PrintJob(Base):
    __tablename__ = "print_jobs"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    job_number = Column(String(50), unique=True, nullable=False, index=True)
    
    # Job details
    computer_id = Column(UUID(as_uuid=True), ForeignKey("computers.id"), nullable=False, index=True)
    requested_by = Column(String(255), nullable=False)  # Customer name/identifier
    description = Column(String(500), nullable=True)
    pages_bw = Column(Integer, nullable=False, default=0)  # Black & white pages
    pages_color = Column(Integer, nullable=False, default=0)  # Color pages
    
    # Pricing
    total_amount = Column(Numeric(10, 2), nullable=False)  # Computed server-side
    
    # Status tracking
    status = Column(SQLEnum(PrintJobStatus), nullable=False, default=PrintJobStatus.PENDING, index=True)
    
    # Transaction link (created on approval)
    transaction_id = Column(UUID(as_uuid=True), ForeignKey("transactions.id"), nullable=True)
    
    # Approval tracking
    approved_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    approved_at = Column(DateTime(timezone=True), nullable=True)
    
    # Rejection tracking
    rejected_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    rejected_at = Column(DateTime(timezone=True), nullable=True)
    rejection_reason = Column(String(500), nullable=True)
    
    # Printed tracking
    printed_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    printed_at = Column(DateTime(timezone=True), nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # Relationships
    computer = relationship("Computer", foreign_keys=[computer_id])
    transaction = relationship("Transaction", foreign_keys=[transaction_id])
    approver = relationship("User", foreign_keys=[approved_by])
    rejecter = relationship("User", foreign_keys=[rejected_by])
    printer = relationship("User", foreign_keys=[printed_by])
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Auto-generate job number if not provided
        if not self.job_number:
            self.job_number = f"PJ{datetime.utcnow().strftime('%Y%m%d%H%M%S')}{str(uuid.uuid4())[:4].upper()}"
    
    @property
    def is_pending(self) -> bool:
        """Check if job is pending approval"""
        return self.status == PrintJobStatus.PENDING
    
    @property
    def is_approved(self) -> bool:
        """Check if job is approved"""
        return self.status == PrintJobStatus.APPROVED
    
    @property
    def is_completed(self) -> bool:
        """Check if job is completed (printed, rejected, or cancelled)"""
        return self.status in [PrintJobStatus.PRINTED, PrintJobStatus.REJECTED, PrintJobStatus.CANCELLED]
    
    @property
    def total_pages(self) -> int:
        """Total pages count"""
        return self.pages_bw + self.pages_color
