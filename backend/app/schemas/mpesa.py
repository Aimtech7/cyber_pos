from pydantic import BaseModel, Field, validator
from typing import Optional, List
from datetime import datetime
from decimal import Decimal
from uuid import UUID

# Payment Intent Schemas

class PaymentIntentCreate(BaseModel):
    """Request to initiate M-Pesa payment"""
    transaction_id: UUID
    phone_number: str = Field(..., pattern=r"^254\d{9}$", description="Phone number in format 254XXXXXXXXX")
    amount: Decimal = Field(..., gt=0, description="Amount in KES")

class PaymentIntentResponse(BaseModel):
    """Payment intent status response"""
    id: UUID
    transaction_id: UUID
    amount: Decimal
    phone_number: str
    status: str
    mpesa_checkout_request_id: Optional[str]
    mpesa_receipt_number: Optional[str]
    failure_reason: Optional[str]
    created_at: datetime
    expires_at: datetime
    confirmed_at: Optional[datetime]
    is_expired: bool
    is_pending: bool
    
    class Config:
        from_attributes = True

# M-Pesa Callback Schemas

class MpesaCallbackItem(BaseModel):
    """Individual item in M-Pesa callback"""
    Name: str
    Value: Optional[str]

class MpesaCallbackBody(BaseModel):
    """M-Pesa STK Push callback body"""
    stkCallback: dict

class MpesaCallbackData(BaseModel):
    """Full M-Pesa callback structure"""
    Body: MpesaCallbackBody

# M-Pesa Payment (Inbox) Schemas

class MpesaPaymentResponse(BaseModel):
    """M-Pesa payment inbox item"""
    id: UUID
    mpesa_receipt_number: str
    amount: Decimal
    phone_number: str
    transaction_date: datetime
    sender_name: Optional[str]
    is_matched: bool
    matched_transaction_id: Optional[UUID]
    matched_at: Optional[datetime]
    created_at: datetime
    
    class Config:
        from_attributes = True

class MpesaPaymentListResponse(BaseModel):
    """List of M-Pesa payments with pagination"""
    items: List[MpesaPaymentResponse]
    total: int
    page: int
    page_size: int
    unmatched_count: int
    unmatched_total: Decimal

# Manual Matching Schemas

class ManualMatchRequest(BaseModel):
    """Request to manually match M-Pesa payment to transaction"""
    mpesa_payment_id: UUID
    transaction_id: UUID
    notes: Optional[str] = None

class ManualMatchResponse(BaseModel):
    """Response after manual match"""
    success: bool
    message: str
    mpesa_payment: MpesaPaymentResponse

# Reconciliation Schemas

class ReconciliationReport(BaseModel):
    """Daily M-Pesa reconciliation report"""
    date: datetime
    
    # Expected (from transactions)
    expected_mpesa_count: int
    expected_mpesa_total: Decimal
    
    # Confirmed (from payment intents)
    confirmed_count: int
    confirmed_total: Decimal
    
    # Unmatched payments
    unmatched_count: int
    unmatched_total: Decimal
    
    # Failed/Expired intents
    failed_count: int
    failed_total: Decimal
    expired_count: int
    expired_total: Decimal
    
    # Variance
    variance_amount: Decimal
    variance_percentage: Decimal
    
    # Details
    unmatched_payments: List[MpesaPaymentResponse]
    failed_intents: List[PaymentIntentResponse]

# STK Push Initiation Response

class STKPushResponse(BaseModel):
    """Response from STK Push initiation"""
    payment_intent_id: UUID
    checkout_request_id: str
    merchant_request_id: str
    response_code: str
    response_description: str
    customer_message: str
