"""
Customer API Endpoints
Handles customer management, credit checks, and statements
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, or_
from typing import List, Optional
from datetime import datetime, date
from decimal import Decimal
from uuid import UUID
import logging

from ..database import get_db
from ..api.deps import get_current_user, require_role
from ..models.user import User, UserRole
from ..models.customer import Customer
from ..models.invoice import Invoice, InvoiceStatus
from ..schemas.customer import (
    CustomerCreate,
    CustomerUpdate,
    CustomerResponse,
    CustomerListResponse,
    CreditCheckRequest,
    CreditCheckResponse,
    CustomerStatement,
    InvoiceSummary
)
from ..core.audit import log_audit

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/customers", tags=["Customers"])


@router.post("", response_model=CustomerResponse, status_code=status.HTTP_201_CREATED)
async def create_customer(
    customer_data: CustomerCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role([UserRole.ADMIN, UserRole.MANAGER]))
):
    """
    Create new customer (Admin/Manager only)
    """
    try:
        # Check if customer with same name exists
        existing = db.query(Customer).filter(
            func.lower(Customer.name) == customer_data.name.lower()
        ).first()
        
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Customer with name '{customer_data.name}' already exists"
            )
        
        # Create customer
        customer = Customer(
            name=customer_data.name,
            phone=customer_data.phone,
            email=customer_data.email,
            type=customer_data.type,
            notes=customer_data.notes,
            credit_limit=customer_data.credit_limit
        )
        
        db.add(customer)
        db.commit()
        db.refresh(customer)
        
        # Audit log
        log_audit(
            db=db,
            user_id=current_user.id,
            action="CUSTOMER_CREATED",
            entity_type="customer",
            entity_id=str(customer.id),
            new_value={
                "customer_number": customer.customer_number,
                "name": customer.name,
                "type": customer.type,
                "credit_limit": float(customer.credit_limit)
            }
        )
        
        logger.info(f"Customer {customer.customer_number} created by {current_user.username}")
        
        return customer
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating customer: {e}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create customer: {str(e)}"
        )


@router.get("", response_model=CustomerListResponse)
async def list_customers(
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    search: Optional[str] = None,
    type_filter: Optional[str] = None,
    active_only: bool = True,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    List customers with optional filtering
    """
    query = db.query(Customer)
    
    # Apply filters
    if active_only:
        query = query.filter(Customer.is_active == True)
    
    if type_filter:
        query = query.filter(Customer.type == type_filter)
    
    if search:
        search_pattern = f"%{search}%"
        query = query.filter(
            or_(
                Customer.name.ilike(search_pattern),
                Customer.phone.ilike(search_pattern),
                Customer.email.ilike(search_pattern),
                Customer.customer_number.ilike(search_pattern)
            )
        )
    
    # Get total count
    total = query.count()
    
    # Paginate
    offset = (page - 1) * page_size
    items = query.order_by(Customer.name).offset(offset).limit(page_size).all()
    
    return CustomerListResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size
    )


@router.get("/{customer_id}", response_model=CustomerResponse)
async def get_customer(
    customer_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get customer details"""
    customer = db.query(Customer).filter(Customer.id == customer_id).first()
    
    if not customer:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Customer not found"
        )
    
    return customer


@router.put("/{customer_id}", response_model=CustomerResponse)
async def update_customer(
    customer_id: UUID,
    customer_data: CustomerUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role([UserRole.ADMIN, UserRole.MANAGER]))
):
    """
    Update customer (Admin/Manager only)
    """
    try:
        customer = db.query(Customer).filter(Customer.id == customer_id).first()
        
        if not customer:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Customer not found"
            )
        
        # Store old values for audit
        old_values = {
            "name": customer.name,
            "credit_limit": float(customer.credit_limit),
            "is_active": customer.is_active
        }
        
        # Update fields
        update_data = customer_data.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(customer, field, value)
        
        db.commit()
        db.refresh(customer)
        
        # Audit log
        log_audit(
            db=db,
            user_id=current_user.id,
            action="CUSTOMER_UPDATED",
            entity_type="customer",
            entity_id=str(customer.id),
            old_value=old_values,
            new_value={
                "name": customer.name,
                "credit_limit": float(customer.credit_limit),
                "is_active": customer.is_active
            }
        )
        
        logger.info(f"Customer {customer.customer_number} updated by {current_user.username}")
        
        return customer
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating customer: {e}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update customer: {str(e)}"
        )


@router.post("/{customer_id}/deactivate", response_model=CustomerResponse)
async def deactivate_customer(
    customer_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role([UserRole.ADMIN]))
):
    """
    Deactivate customer (Admin only)
    """
    try:
        customer = db.query(Customer).filter(Customer.id == customer_id).first()
        
        if not customer:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Customer not found"
            )
        
        # Check for outstanding balance
        if customer.current_balance > 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Cannot deactivate customer with outstanding balance of KES {customer.current_balance}"
            )
        
        customer.is_active = False
        db.commit()
        db.refresh(customer)
        
        # Audit log
        log_audit(
            db=db,
            user_id=current_user.id,
            action="CUSTOMER_DEACTIVATED",
            entity_type="customer",
            entity_id=str(customer.id),
            new_value={"customer_number": customer.customer_number}
        )
        
        logger.info(f"Customer {customer.customer_number} deactivated by {current_user.username}")
        
        return customer
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deactivating customer: {e}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to deactivate customer: {str(e)}"
        )


@router.post("/{customer_id}/check-credit", response_model=CreditCheckResponse)
async def check_credit(
    customer_id: UUID,
    request: CreditCheckRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Check if customer has available credit for transaction
    """
    customer = db.query(Customer).filter(Customer.id == customer_id).first()
    
    if not customer:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Customer not found"
        )
    
    if not customer.is_active:
        return CreditCheckResponse(
            customer_id=customer.id,
            customer_name=customer.name,
            credit_limit=customer.credit_limit,
            current_balance=customer.current_balance,
            available_credit=Decimal("0"),
            requested_amount=request.amount,
            can_proceed=False,
            message="Customer account is inactive"
        )
    
    available = Decimal(str(customer.available_credit))
    can_proceed = available >= request.amount
    
    if can_proceed:
        message = f"Credit approved. Available: KES {available}"
    else:
        shortage = request.amount - available
        message = f"Insufficient credit. Short by KES {shortage}"
    
    return CreditCheckResponse(
        customer_id=customer.id,
        customer_name=customer.name,
        credit_limit=customer.credit_limit,
        current_balance=customer.current_balance,
        available_credit=available,
        requested_amount=request.amount,
        can_proceed=can_proceed,
        message=message
    )


@router.get("/{customer_id}/statement", response_model=CustomerStatement)
async def get_customer_statement(
    customer_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get customer statement with invoices
    """
    customer = db.query(Customer).filter(Customer.id == customer_id).first()
    
    if not customer:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Customer not found"
        )
    
    # Get all invoices (excluding cancelled)
    invoices = db.query(Invoice).filter(
        Invoice.customer_id == customer_id,
        Invoice.status != InvoiceStatus.CANCELLED
    ).order_by(Invoice.created_at.desc()).all()
    
    # Calculate totals
    total_outstanding = sum(inv.balance for inv in invoices if inv.status in [InvoiceStatus.ISSUED, InvoiceStatus.PART_PAID])
    total_overdue = sum(inv.balance for inv in invoices if inv.is_overdue)
    
    # Find oldest invoice
    oldest_days = 0
    if invoices:
        oldest_invoice = max(invoices, key=lambda inv: inv.days_overdue if inv.is_overdue else 0)
        oldest_days = oldest_invoice.days_overdue
    
    return CustomerStatement(
        customer=customer,
        invoices=invoices,
        total_outstanding=Decimal(str(total_outstanding)),
        total_overdue=Decimal(str(total_overdue)),
        oldest_invoice_days=oldest_days
    )
