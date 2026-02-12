"""
Print Job Queue API Endpoints
Handles print job submission, approval, rejection, and printing workflow
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func, and_
from typing import List, Optional
from datetime import datetime
from decimal import Decimal
from uuid import UUID
import logging

from ..database import get_db
from ..api.deps import get_current_user, require_role
from ..models.user import User, UserRole
from ..models.print_job import PrintJob, PrintJobStatus
from ..models.computer import Computer
from ..models.service import Service
from ..models.transaction import Transaction, TransactionItem, PaymentMethod, TransactionStatus
from ..models.inventory import InventoryItem, StockMovement
from ..models.shift import Shift
from ..schemas.print_job import (
    PrintJobCreate,
    PrintJobResponse,
    PrintJobListResponse,
    RejectJobRequest,
    ApproveJobRequest,
    MarkPrintedRequest,
    PrintJobStats
)
from ..core.audit import log_audit

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/print-jobs", tags=["Print Jobs"])


def get_printing_services(db: Session):
    """Get B&W and Color printing services"""
    bw_service = db.query(Service).filter(
        Service.name.ilike("%black%white%"),
        Service.is_active == True
    ).first()
    
    color_service = db.query(Service).filter(
        Service.name.ilike("%color%"),
        Service.is_active == True
    ).first()
    
    if not bw_service:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Black & White printing service not found. Please create a service with 'Black' and 'White' in the name."
        )
    
    if not color_service:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Color printing service not found. Please create a service with 'Color' in the name."
        )
    
    return bw_service, color_service


@router.post("", response_model=PrintJobResponse, status_code=status.HTTP_201_CREATED)
async def submit_print_job(
    job_data: PrintJobCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Submit a new print job
    
    Calculates total amount server-side based on printing services
    """
    try:
        # Validate computer exists
        computer = db.query(Computer).filter(Computer.id == job_data.computer_id).first()
        if not computer:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Computer not found"
            )
        
        # Validate at least one page
        if job_data.pages_bw == 0 and job_data.pages_color == 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="At least one page (B&W or Color) must be requested"
            )
        
        # Get printing services
        bw_service, color_service = get_printing_services(db)
        
        # Calculate total amount server-side
        total_amount = Decimal("0")
        if job_data.pages_bw > 0:
            total_amount += Decimal(str(job_data.pages_bw)) * bw_service.base_price
        if job_data.pages_color > 0:
            total_amount += Decimal(str(job_data.pages_color)) * color_service.base_price
        
        # Create print job
        print_job = PrintJob(
            computer_id=job_data.computer_id,
            requested_by=job_data.requested_by,
            description=job_data.description,
            pages_bw=job_data.pages_bw,
            pages_color=job_data.pages_color,
            total_amount=total_amount,
            status=PrintJobStatus.PENDING
        )
        
        db.add(print_job)
        db.commit()
        db.refresh(print_job)
        
        logger.info(f"Print job {print_job.job_number} submitted by {current_user.username}")
        
        return print_job
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error submitting print job: {e}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to submit print job: {str(e)}"
        )


@router.get("", response_model=PrintJobListResponse)
async def list_print_jobs(
    page: int = 1,
    page_size: int = 50,
    status_filter: Optional[str] = None,
    computer_id: Optional[UUID] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    List print jobs with optional filtering
    """
    query = db.query(PrintJob)
    
    # Apply filters
    if status_filter:
        query = query.filter(PrintJob.status == status_filter)
    
    if computer_id:
        query = query.filter(PrintJob.computer_id == computer_id)
    
    # Get total count
    total = query.count()
    
    # Get counts by status
    pending_count = db.query(func.count(PrintJob.id)).filter(
        PrintJob.status == PrintJobStatus.PENDING
    ).scalar()
    
    approved_count = db.query(func.count(PrintJob.id)).filter(
        PrintJob.status == PrintJobStatus.APPROVED
    ).scalar()
    
    # Paginate
    offset = (page - 1) * page_size
    items = query.order_by(PrintJob.created_at.desc()).offset(offset).limit(page_size).all()
    
    return PrintJobListResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        pending_count=pending_count or 0,
        approved_count=approved_count or 0
    )


@router.get("/{job_id}", response_model=PrintJobResponse)
async def get_print_job(
    job_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get print job details"""
    job = db.query(PrintJob).filter(PrintJob.id == job_id).first()
    
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Print job not found"
        )
    
    return job


@router.post("/{job_id}/approve", response_model=PrintJobResponse)
async def approve_print_job(
    job_id: UUID,
    request: ApproveJobRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role([UserRole.ADMIN, UserRole.MANAGER, UserRole.ATTENDANT]))
):
    """
    Approve print job
    
    Creates transaction and reserves stock
    """
    try:
        # Get job
        job = db.query(PrintJob).filter(PrintJob.id == job_id).first()
        if not job:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Print job not found"
            )
        
        # Verify status
        if job.status != PrintJobStatus.PENDING:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Cannot approve job with status: {job.status}"
            )
        
        # Get current shift
        current_shift = db.query(Shift).filter(
            Shift.attendant_id == current_user.id,
            Shift.closed_at.is_(None)
        ).first()
        
        if not current_shift:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No open shift found. Please open a shift first."
            )
        
        # Get printing services
        bw_service, color_service = get_printing_services(db)
        
        # Create transaction
        # Get next transaction number
        max_number = db.query(func.max(Transaction.transaction_number)).scalar()
        next_number = (max_number or 0) + 1
        
        transaction = Transaction(
            transaction_number=next_number,
            created_by=current_user.id,
            shift_id=current_shift.id,
            total_amount=job.total_amount,
            discount_amount=Decimal("0"),
            final_amount=job.total_amount,
            payment_method=PaymentMethod.CASH,  # Default to cash, can be changed later
            status=TransactionStatus.COMPLETED
        )
        
        db.add(transaction)
        db.flush()  # Get transaction ID
        
        # Add transaction items
        if job.pages_bw > 0:
            bw_item = TransactionItem(
                transaction_id=transaction.id,
                service_id=bw_service.id,
                description=f"Printing (B&W) - {job.pages_bw} pages",
                quantity=job.pages_bw,
                unit_price=bw_service.base_price,
                total_price=Decimal(str(job.pages_bw)) * bw_service.base_price
            )
            db.add(bw_item)
        
        if job.pages_color > 0:
            color_item = TransactionItem(
                transaction_id=transaction.id,
                service_id=color_service.id,
                description=f"Printing (Color) - {job.pages_color} pages",
                quantity=job.pages_color,
                unit_price=color_service.base_price,
                total_price=Decimal(str(job.pages_color)) * color_service.base_price
            )
            db.add(color_item)
        
        # Update job
        job.status = PrintJobStatus.APPROVED
        job.approved_by = current_user.id
        job.approved_at = datetime.utcnow()
        job.transaction_id = transaction.id
        
        # Audit log
        log_audit(
            db=db,
            user_id=current_user.id,
            action="PRINT_JOB_APPROVED",
            entity_type="print_job",
            entity_id=str(job.id),
            old_value={"status": "pending"},
            new_value={
                "status": "approved",
                "transaction_id": str(transaction.id),
                "job_number": job.job_number
            }
        )
        
        db.commit()
        db.refresh(job)
        
        logger.info(f"Print job {job.job_number} approved by {current_user.username}")
        
        return job
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error approving print job: {e}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to approve print job: {str(e)}"
        )


@router.post("/{job_id}/reject", response_model=PrintJobResponse)
async def reject_print_job(
    job_id: UUID,
    request: RejectJobRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role([UserRole.ADMIN, UserRole.MANAGER, UserRole.ATTENDANT]))
):
    """
    Reject print job with reason
    """
    try:
        # Get job
        job = db.query(PrintJob).filter(PrintJob.id == job_id).first()
        if not job:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Print job not found"
            )
        
        # Verify status
        if job.status != PrintJobStatus.PENDING:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Cannot reject job with status: {job.status}"
            )
        
        # Update job
        job.status = PrintJobStatus.REJECTED
        job.rejected_by = current_user.id
        job.rejected_at = datetime.utcnow()
        job.rejection_reason = request.rejection_reason
        
        # Audit log
        log_audit(
            db=db,
            user_id=current_user.id,
            action="PRINT_JOB_REJECTED",
            entity_type="print_job",
            entity_id=str(job.id),
            old_value={"status": "pending"},
            new_value={
                "status": "rejected",
                "rejection_reason": request.rejection_reason,
                "job_number": job.job_number
            }
        )
        
        db.commit()
        db.refresh(job)
        
        logger.info(f"Print job {job.job_number} rejected by {current_user.username}")
        
        return job
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error rejecting print job: {e}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to reject print job: {str(e)}"
        )


@router.post("/{job_id}/mark-printed", response_model=PrintJobResponse)
async def mark_job_printed(
    job_id: UUID,
    request: MarkPrintedRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role([UserRole.ADMIN, UserRole.MANAGER, UserRole.ATTENDANT]))
):
    """
    Mark job as printed and finalize stock deduction
    """
    try:
        # Get job
        job = db.query(PrintJob).filter(PrintJob.id == job_id).first()
        if not job:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Print job not found"
            )
        
        # Verify status
        if job.status != PrintJobStatus.APPROVED:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Cannot mark as printed. Job status: {job.status}"
            )
        
        # Get printing services for stock deduction
        bw_service, color_service = get_printing_services(db)
        
        # Deduct stock if services have stock items linked
        if job.pages_bw > 0 and bw_service.requires_stock and bw_service.stock_item_id:
            stock_item = db.query(InventoryItem).filter(
                InventoryItem.id == bw_service.stock_item_id
            ).first()
            
            if stock_item:
                # Create stock movement
                movement = StockMovement(
                    item_id=stock_item.id,
                    movement_type="SALE",
                    quantity=Decimal(str(job.pages_bw)),
                    reference_type="print_job",
                    reference_id=str(job.id),
                    performed_by=current_user.id,
                    notes=f"Print job {job.job_number} - B&W pages"
                )
                db.add(movement)
                
                # Update stock
                stock_item.current_stock -= Decimal(str(job.pages_bw))
        
        if job.pages_color > 0 and color_service.requires_stock and color_service.stock_item_id:
            stock_item = db.query(InventoryItem).filter(
                InventoryItem.id == color_service.stock_item_id
            ).first()
            
            if stock_item:
                # Create stock movement
                movement = StockMovement(
                    item_id=stock_item.id,
                    movement_type="SALE",
                    quantity=Decimal(str(job.pages_color)),
                    reference_type="print_job",
                    reference_id=str(job.id),
                    performed_by=current_user.id,
                    notes=f"Print job {job.job_number} - Color pages"
                )
                db.add(movement)
                
                # Update stock
                stock_item.current_stock -= Decimal(str(job.pages_color))
        
        # Update job
        job.status = PrintJobStatus.PRINTED
        job.printed_by = current_user.id
        job.printed_at = datetime.utcnow()
        
        # Audit log
        log_audit(
            db=db,
            user_id=current_user.id,
            action="PRINT_JOB_PRINTED",
            entity_type="print_job",
            entity_id=str(job.id),
            old_value={"status": "approved"},
            new_value={
                "status": "printed",
                "job_number": job.job_number
            }
        )
        
        db.commit()
        db.refresh(job)
        
        logger.info(f"Print job {job.job_number} marked as printed by {current_user.username}")
        
        return job
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error marking job as printed: {e}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to mark job as printed: {str(e)}"
        )


@router.post("/{job_id}/cancel", response_model=PrintJobResponse)
async def cancel_print_job(
    job_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Cancel print job (PENDING only)
    """
    try:
        # Get job
        job = db.query(PrintJob).filter(PrintJob.id == job_id).first()
        if not job:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Print job not found"
            )
        
        # Verify status
        if job.status != PrintJobStatus.PENDING:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Cannot cancel job with status: {job.status}"
            )
        
        # Update job
        job.status = PrintJobStatus.CANCELLED
        
        db.commit()
        db.refresh(job)
        
        logger.info(f"Print job {job.job_number} cancelled by {current_user.username}")
        
        return job
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error cancelling print job: {e}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to cancel print job: {str(e)}"
        )


@router.get("/stats/summary", response_model=PrintJobStats)
async def get_print_job_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role([UserRole.ADMIN, UserRole.MANAGER]))
):
    """Get print job statistics (Admin/Manager only)"""
    total_jobs = db.query(func.count(PrintJob.id)).scalar() or 0
    
    pending_jobs = db.query(func.count(PrintJob.id)).filter(
        PrintJob.status == PrintJobStatus.PENDING
    ).scalar() or 0
    
    approved_jobs = db.query(func.count(PrintJob.id)).filter(
        PrintJob.status == PrintJobStatus.APPROVED
    ).scalar() or 0
    
    printed_jobs = db.query(func.count(PrintJob.id)).filter(
        PrintJob.status == PrintJobStatus.PRINTED
    ).scalar() or 0
    
    rejected_jobs = db.query(func.count(PrintJob.id)).filter(
        PrintJob.status == PrintJobStatus.REJECTED
    ).scalar() or 0
    
    cancelled_jobs = db.query(func.count(PrintJob.id)).filter(
        PrintJob.status == PrintJobStatus.CANCELLED
    ).scalar() or 0
    
    total_revenue = db.query(func.sum(PrintJob.total_amount)).filter(
        PrintJob.status == PrintJobStatus.PRINTED
    ).scalar() or Decimal("0")
    
    total_pages_bw = db.query(func.sum(PrintJob.pages_bw)).filter(
        PrintJob.status == PrintJobStatus.PRINTED
    ).scalar() or 0
    
    total_pages_color = db.query(func.sum(PrintJob.pages_color)).filter(
        PrintJob.status == PrintJobStatus.PRINTED
    ).scalar() or 0
    
    return PrintJobStats(
        total_jobs=total_jobs,
        pending_jobs=pending_jobs,
        approved_jobs=approved_jobs,
        printed_jobs=printed_jobs,
        rejected_jobs=rejected_jobs,
        cancelled_jobs=cancelled_jobs,
        total_revenue=total_revenue,
        total_pages_bw=total_pages_bw,
        total_pages_color=total_pages_color
    )
