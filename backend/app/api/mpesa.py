"""
M-Pesa API Endpoints
Handles payment initiation, callbacks, inbox, matching, and reconciliation
"""
from fastapi import APIRouter, Depends, HTTPException, status, Request, BackgroundTasks
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_
from typing import List, Optional
from datetime import datetime, timedelta, date
from decimal import Decimal
from uuid import UUID
import logging

from ..database import get_db
from ..api.deps import get_current_user, require_role
from ..models.user import User, UserRole
from ..models.payment_intent import PaymentIntent, PaymentIntentStatus
from ..models.mpesa_payment import MpesaPayment
from ..models.transaction import Transaction, PaymentMethod, TransactionStatus
from ..schemas.mpesa import (
    PaymentIntentCreate,
    PaymentIntentResponse,
    STKPushResponse,
    MpesaCallbackData,
    MpesaPaymentResponse,
    MpesaPaymentListResponse,
    ManualMatchRequest,
    ManualMatchResponse,
    ReconciliationReport
)
from ..services.daraja import daraja_service
from ..services.mpesa_matcher import mpesa_matcher
from ..core.audit import log_audit
from ..config import settings

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/mpesa", tags=["M-Pesa"])


@router.post("/initiate", response_model=STKPushResponse)
async def initiate_mpesa_payment(
    payment_request: PaymentIntentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Initiate M-Pesa STK Push payment
    
    Creates a payment intent and triggers STK Push to customer's phone
    """
    try:
        # Validate transaction exists
        transaction = db.query(Transaction).filter(
            Transaction.id == payment_request.transaction_id
        ).first()
        
        if not transaction:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Transaction not found"
            )
        
        # Check if transaction already has a pending or confirmed intent
        existing_intent = db.query(PaymentIntent).filter(
            PaymentIntent.transaction_id == payment_request.transaction_id,
            PaymentIntent.status.in_([PaymentIntentStatus.PENDING, PaymentIntentStatus.CONFIRMED])
        ).first()
        
        if existing_intent:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Payment intent already exists with status: {existing_intent.status}"
            )
        
        # Create payment intent
        payment_intent = PaymentIntent(
            transaction_id=payment_request.transaction_id,
            amount=payment_request.amount,
            phone_number=payment_request.phone_number,
            status=PaymentIntentStatus.PENDING,
            created_by=current_user.id
        )
        
        db.add(payment_intent)
        db.flush()  # Get the ID without committing
        
        # Initiate STK Push
        stk_response = daraja_service.initiate_stk_push(
            phone_number=payment_request.phone_number,
            amount=float(payment_request.amount),
            account_reference=str(payment_request.transaction_id),
            transaction_desc=f"Payment for Transaction #{transaction.transaction_number}"
        )
        
        if not stk_response.get("success"):
            # STK Push failed
            payment_intent.status = PaymentIntentStatus.FAILED
            payment_intent.failure_reason = stk_response.get("error", "STK Push failed")
            db.commit()
            
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=stk_response.get("error", "Failed to initiate payment")
            )
        
        # Update intent with STK Push details
        payment_intent.mpesa_checkout_request_id = stk_response.get("checkout_request_id")
        payment_intent.mpesa_request_id = stk_response.get("merchant_request_id")
        
        db.commit()
        db.refresh(payment_intent)
        
        logger.info(f"STK Push initiated for transaction {payment_request.transaction_id}")
        
        return STKPushResponse(
            payment_intent_id=payment_intent.id,
            checkout_request_id=stk_response["checkout_request_id"],
            merchant_request_id=stk_response["merchant_request_id"],
            response_code=stk_response["response_code"],
            response_description=stk_response["response_description"],
            customer_message=stk_response["customer_message"]
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error initiating M-Pesa payment: {e}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to initiate payment: {str(e)}"
        )


@router.post("/callback")
async def mpesa_callback(
    request: Request,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """
    M-Pesa callback endpoint (PUBLIC - No authentication required)
    
    SECURITY:
    - IP allowlist validation (if configured)
    - Replay attack prevention (same checkout_request_id processed once)
    - Amount validation (matches expected amount)
    - Provider reference validation (checkout_request_id exists)
    """
    try:
        # SECURITY CHECK 1: IP Allowlist Validation
        client_ip = request.client.host if request.client else "unknown"
        allowed_ips = settings.get_mpesa_allowed_ips()
        
        if allowed_ips and client_ip not in allowed_ips:
            logger.warning(
                f"M-Pesa callback rejected from unauthorized IP: {client_ip}. "
                f"Allowed IPs: {allowed_ips}"
            )
            # Log security event
            log_audit(
                db=db,
                user_id=None,
                action="MPESA_CALLBACK_REJECTED",
                details={
                    "reason": "unauthorized_ip",
                    "client_ip": client_ip,
                    "allowed_ips": allowed_ips
                }
            )
            return {
                "ResultCode": 1,
                "ResultDesc": "Unauthorized"
            }
        
        # Get callback data
        callback_data = await request.json()
        logger.info(f"Received M-Pesa callback from {client_ip}: {callback_data}")
        
        # Extract callback data
        extracted = daraja_service.extract_callback_data(callback_data)
        
        if not extracted:
            logger.error("Failed to extract callback data")
            return {"ResultCode": 1, "ResultDesc": "Invalid callback data"}
        
        result_code = extracted["result_code"]
        checkout_request_id = extracted["checkout_request_id"]
        
        # SECURITY CHECK 2: Validate checkout_request_id exists
        if not checkout_request_id:
            logger.error("Callback missing checkout_request_id")
            return {"ResultCode": 1, "ResultDesc": "Missing checkout_request_id"}
        
        # SECURITY CHECK 3: Replay Attack Prevention
        # Check if this checkout_request_id has already been processed
        existing_intent = db.query(PaymentIntent).filter(
            PaymentIntent.mpesa_checkout_request_id == checkout_request_id
        ).first()
        
        if not existing_intent:
            logger.warning(
                f"Callback for unknown checkout_request_id: {checkout_request_id}. "
                "This could be a replay attack or orphaned callback."
            )
            # Log security event
            log_audit(
                db=db,
                user_id=None,
                action="MPESA_CALLBACK_UNKNOWN_REQUEST",
                details={
                    "checkout_request_id": checkout_request_id,
                    "callback_data": callback_data
                }
            )
            return {
                "ResultCode": 1,
                "ResultDesc": "Unknown checkout request"
            }
        
        # Check if already processed (replay attack)
        if existing_intent.status in [PaymentIntentStatus.CONFIRMED, PaymentIntentStatus.FAILED]:
            logger.warning(
                f"Replay attack detected: checkout_request_id {checkout_request_id} "
                f"already processed with status {existing_intent.status}"
            )
            # Log security event
            log_audit(
                db=db,
                user_id=None,
                action="MPESA_CALLBACK_REPLAY_DETECTED",
                details={
                    "checkout_request_id": checkout_request_id,
                    "existing_status": existing_intent.status.value,
                    "callback_data": callback_data
                }
            )
            # Still acknowledge to prevent retries
            return {
                "ResultCode": 0,
                "ResultDesc": "Already processed"
            }
        
        # Handle successful payment
        if result_code == 0:
            mpesa_receipt = extracted["mpesa_receipt_number"]
            amount = Decimal(str(extracted["amount"]))
            phone_number = str(extracted["phone_number"])
            transaction_date_str = str(extracted["transaction_date"])
            
            # SECURITY CHECK 4: Amount Validation
            # Verify amount matches expected amount (within tolerance for rounding)
            expected_amount = existing_intent.amount
            amount_diff = abs(amount - expected_amount)
            
            if amount_diff > Decimal("0.01"):  # 1 cent tolerance
                logger.error(
                    f"Amount mismatch for checkout_request_id {checkout_request_id}: "
                    f"Expected {expected_amount}, Got {amount}"
                )
                # Log security event
                log_audit(
                    db=db,
                    user_id=None,
                    action="MPESA_CALLBACK_AMOUNT_MISMATCH",
                    details={
                        "checkout_request_id": checkout_request_id,
                        "expected_amount": str(expected_amount),
                        "received_amount": str(amount),
                        "difference": str(amount_diff)
                    }
                )
                # Mark intent as failed
                existing_intent.status = PaymentIntentStatus.FAILED
                existing_intent.failure_reason = f"Amount mismatch: expected {expected_amount}, got {amount}"
                existing_intent.callback_data = callback_data
                db.commit()
                
                return {
                    "ResultCode": 1,
                    "ResultDesc": "Amount mismatch"
                }
            
            # Parse M-Pesa date format (YYYYMMDDHHmmss)
            try:
                transaction_date = datetime.strptime(transaction_date_str, "%Y%m%d%H%M%S")
            except:
                transaction_date = datetime.utcnow()
            
            # Try to match to payment intent
            matched_intent = mpesa_matcher.match_callback_to_intent(
                db=db,
                checkout_request_id=checkout_request_id,
                mpesa_receipt_number=mpesa_receipt,
                amount=amount,
                phone_number=phone_number,
                transaction_date=transaction_date,
                callback_data=callback_data
            )
            
            if not matched_intent:
                # Create unmatched payment for manual matching
                mpesa_matcher.create_unmatched_payment(
                    db=db,
                    mpesa_receipt_number=mpesa_receipt,
                    amount=amount,
                    phone_number=phone_number,
                    transaction_date=transaction_date,
                    sender_name=None,  # Not provided in STK callback
                    callback_data=callback_data
                )
                logger.warning(f"Created unmatched payment for receipt {mpesa_receipt}")
        
        # Handle failed payment
        else:
            # Find intent and mark as failed
            intent = db.query(PaymentIntent).filter(
                PaymentIntent.mpesa_checkout_request_id == checkout_request_id
            ).first()
            
            if intent:
                intent.status = PaymentIntentStatus.FAILED
                intent.failure_reason = extracted["result_desc"]
                intent.callback_data = callback_data
                db.commit()
                logger.info(f"Payment intent {intent.id} marked as failed")
        
        # Acknowledge callback
        return {
            "ResultCode": 0,
            "ResultDesc": "Success"
        }
        
    except Exception as e:
        logger.error(f"Error processing M-Pesa callback: {e}")
        # Log error for monitoring
        try:
            log_audit(
                db=db,
                user_id=None,
                action="MPESA_CALLBACK_ERROR",
                details={
                    "error": str(e),
                    "client_ip": request.client.host if request.client else "unknown"
                }
            )
        except:
            pass
        
        return {
            "ResultCode": 1,
            "ResultDesc": f"Error: {str(e)}"
        }


@router.get("/intent/{intent_id}", response_model=PaymentIntentResponse)
async def get_payment_intent(
    intent_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get payment intent status"""
    intent = db.query(PaymentIntent).filter(PaymentIntent.id == intent_id).first()
    
    if not intent:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Payment intent not found"
        )
    
    # Check if expired and update status
    if intent.is_expired and intent.status == PaymentIntentStatus.PENDING:
        intent.status = PaymentIntentStatus.EXPIRED
        db.commit()
        db.refresh(intent)
    
    return intent


@router.get("/inbox", response_model=MpesaPaymentListResponse)
async def get_mpesa_inbox(
    page: int = 1,
    page_size: int = 50,
    is_matched: Optional[bool] = None,
    date_from: Optional[date] = None,
    date_to: Optional[date] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role([UserRole.ADMIN, UserRole.MANAGER]))
):
    """
    Get M-Pesa inbox (all payments, matched and unmatched)
    Admin/Manager only
    """
    query = db.query(MpesaPayment)
    
    # Apply filters
    if is_matched is not None:
        query = query.filter(MpesaPayment.is_matched == is_matched)
    
    if date_from:
        query = query.filter(MpesaPayment.transaction_date >= datetime.combine(date_from, datetime.min.time()))
    
    if date_to:
        query = query.filter(MpesaPayment.transaction_date <= datetime.combine(date_to, datetime.max.time()))
    
    # Get total count
    total = query.count()
    
    # Get unmatched stats
    unmatched_count = db.query(func.count(MpesaPayment.id)).filter(
        MpesaPayment.is_matched == False
    ).scalar()
    
    unmatched_total = db.query(func.sum(MpesaPayment.amount)).filter(
        MpesaPayment.is_matched == False
    ).scalar() or Decimal("0")
    
    # Paginate
    offset = (page - 1) * page_size
    items = query.order_by(MpesaPayment.transaction_date.desc()).offset(offset).limit(page_size).all()
    
    return MpesaPaymentListResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        unmatched_count=unmatched_count,
        unmatched_total=unmatched_total
    )


@router.post("/match", response_model=ManualMatchResponse)
async def manual_match_payment(
    match_request: ManualMatchRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role([UserRole.ADMIN, UserRole.MANAGER]))
):
    """
    Manually match M-Pesa payment to transaction
    Admin/Manager only
    """
    success = mpesa_matcher.manual_match(
        db=db,
        mpesa_payment_id=match_request.mpesa_payment_id,
        transaction_id=match_request.transaction_id,
        user_id=current_user.id,
        notes=match_request.notes
    )
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to match payment"
        )
    
    # Get updated payment
    payment = db.query(MpesaPayment).filter(
        MpesaPayment.id == match_request.mpesa_payment_id
    ).first()
    
    return ManualMatchResponse(
        success=True,
        message="Payment matched successfully",
        mpesa_payment=payment
    )


@router.get("/reconciliation", response_model=ReconciliationReport)
async def get_reconciliation_report(
    report_date: date = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role([UserRole.ADMIN, UserRole.MANAGER]))
):
    """
    Get daily M-Pesa reconciliation report
    Admin/Manager only
    """
    if not report_date:
        report_date = date.today()
    
    date_start = datetime.combine(report_date, datetime.min.time())
    date_end = datetime.combine(report_date, datetime.max.time())
    
    # Expected M-Pesa (from transactions)
    expected_query = db.query(
        func.count(Transaction.id),
        func.sum(Transaction.final_amount)
    ).filter(
        Transaction.payment_method == PaymentMethod.MPESA,
        Transaction.status == TransactionStatus.COMPLETED,
        Transaction.created_at >= date_start,
        Transaction.created_at <= date_end
    )
    expected_count, expected_total = expected_query.first()
    expected_count = expected_count or 0
    expected_total = expected_total or Decimal("0")
    
    # Confirmed M-Pesa (from payment intents)
    confirmed_query = db.query(
        func.count(PaymentIntent.id),
        func.sum(PaymentIntent.amount)
    ).filter(
        PaymentIntent.status == PaymentIntentStatus.CONFIRMED,
        PaymentIntent.confirmed_at >= date_start,
        PaymentIntent.confirmed_at <= date_end
    )
    confirmed_count, confirmed_total = confirmed_query.first()
    confirmed_count = confirmed_count or 0
    confirmed_total = confirmed_total or Decimal("0")
    
    # Unmatched payments
    unmatched_payments = db.query(MpesaPayment).filter(
        MpesaPayment.is_matched == False,
        MpesaPayment.transaction_date >= date_start,
        MpesaPayment.transaction_date <= date_end
    ).all()
    
    unmatched_count = len(unmatched_payments)
    unmatched_total = sum(p.amount for p in unmatched_payments)
    
    # Failed intents
    failed_intents = db.query(PaymentIntent).filter(
        PaymentIntent.status == PaymentIntentStatus.FAILED,
        PaymentIntent.created_at >= date_start,
        PaymentIntent.created_at <= date_end
    ).all()
    
    failed_count = len(failed_intents)
    failed_total = sum(i.amount for i in failed_intents)
    
    # Expired intents
    expired_intents = db.query(PaymentIntent).filter(
        PaymentIntent.status == PaymentIntentStatus.EXPIRED,
        PaymentIntent.created_at >= date_start,
        PaymentIntent.created_at <= date_end
    ).all()
    
    expired_count = len(expired_intents)
    expired_total = sum(i.amount for i in expired_intents)
    
    # Calculate variance
    variance_amount = confirmed_total - expected_total
    variance_percentage = (variance_amount / expected_total * 100) if expected_total > 0 else Decimal("0")
    
    return ReconciliationReport(
        date=datetime.combine(report_date, datetime.min.time()),
        expected_mpesa_count=expected_count,
        expected_mpesa_total=expected_total,
        confirmed_count=confirmed_count,
        confirmed_total=confirmed_total,
        unmatched_count=unmatched_count,
        unmatched_total=unmatched_total,
        failed_count=failed_count,
        failed_total=failed_total,
        expired_count=expired_count,
        expired_total=expired_total,
        variance_amount=variance_amount,
        variance_percentage=variance_percentage,
        unmatched_payments=unmatched_payments,
        failed_intents=failed_intents
    )


@router.get("/potential-matches/{mpesa_payment_id}")
async def get_potential_matches(
    mpesa_payment_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role([UserRole.ADMIN, UserRole.MANAGER]))
):
    """
    Get potential transaction matches for unmatched M-Pesa payment
    Admin/Manager only
    """
    payment = db.query(MpesaPayment).filter(
        MpesaPayment.id == mpesa_payment_id
    ).first()
    
    if not payment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="M-Pesa payment not found"
        )
    
    if payment.is_matched:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Payment already matched"
        )
    
    # Find potential matches
    matches = mpesa_matcher.find_potential_matches(
        db=db,
        mpesa_receipt_number=payment.mpesa_receipt_number,
        amount=payment.amount,
        transaction_date=payment.transaction_date,
        phone_number=payment.phone_number
    )
    
    return {
        "mpesa_payment": payment,
        "potential_matches": matches,
        "match_count": len(matches)
    }
