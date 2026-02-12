from pydantic import BaseModel, Field, validator
from typing import Optional, List
from datetime import datetime
from decimal import Decimal
from uuid import UUID


# Print Job Schemas

class PrintJobCreate(BaseModel):
    """Request to submit a new print job"""
    computer_id: UUID
    requested_by: str = Field(..., min_length=1, max_length=255, description="Customer name or identifier")
    description: Optional[str] = Field(None, max_length=500, description="Job description")
    pages_bw: int = Field(0, ge=0, description="Black & white pages count")
    pages_color: int = Field(0, ge=0, description="Color pages count")
    
    @validator('pages_bw', 'pages_color')
    def validate_pages(cls, v, values):
        # Ensure at least one page is requested
        if 'pages_bw' in values and v == 0 and values.get('pages_bw', 0) == 0:
            raise ValueError('At least one page (B&W or Color) must be requested')
        return v


class PrintJobResponse(BaseModel):
    """Print job details response"""
    id: UUID
    job_number: str
    computer_id: UUID
    requested_by: str
    description: Optional[str]
    pages_bw: int
    pages_color: int
    total_pages: int
    total_amount: Decimal
    status: str
    transaction_id: Optional[UUID]
    approved_by: Optional[UUID]
    approved_at: Optional[datetime]
    rejected_by: Optional[UUID]
    rejected_at: Optional[datetime]
    rejection_reason: Optional[str]
    printed_by: Optional[UUID]
    printed_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class PrintJobListResponse(BaseModel):
    """List of print jobs with pagination"""
    items: List[PrintJobResponse]
    total: int
    page: int
    page_size: int
    pending_count: int
    approved_count: int


class RejectJobRequest(BaseModel):
    """Request to reject a print job"""
    rejection_reason: str = Field(..., min_length=1, max_length=500, description="Reason for rejection")


class ApproveJobRequest(BaseModel):
    """Request to approve a print job (empty, action only)"""
    pass


class MarkPrintedRequest(BaseModel):
    """Request to mark job as printed (empty, action only)"""
    pass


class PrintJobStats(BaseModel):
    """Print job statistics"""
    total_jobs: int
    pending_jobs: int
    approved_jobs: int
    printed_jobs: int
    rejected_jobs: int
    cancelled_jobs: int
    total_revenue: Decimal
    total_pages_bw: int
    total_pages_color: int
