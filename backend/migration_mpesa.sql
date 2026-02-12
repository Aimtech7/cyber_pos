-- Migration: M-Pesa Daraja Integration
-- Creates payment_intents and mpesa_payments tables

-- Payment Intents Table
CREATE TABLE IF NOT EXISTS payment_intents (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    transaction_id UUID NOT NULL REFERENCES transactions(id) ON DELETE CASCADE,
    
    -- Payment details
    amount NUMERIC(10, 2) NOT NULL,
    phone_number VARCHAR(15) NOT NULL,
    
    -- Status
    status VARCHAR(20) NOT NULL DEFAULT 'pending',
    
    -- M-Pesa tracking
    mpesa_request_id VARCHAR(100),
    mpesa_checkout_request_id VARCHAR(100) UNIQUE,
    mpesa_receipt_number VARCHAR(50),
    mpesa_transaction_date TIMESTAMPTZ,
    
    -- Additional data
    callback_data JSONB,
    failure_reason VARCHAR(500),
    
    -- Timestamps
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    expires_at TIMESTAMPTZ NOT NULL,
    confirmed_at TIMESTAMPTZ,
    
    -- Audit
    created_by UUID NOT NULL REFERENCES users(id)
);

-- Indexes for payment_intents
CREATE INDEX IF NOT EXISTS idx_payment_intents_transaction_id ON payment_intents(transaction_id);
CREATE INDEX IF NOT EXISTS idx_payment_intents_status ON payment_intents(status);
CREATE INDEX IF NOT EXISTS idx_payment_intents_expires_at ON payment_intents(expires_at);
CREATE INDEX IF NOT EXISTS idx_payment_intents_checkout_request ON payment_intents(mpesa_checkout_request_id);
CREATE INDEX IF NOT EXISTS idx_payment_intents_receipt ON payment_intents(mpesa_receipt_number);

-- M-Pesa Payments (Inbox) Table
CREATE TABLE IF NOT EXISTS mpesa_payments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    
    -- M-Pesa details
    mpesa_receipt_number VARCHAR(50) NOT NULL UNIQUE,
    amount NUMERIC(10, 2) NOT NULL,
    phone_number VARCHAR(15) NOT NULL,
    transaction_date TIMESTAMPTZ NOT NULL,
    sender_name VARCHAR(200),
    
    -- Matching
    is_matched BOOLEAN NOT NULL DEFAULT FALSE,
    matched_transaction_id UUID REFERENCES transactions(id),
    matched_intent_id UUID REFERENCES payment_intents(id),
    matched_at TIMESTAMPTZ,
    matched_by UUID REFERENCES users(id),
    
    -- Raw data
    raw_callback_data JSONB,
    
    -- Timestamps
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Indexes for mpesa_payments
CREATE INDEX IF NOT EXISTS idx_mpesa_payments_receipt ON mpesa_payments(mpesa_receipt_number);
CREATE INDEX IF NOT EXISTS idx_mpesa_payments_is_matched ON mpesa_payments(is_matched);
CREATE INDEX IF NOT EXISTS idx_mpesa_payments_transaction_date ON mpesa_payments(transaction_date);
CREATE INDEX IF NOT EXISTS idx_mpesa_payments_matched_transaction ON mpesa_payments(matched_transaction_id);
CREATE INDEX IF NOT EXISTS idx_mpesa_payments_amount ON mpesa_payments(amount);

-- Add check constraints
ALTER TABLE payment_intents ADD CONSTRAINT chk_payment_intents_status 
    CHECK (status IN ('pending', 'confirmed', 'failed', 'expired', 'cancelled'));

ALTER TABLE payment_intents ADD CONSTRAINT chk_payment_intents_amount 
    CHECK (amount > 0);

ALTER TABLE mpesa_payments ADD CONSTRAINT chk_mpesa_payments_amount 
    CHECK (amount > 0);
