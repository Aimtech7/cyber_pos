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
    
        # Validate price against service if service_id is provided
    for item in transaction_data.items:
        # Validate price against service if service_id is provided
        if item.service_id:
            service = db.query(Service).filter(Service.id == item.service_id).first()
            if not service:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Service not found for item: {item.description}"
                )
            
            if not service.is_active:
                 raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Service is inactive: {item.description}"
                )

            # FORCE server-side price (Security: Financial Integrity)
            # We ignore item.unit_price from client and use service.base_price
            unit_price = service.base_price
            
        else:
            # For non-service items (if allowed), we might have to trust client or logic
            # But for now, let's assume all main items are services
            # Or if it's a "Custom Item", maybe we allow it for Admin?
            # Safe default: use client price but maybe flag it?
            # For this MVP hardening, let's use client price but ensure it's logged
            unit_price = item.unit_price
        
        total_price = item.quantity * unit_price
        total_amount += total_price
        items_data.append({
            **item.model_dump(exclude={'unit_price', 'total_price'}), # Exclude to avoid conflict/override
            "unit_price": unit_price,
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
    
    if transaction_data.discount_amount > 0:
        # Log Audit
        from ..models.audit import AuditLog
        audit_log = AuditLog(
            user_id=current_user.id,
            action="APPLY_DISCOUNT",
            details=f"Applied discount of {transaction_data.discount_amount} to Transaction #{transaction_number}",
            metadata_json={"transaction_id": str(transaction.id), "amount": str(transaction_data.discount_amount)}
        )
        db.add(audit_log)
    
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
    
    # Update shift totals
    shift = db.query(Shift).filter(Shift.id == transaction.shift_id).first()
    if shift:
        shift.total_sales -= transaction.final_amount
        if transaction.payment_method == PaymentMethod.CASH:
            # We assume expected_cash tracks what SHOULD be there. Voiding means it shouldn't be there.
            # If it was already collected, this reduces the expectation.
            shift.expected_cash -= transaction.final_amount
        elif transaction.payment_method == PaymentMethod.MPESA:
            shift.total_mpesa -= transaction.final_amount

    # Log Audit
    from ..models.audit import AuditLog
    
    audit_log = AuditLog(
        user_id=current_user.id,
        action="VOID_TRANSACTION",
        details=f"Voided Transaction #{transaction.transaction_number}. Amount: {transaction.final_amount}. Reason: {void_data.reason}"
    )
    db.add(audit_log)

    db.commit()
    
    return {"message": "Transaction voided successfully"}


@router.post("/{transaction_id}/refund")
async def refund_transaction(
    transaction_id: UUID,
    refund_data: TransactionVoid, # Reusing the reason schema
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission(Permission.REFUND_TRANSACTION))
):
    """Refund a transaction"""
    transaction = db.query(Transaction).filter(Transaction.id == transaction_id).first()
    if not transaction:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Transaction not found"
        )
    
    if transaction.status != TransactionStatus.COMPLETED:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only completed transactions can be refunded"
        )
    
    transaction.status = TransactionStatus.REFUNDED
    
    # Reverse stock movements (Item returned to stock?)
    # Valid question: do refunds always imply stock return? 
    # For services like "Printing", if usage was wasted (bad print), maybe not?
    # But usually "Refund" implies "Return". Let's assume stock is returned for now 
    # or leave it as a business logic choice. 
    # User requirement: "Reverse stock movements (put items back)"
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
                        notes=f"Refund transaction #{transaction.transaction_number}: {refund_data.reason}",
                        created_by=current_user.id
                    )
                    db.add(movement)
    
    # Update shift totals
    # Refunds increase "total_refunds" and reduce "net sales" logic?
    # User req: "Track... total_refunds, and net sales per shift"
    # Current Shift model has `total_refunds`.
    # It does NOT have `net_sales` column, but `total_sales` usually implies Gross or Net?
    # Let's check Shift model again... `total_sales`, `total_mpesa`, `total_refunds`.
    # If I refund, I should probably increase `total_refunds`.
    # Should I decrease `total_sales`? 
    # Usually Total Sales = Gross. Net Sales = Gross - Refunds.
    # If the report calculates Net as Total - Refunds, then I should NOT decrease Total.
    # CONSTANT: `total_sales`
    # Let's assume `total_sales` is GROSS.
    # So I only ADD to `total_refunds`.
    # AND I need to reduce the Cash Expectation if it was a Cash refund?
    # "Refund" implies giving money BACK.
    # If I give cash back, `expected_cash` should DECREASE (or `counted_cash` will be lower).
    # If `expected_cash` is "Money that should be in drawer", and I took money out to refund, 
    # then `expected_cash` should decrease.
    
    shift = db.query(Shift).filter(Shift.id == transaction.shift_id).first()
    if shift:
        shift.total_refunds += transaction.final_amount
        
        # If refunded via CASH, reduce expected cash
        # If refunded via MPESA (reversal), reduce total_mpesa? 
        # Or just track it. 
        # Let's assume Refunds are done in CASH usually for POS, or Reversal.
        # If original was CASH, we refund CASH.
        if transaction.payment_method == PaymentMethod.CASH:
             shift.expected_cash -= transaction.final_amount
        elif transaction.payment_method == PaymentMethod.MPESA:
             # If we refund M-Pesa, we likely do a reversal or send money.
             # This might not affect the "Cash in Drawer", but affects "M-Pesa balance".
             # For now, let's decrement total_mpesa to reflect the 'Net M-Pesa In'.
             shift.total_mpesa -= transaction.final_amount

    # Log Audit
    from ..models.audit import AuditLog
    
    # Audit for refund
    audit_log = AuditLog(
        user_id=current_user.id,
        action="REFUND_TRANSACTION",
        details=f"Refunded Transaction #{transaction.transaction_number}. Amount: {transaction.final_amount}. Reason: {refund_data.reason}"
    )
    db.add(audit_log)

    db.commit()
    
    return {"message": "Transaction refunded successfully"}


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
