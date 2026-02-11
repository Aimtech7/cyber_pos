from fastapi import APIRouter, Depends, HTTPException, status, Response
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List
from uuid import UUID
from decimal import Decimal
from ..database import get_db
from ..schemas.transaction import TransactionCreate, TransactionResponse, TransactionVoid, TransactionItemResponse
from ..models.transaction import Transaction, TransactionItem, TransactionStatus, PaymentMethod
from ..models.shift import Shift, ShiftStatus
from ..models.user import User
from ..models.inventory import InventoryItem, StockMovement, MovementType
from ..models.service import Service
from ..core.permissions import Permission
from ..api.deps import get_current_user, require_permission
from ..utils.receipt import generate_receipt_pdf
from io import BytesIO

router = APIRouter(prefix="/transactions", tags=["Transactions"])


@router.get("/", response_model=List[TransactionResponse])
async def list_transactions(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """List transactions"""
    query = db.query(Transaction)
    
    # Attendants can only see their own transactions
    if current_user.role.value == "attendant":
        query = query.filter(Transaction.created_by == current_user.id)
    
    transactions = query.order_by(Transaction.created_at.desc()).offset(skip).limit(limit).all()
    return transactions


@router.get("/{transaction_id}", response_model=TransactionResponse)
async def get_transaction(
    transaction_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get transaction by ID"""
    transaction = db.query(Transaction).filter(Transaction.id == transaction_id).first()
    if not transaction:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Transaction not found"
        )
    
    # Attendants can only see their own transactions
    if current_user.role.value == "attendant" and transaction.created_by != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )
    
    return transaction


@router.post("/", response_model=TransactionResponse, status_code=status.HTTP_201_CREATED)
async def create_transaction(
    transaction_data: TransactionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a new transaction"""
    # Check if user has an open shift
    open_shift = db.query(Shift).filter(
        Shift.user_id == current_user.id,
        Shift.status == ShiftStatus.OPEN
    ).first()
    
    if not open_shift:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No open shift found. Please open a shift first."
        )
    
    # Check discount permission
    if transaction_data.discount_amount > 0:
        from ..core.permissions import has_permission
        if not has_permission(current_user.role, Permission.APPLY_DISCOUNT):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have permission to apply discounts"
            )
    
    # Get next transaction number
    max_number = db.query(func.max(Transaction.transaction_number)).scalar() or 0
    transaction_number = max_number + 1
    
    # Calculate totals
    total_amount = Decimal(0)
    items_data = []
    
    for item in transaction_data.items:
        # Validate price against service if service_id is provided
        if item.service_id:
            service = db.query(Service).filter(Service.id == item.service_id).first()
            if not service:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Service not found for item: {item.description}"
                )
            
            # Enforce base price validation (optional, but good for security)
            # For now, we trust the frontend but ensure the calculation is correct
            calculated_price = item.quantity * item.unit_price
            
            # Future improvement: Enforce unit_price matches service.base_price 
            # unless a discount/override is explicitly allowed.
        
        total_price = item.quantity * item.unit_price
        total_amount += total_price
        items_data.append({
            **item.model_dump(),
            "total_price": total_price
        })
    
    final_amount = total_amount - transaction_data.discount_amount
    
    # Create transaction
    transaction = Transaction(
        transaction_number=transaction_number,
        created_by=current_user.id,
        shift_id=open_shift.id,
        total_amount=total_amount,
        discount_amount=transaction_data.discount_amount,
        final_amount=final_amount,
        payment_method=transaction_data.payment_method,
        mpesa_code=transaction_data.mpesa_code,
        status=TransactionStatus.COMPLETED
    )
    db.add(transaction)
    db.flush()
    
    # Create transaction items and handle stock
    for item_data in items_data:
        transaction_item = TransactionItem(
            transaction_id=transaction.id,
            **item_data
        )
        db.add(transaction_item)
        
        # Deduct stock if service requires it
        if item_data["service_id"]:
            service = db.query(Service).filter(Service.id == item_data["service_id"]).first()
            if service and service.requires_stock and service.stock_item_id:
                stock_item = db.query(InventoryItem).filter(
                    InventoryItem.id == service.stock_item_id
                ).first()
                
                if stock_item:
                    # Deduct stock
                    stock_item.current_stock -= item_data["quantity"]
                    
                    # Record movement
                    movement = StockMovement(
                        item_id=stock_item.id,
                        movement_type=MovementType.USAGE,
                        quantity=-item_data["quantity"],
                        reference_id=str(transaction.id),
                        notes=f"Used for transaction #{transaction_number}",
                        created_by=current_user.id
                    )
                    db.add(movement)
    
    # Update shift totals
    open_shift.total_sales += final_amount
    if transaction_data.payment_method == PaymentMethod.CASH:
        open_shift.expected_cash = (open_shift.expected_cash or Decimal(0)) + final_amount
    elif transaction_data.payment_method == PaymentMethod.MPESA:
        open_shift.total_mpesa += final_amount
    
    db.commit()
    db.refresh(transaction)
    
    return transaction


@router.post("/{transaction_id}/void")
async def void_transaction(
    transaction_id: UUID,
    void_data: TransactionVoid,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission(Permission.VOID_TRANSACTION))
):
    """Void a transaction"""
    transaction = db.query(Transaction).filter(Transaction.id == transaction_id).first()
    if not transaction:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Transaction not found"
        )
    
    if transaction.status != TransactionStatus.COMPLETED:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only completed transactions can be voided"
        )
    
    transaction.status = TransactionStatus.VOIDED
    
    # Reverse stock movements
    for item in transaction.items:
        if item.service_id:
            service = db.query(Service).filter(Service.id == item.service_id).first()
            if service and service.requires_stock and service.stock_item_id:
                stock_item = db.query(InventoryItem).filter(
                    InventoryItem.id == service.stock_item_id
                ).first()
                
                if stock_item:
                    stock_item.current_stock += item.quantity
                    
                    movement = StockMovement(
                        item_id=stock_item.id,
                        movement_type=MovementType.ADJUSTMENT,
                        quantity=item.quantity,
                        reference_id=str(transaction.id),
                        notes=f"Void transaction #{transaction.transaction_number}: {void_data.reason}",
                        created_by=current_user.id
                    )
                    db.add(movement)
    
    db.commit()
    
    return {"message": "Transaction voided successfully"}


@router.get("/{transaction_id}/receipt")
async def get_receipt(
    transaction_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Generate receipt PDF"""
    transaction = db.query(Transaction).filter(Transaction.id == transaction_id).first()
    if not transaction:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Transaction not found"
        )
    
    # Prepare receipt data
    receipt_data = {
        "transaction_number": transaction.transaction_number,
        "date": transaction.created_at.strftime("%Y-%m-%d %H:%M"),
        "attendant_name": transaction.user.full_name,
        "items": [
            {
                "description": item.description,
                "quantity": float(item.quantity),
                "unit_price": float(item.unit_price),
                "total_price": float(item.total_price)
            }
            for item in transaction.items
        ],
        "total_amount": float(transaction.total_amount),
        "discount_amount": float(transaction.discount_amount),
        "final_amount": float(transaction.final_amount),
        "payment_method": transaction.payment_method.value,
        "mpesa_code": transaction.mpesa_code
    }
    
    pdf_buffer = generate_receipt_pdf(receipt_data)
    
    return Response(
        content=pdf_buffer.getvalue(),
        media_type="application/pdf",
        headers={
            "Content-Disposition": f"attachment; filename=receipt_{transaction.transaction_number}.pdf"
        }
    )
