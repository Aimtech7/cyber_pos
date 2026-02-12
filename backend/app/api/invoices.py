"""
Invoice API Endpoints
Handles invoice creation, payment recording, and aging reports
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_
from typing import List, Optional, Dict
from datetime import datetime, date, timedelta
from decimal import Decimal
from uuid import UUID
import logging

from ..database import get_db
from ..api.deps import get_current_user, require_role
from ..models.user import User, UserRole
from ..models.customer import Customer
from ..models.invoice import Invoice, InvoiceItem, InvoicePayment, InvoiceStatus
from ..models.transaction import Transaction
from ..schemas.invoice import (
    InvoiceCreate,
    InvoiceUpdate,
    InvoiceResponse,
    InvoiceListResponse,
    InvoicePaymentCreate,
    InvoicePaymentResponse,
    CreateInvoiceFromTransactions,
    AgingReportResponse,
    AgingBucket,
    IssueInvoiceRequest,
    CancelInvoiceRequest
)
from ..core.audit import log_audit

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/invoices", tags=["Invoices"])


@router.post("", response_model=InvoiceResponse, status_code=status.HTTP_201_CREATED)
async def create_invoice(
    invoice_data: InvoiceCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Create new invoice
    """
    try:
        # Validate customer
        customer = db.query(Customer).filter(Customer.id == invoice_data.customer_id).first()
        if not customer:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Customer not found"
            )
        
        if not customer.is_active:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Customer account is inactive"
            )
        
        # Calculate totals
        subtotal = sum(item.total_price for item in invoice_data.items)
        tax_amount = Decimal("0")  # Can be calculated if needed
        total_amount = subtotal + tax_amount
        
        # Calculate due date
        due_date = date.today() + timedelta(days=invoice_data.due_days)
        
        # Create invoice
        invoice = Invoice(
            customer_id=invoice_data.customer_id,
            status=InvoiceStatus.DRAFT,
            due_date=due_date,
            subtotal=subtotal,
            tax_amount=tax_amount,
            total_amount=total_amount,
            notes=invoice_data.notes,
            created_by=current_user.id
        )
        
        db.add(invoice)
        db.flush()  # Get invoice ID
        
        # Add items
        for item_data in invoice_data.items:
            item = InvoiceItem(
                invoice_id=invoice.id,
                transaction_id=item_data.transaction_id,
                description=item_data.description,
                quantity=item_data.quantity,
                unit_price=item_data.unit_price,
                total_price=item_data.total_price
            )
            db.add(item)
        
        # Issue immediately if requested
        if invoice_data.issue_immediately:
            # Check credit limit
            new_balance = customer.current_balance + total_amount
            if new_balance > customer.credit_limit:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Credit limit exceeded. Available: KES {customer.available_credit}"
                )
            
            invoice.status = InvoiceStatus.ISSUED
            invoice.issue_date = date.today()
            customer.current_balance = new_balance
        
        db.commit()
        db.refresh(invoice)
        
        # Audit log
        log_audit(
            db=db,
            user_id=current_user.id,
            action="INVOICE_CREATED",
            entity_type="invoice",
            entity_id=str(invoice.id),
            new_value={
                "invoice_number": invoice.invoice_number,
                "customer_id": str(customer.id),
                "total_amount": float(total_amount),
                "status": invoice.status.value
            }
        )
        
        logger.info(f"Invoice {invoice.invoice_number} created by {current_user.username}")
        
        return invoice
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating invoice: {e}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create invoice: {str(e)}"
        )


@router.post("/from-transactions", response_model=InvoiceResponse, status_code=status.HTTP_201_CREATED)
async def create_invoice_from_transactions(
    request: CreateInvoiceFromTransactions,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Create invoice from existing transactions
    """
    try:
        # Validate customer
        customer = db.query(Customer).filter(Customer.id == request.customer_id).first()
        if not customer:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Customer not found"
            )
        
        # Get transactions
        transactions = db.query(Transaction).filter(
            Transaction.id.in_(request.transaction_ids)
        ).all()
        
        if len(transactions) != len(request.transaction_ids):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="One or more transactions not found"
            )
        
        # Check if any transaction already has an invoice
        for txn in transactions:
            if txn.invoice_id:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Transaction {txn.transaction_number} already has an invoice"
                )
        
        # Calculate totals
        subtotal = sum(txn.final_amount for txn in transactions)
        tax_amount = Decimal("0")
        total_amount = subtotal + tax_amount
        
        # Calculate due date
        due_date = date.today() + timedelta(days=request.due_days)
        
        # Create invoice
        invoice = Invoice(
            customer_id=request.customer_id,
            status=InvoiceStatus.DRAFT,
            due_date=due_date,
            subtotal=subtotal,
            tax_amount=tax_amount,
            total_amount=total_amount,
            notes=request.notes,
            created_by=current_user.id
        )
        
        db.add(invoice)
        db.flush()
        
        # Add items from transactions
        for txn in transactions:
            item = InvoiceItem(
                invoice_id=invoice.id,
                transaction_id=txn.id,
                description=f"Transaction #{txn.transaction_number}",
                quantity=Decimal("1"),
                unit_price=txn.final_amount,
                total_price=txn.final_amount
            )
            db.add(item)
            
            # Link transaction to invoice
            txn.invoice_id = invoice.id
        
        # Issue immediately if requested
        if request.issue_immediately:
            # Check credit limit
            new_balance = customer.current_balance + total_amount
            if new_balance > customer.credit_limit:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Credit limit exceeded. Available: KES {customer.available_credit}"
                )
            
            invoice.status = InvoiceStatus.ISSUED
            invoice.issue_date = date.today()
            customer.current_balance = new_balance
        
        db.commit()
        db.refresh(invoice)
        
        logger.info(f"Invoice {invoice.invoice_number} created from {len(transactions)} transactions")
        
        return invoice
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating invoice from transactions: {e}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create invoice: {str(e)}"
        )


@router.get("", response_model=InvoiceListResponse)
async def list_invoices(
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    customer_id: Optional[UUID] = None,
    status_filter: Optional[str] = None,
    overdue_only: bool = False,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    List invoices with optional filtering
    """
    query = db.query(Invoice)
    
    # Apply filters
    if customer_id:
        query = query.filter(Invoice.customer_id == customer_id)
    
    if status_filter:
        query = query.filter(Invoice.status == status_filter)
    
    if overdue_only:
        query = query.filter(
            Invoice.status.in_([InvoiceStatus.ISSUED, InvoiceStatus.PART_PAID]),
            Invoice.due_date < date.today()
        )
    
    # Get total count
    total = query.count()
    
    # Paginate
    offset = (page - 1) * page_size
    items = query.order_by(Invoice.created_at.desc()).offset(offset).limit(page_size).all()
    
    return InvoiceListResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size
    )


@router.get("/{invoice_id}", response_model=InvoiceResponse)
async def get_invoice(
    invoice_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get invoice details"""
    invoice = db.query(Invoice).filter(Invoice.id == invoice_id).first()
    
    if not invoice:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Invoice not found"
        )
    
    return invoice


@router.put("/{invoice_id}", response_model=InvoiceResponse)
async def update_invoice(
    invoice_id: UUID,
    invoice_data: InvoiceUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role([UserRole.ADMIN, UserRole.MANAGER]))
):
    """
    Update invoice (Admin/Manager only, DRAFT only)
    """
    try:
        invoice = db.query(Invoice).filter(Invoice.id == invoice_id).first()
        
        if not invoice:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Invoice not found"
            )
        
        if invoice.status != InvoiceStatus.DRAFT:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Can only update DRAFT invoices"
            )
        
        # Update fields
        update_data = invoice_data.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(invoice, field, value)
        
        db.commit()
        db.refresh(invoice)
        
        logger.info(f"Invoice {invoice.invoice_number} updated by {current_user.username}")
        
        return invoice
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating invoice: {e}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update invoice: {str(e)}"
        )


@router.post("/{invoice_id}/issue", response_model=InvoiceResponse)
async def issue_invoice(
    invoice_id: UUID,
    request: IssueInvoiceRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role([UserRole.ADMIN, UserRole.MANAGER]))
):
    """
    Issue invoice (DRAFT → ISSUED)
    """
    try:
        invoice = db.query(Invoice).filter(Invoice.id == invoice_id).first()
        
        if not invoice:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Invoice not found"
            )
        
        if invoice.status != InvoiceStatus.DRAFT:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Cannot issue invoice with status: {invoice.status}"
            )
        
        # Get customer
        customer = db.query(Customer).filter(Customer.id == invoice.customer_id).first()
        
        # Check credit limit
        new_balance = customer.current_balance + invoice.total_amount
        if new_balance > customer.credit_limit:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Credit limit exceeded. Available: KES {customer.available_credit}"
            )
        
        # Issue invoice
        invoice.status = InvoiceStatus.ISSUED
        invoice.issue_date = date.today()
        customer.current_balance = new_balance
        
        db.commit()
        db.refresh(invoice)
        
        # Audit log
        log_audit(
            db=db,
            user_id=current_user.id,
            action="INVOICE_ISSUED",
            entity_type="invoice",
            entity_id=str(invoice.id),
            new_value={
                "invoice_number": invoice.invoice_number,
                "total_amount": float(invoice.total_amount)
            }
        )
        
        logger.info(f"Invoice {invoice.invoice_number} issued by {current_user.username}")
        
        return invoice
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error issuing invoice: {e}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to issue invoice: {str(e)}"
        )


@router.post("/{invoice_id}/cancel", response_model=InvoiceResponse)
async def cancel_invoice(
    invoice_id: UUID,
    request: CancelInvoiceRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role([UserRole.ADMIN, UserRole.MANAGER]))
):
    """
    Cancel invoice (Admin/Manager only)
    """
    try:
        invoice = db.query(Invoice).filter(Invoice.id == invoice_id).first()
        
        if not invoice:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Invoice not found"
            )
        
        if invoice.status == InvoiceStatus.CANCELLED:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invoice already cancelled"
            )
        
        if invoice.status == InvoiceStatus.PAID:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot cancel paid invoice"
            )
        
        # Get customer
        customer = db.query(Customer).filter(Customer.id == invoice.customer_id).first()
        
        # If invoice was issued, reduce customer balance
        if invoice.status in [InvoiceStatus.ISSUED, InvoiceStatus.PART_PAID]:
            outstanding = invoice.balance
            customer.current_balance -= Decimal(str(outstanding))
        
        # Cancel invoice
        invoice.status = InvoiceStatus.CANCELLED
        if request.reason:
            invoice.notes = f"{invoice.notes or ''}\n\nCancellation reason: {request.reason}".strip()
        
        db.commit()
        db.refresh(invoice)
        
        # Audit log
        log_audit(
            db=db,
            user_id=current_user.id,
            action="INVOICE_CANCELLED",
            entity_type="invoice",
            entity_id=str(invoice.id),
            new_value={
                "invoice_number": invoice.invoice_number,
                "reason": request.reason
            }
        )
        
        logger.info(f"Invoice {invoice.invoice_number} cancelled by {current_user.username}")
        
        return invoice
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error cancelling invoice: {e}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to cancel invoice: {str(e)}"
        )


@router.post("/{invoice_id}/payments", response_model=InvoicePaymentResponse, status_code=status.HTTP_201_CREATED)
async def record_payment(
    invoice_id: UUID,
    payment_data: InvoicePaymentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Record payment on invoice
    """
    try:
        invoice = db.query(Invoice).filter(Invoice.id == invoice_id).first()
        
        if not invoice:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Invoice not found"
            )
        
        if invoice.status not in [InvoiceStatus.ISSUED, InvoiceStatus.PART_PAID]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Cannot record payment for invoice with status: {invoice.status}"
            )
        
        # Validate payment amount
        outstanding = Decimal(str(invoice.balance))
        if payment_data.amount > outstanding:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Payment amount exceeds outstanding balance of KES {outstanding}"
            )
        
        # Create payment record
        payment = InvoicePayment(
            invoice_id=invoice.id,
            amount=payment_data.amount,
            payment_method=payment_data.payment_method,
            reference=payment_data.reference,
            notes=payment_data.notes,
            recorded_by=current_user.id
        )
        
        db.add(payment)
        
        # Update invoice
        invoice.paid_amount += payment_data.amount
        new_balance = invoice.balance
        
        # Update status
        if new_balance == 0:
            invoice.status = InvoiceStatus.PAID
        else:
            invoice.status = InvoiceStatus.PART_PAID
        
        # Update customer balance
        customer = db.query(Customer).filter(Customer.id == invoice.customer_id).first()
        customer.current_balance -= payment_data.amount
        
        db.commit()
        db.refresh(payment)
        
        # Audit log
        log_audit(
            db=db,
            user_id=current_user.id,
            action="INVOICE_PAYMENT_RECORDED",
            entity_type="invoice",
            entity_id=str(invoice.id),
            new_value={
                "invoice_number": invoice.invoice_number,
                "payment_amount": float(payment_data.amount),
                "payment_method": payment_data.payment_method,
                "new_status": invoice.status.value
            }
        )
        
        logger.info(f"Payment of KES {payment_data.amount} recorded for invoice {invoice.invoice_number}")
        
        return payment
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error recording payment: {e}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to record payment: {str(e)}"
        )


@router.get("/{invoice_id}/payments", response_model=List[InvoicePaymentResponse])
async def list_invoice_payments(
    invoice_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """List payments for invoice"""
    invoice = db.query(Invoice).filter(Invoice.id == invoice_id).first()
    
    if not invoice:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Invoice not found"
        )
    
    payments = db.query(InvoicePayment).filter(
        InvoicePayment.invoice_id == invoice_id
    ).order_by(InvoicePayment.payment_date.desc()).all()
    
    return payments


@router.get("/aging-report", response_model=List[AgingReportResponse])
async def get_aging_report(
    customer_id: Optional[UUID] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role([UserRole.ADMIN, UserRole.MANAGER]))
):
    """
    Get aging report (Admin/Manager only)
    """
    query = db.query(Invoice).filter(
        Invoice.status.in_([InvoiceStatus.ISSUED, InvoiceStatus.PART_PAID])
    )
    
    if customer_id:
        query = query.filter(Invoice.customer_id == customer_id)
    
    invoices = query.all()
    
    # Group by customer
    customer_data: Dict[UUID, Dict] = {}
    
    for invoice in invoices:
        if invoice.customer_id not in customer_data:
            customer_data[invoice.customer_id] = {
                "customer": db.query(Customer).filter(Customer.id == invoice.customer_id).first(),
                "buckets": {
                    "0-30": {"count": 0, "total": Decimal("0")},
                    "31-60": {"count": 0, "total": Decimal("0")},
                    "61-90": {"count": 0, "total": Decimal("0")},
                    "90+": {"count": 0, "total": Decimal("0")}
                }
            }
        
        # Determine bucket
        days_old = (date.today() - invoice.issue_date).days if invoice.issue_date else 0
        balance = Decimal(str(invoice.balance))
        
        if days_old <= 30:
            bucket = "0-30"
        elif days_old <= 60:
            bucket = "31-60"
        elif days_old <= 90:
            bucket = "61-90"
        else:
            bucket = "90+"
        
        customer_data[invoice.customer_id]["buckets"][bucket]["count"] += 1
        customer_data[invoice.customer_id]["buckets"][bucket]["total"] += balance
    
    # Build response
    reports = []
    for cust_id, data in customer_data.items():
        customer = data["customer"]
        buckets = {
            key: AgingBucket(
                range_label=f"{key} days",
                count=val["count"],
                total_amount=val["total"]
            )
            for key, val in data["buckets"].items()
        }
        
        total_outstanding = sum(b.total_amount for b in buckets.values())
        total_invoices = sum(b.count for b in buckets.values())
        
        reports.append(AgingReportResponse(
            customer_id=cust_id,
            customer_name=customer.name,
            buckets=buckets,
            total_outstanding=total_outstanding,
            total_invoices=total_invoices
        ))
    
    return reports
