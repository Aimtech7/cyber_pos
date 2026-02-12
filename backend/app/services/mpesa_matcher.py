"""
M-Pesa Payment Matching Service
Intelligently matches M-Pesa callbacks to payment intents and transactions
"""
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Optional, List, Dict, Any
from uuid import UUID
import logging

from ..models.payment_intent import PaymentIntent, PaymentIntentStatus
from ..models.mpesa_payment import MpesaPayment
from ..models.transaction import Transaction, PaymentMethod
from ..models.audit import AuditLog
from ..core.audit import log_audit

logger = logging.getLogger(__name__)

class MpesaMatcher:
    """Intelligent M-Pesa payment matching service"""
    
    # Matching tolerance (in KES)
    AMOUNT_TOLERANCE = Decimal("5.00")
    
    # Time window for fuzzy matching (minutes)
    TIME_WINDOW_MINUTES = 30
    
    def match_callback_to_intent(
        self,
        db: Session,
        checkout_request_id: str,
        mpesa_receipt_number: str,
        amount: Decimal,
        phone_number: str,
        transaction_date: datetime,
        callback_data: Dict[str, Any]
    ) -> Optional[PaymentIntent]:
        """
        Match M-Pesa callback to payment intent (Tier 1: Exact Match)
        
        Args:
            db: Database session
            checkout_request_id: CheckoutRequestID from callback
            mpesa_receipt_number: M-Pesa receipt number
            amount: Payment amount
            phone_number: Customer phone number
            transaction_date: M-Pesa transaction timestamp
            callback_data: Full callback payload
        
        Returns:
            Matched PaymentIntent or None
        """
        try:
            # Tier 1: Exact match by checkout_request_id
            intent = db.query(PaymentIntent).filter(
                PaymentIntent.mpesa_checkout_request_id == checkout_request_id
            ).first()
            
            if intent:
                logger.info(f"Exact match found for checkout_request_id: {checkout_request_id}")
                
                # Update intent with confirmation data
                intent.status = PaymentIntentStatus.CONFIRMED
                intent.mpesa_receipt_number = mpesa_receipt_number
                intent.mpesa_transaction_date = transaction_date
                intent.confirmed_at = datetime.utcnow()
                intent.callback_data = callback_data
                
                # Update transaction
                transaction = intent.transaction
                if transaction:
                    transaction.mpesa_code = mpesa_receipt_number
                    transaction.payment_method = PaymentMethod.MPESA
                
                db.commit()
                db.refresh(intent)
                
                logger.info(f"Payment intent {intent.id} confirmed with receipt {mpesa_receipt_number}")
                return intent
            
            logger.warning(f"No exact match found for checkout_request_id: {checkout_request_id}")
            return None
            
        except Exception as e:
            logger.error(f"Error matching callback to intent: {e}")
            db.rollback()
            return None
    
    def create_unmatched_payment(
        self,
        db: Session,
        mpesa_receipt_number: str,
        amount: Decimal,
        phone_number: str,
        transaction_date: datetime,
        sender_name: Optional[str],
        callback_data: Dict[str, Any]
    ) -> MpesaPayment:
        """
        Create unmatched M-Pesa payment record for manual matching
        
        Returns:
            Created MpesaPayment record
        """
        try:
            # Check if payment already exists
            existing = db.query(MpesaPayment).filter(
                MpesaPayment.mpesa_receipt_number == mpesa_receipt_number
            ).first()
            
            if existing:
                logger.warning(f"Payment {mpesa_receipt_number} already exists")
                return existing
            
            payment = MpesaPayment(
                mpesa_receipt_number=mpesa_receipt_number,
                amount=amount,
                phone_number=phone_number,
                transaction_date=transaction_date,
                sender_name=sender_name,
                raw_callback_data=callback_data,
                is_matched=False
            )
            
            db.add(payment)
            db.commit()
            db.refresh(payment)
            
            logger.info(f"Created unmatched payment: {mpesa_receipt_number}")
            return payment
            
        except Exception as e:
            logger.error(f"Error creating unmatched payment: {e}")
            db.rollback()
            raise
    
    def find_potential_matches(
        self,
        db: Session,
        mpesa_receipt_number: str,
        amount: Decimal,
        transaction_date: datetime,
        phone_number: str
    ) -> List[Transaction]:
        """
        Find potential transaction matches for unmatched M-Pesa payment (Tier 2 & 3)
        
        Uses fuzzy matching:
        - Amount within tolerance (±5 KES)
        - Time window (within 30 minutes)
        - M-Pesa payment method
        - Not already matched
        
        Returns:
            List of potential matching transactions
        """
        try:
            # Calculate time window
            time_start = transaction_date - timedelta(minutes=self.TIME_WINDOW_MINUTES)
            time_end = transaction_date + timedelta(minutes=self.TIME_WINDOW_MINUTES)
            
            # Calculate amount range
            amount_min = amount - self.AMOUNT_TOLERANCE
            amount_max = amount + self.AMOUNT_TOLERANCE
            
            # Query for potential matches
            potential_matches = db.query(Transaction).filter(
                Transaction.payment_method == PaymentMethod.MPESA,
                Transaction.final_amount >= amount_min,
                Transaction.final_amount <= amount_max,
                Transaction.created_at >= time_start,
                Transaction.created_at <= time_end,
                Transaction.mpesa_code.is_(None)  # Not already matched
            ).all()
            
            logger.info(f"Found {len(potential_matches)} potential matches for {mpesa_receipt_number}")
            return potential_matches
            
        except Exception as e:
            logger.error(f"Error finding potential matches: {e}")
            return []
    
    def manual_match(
        self,
        db: Session,
        mpesa_payment_id: UUID,
        transaction_id: UUID,
        user_id: UUID,
        notes: Optional[str] = None
    ) -> bool:
        """
        Manually match M-Pesa payment to transaction (Admin action)
        
        Args:
            db: Database session
            mpesa_payment_id: MpesaPayment ID
            transaction_id: Transaction ID to match
            user_id: User performing the match
            notes: Optional notes about the match
        
        Returns:
            True if successful, False otherwise
        """
        try:
            # Get payment and transaction
            payment = db.query(MpesaPayment).filter(
                MpesaPayment.id == mpesa_payment_id
            ).first()
            
            if not payment:
                logger.error(f"Payment {mpesa_payment_id} not found")
                return False
            
            if payment.is_matched:
                logger.error(f"Payment {mpesa_payment_id} already matched")
                return False
            
            transaction = db.query(Transaction).filter(
                Transaction.id == transaction_id
            ).first()
            
            if not transaction:
                logger.error(f"Transaction {transaction_id} not found")
                return False
            
            # Perform match
            payment.is_matched = True
            payment.matched_transaction_id = transaction_id
            payment.matched_at = datetime.utcnow()
            payment.matched_by = user_id
            
            # Update transaction
            transaction.mpesa_code = payment.mpesa_receipt_number
            transaction.payment_method = PaymentMethod.MPESA
            
            # Check if there's a payment intent for this transaction
            intent = db.query(PaymentIntent).filter(
                PaymentIntent.transaction_id == transaction_id,
                PaymentIntent.status == PaymentIntentStatus.PENDING
            ).first()
            
            if intent:
                intent.status = PaymentIntentStatus.CONFIRMED
                intent.mpesa_receipt_number = payment.mpesa_receipt_number
                intent.mpesa_transaction_date = payment.transaction_date
                intent.confirmed_at = datetime.utcnow()
                payment.matched_intent_id = intent.id
            
            # Audit log
            log_audit(
                db=db,
                user_id=user_id,
                action="MANUAL_MPESA_MATCH",
                entity_type="mpesa_payment",
                entity_id=str(mpesa_payment_id),
                old_value={"is_matched": False},
                new_value={
                    "is_matched": True,
                    "matched_transaction_id": str(transaction_id),
                    "notes": notes
                }
            )
            
            db.commit()
            
            logger.info(f"Manually matched payment {mpesa_payment_id} to transaction {transaction_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error in manual match: {e}")
            db.rollback()
            return False


# Singleton instance
mpesa_matcher = MpesaMatcher()
