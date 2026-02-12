"""
Database Migration: Production Hardening
Adds receipt_hash field to transactions table
"""

-- Add receipt_hash column to transactions table
ALTER TABLE transactions 
ADD COLUMN receipt_hash VARCHAR(64);

-- Add index for faster lookups
CREATE INDEX idx_transactions_receipt_hash ON transactions(receipt_hash);

-- Add comment
COMMENT ON COLUMN transactions.receipt_hash IS 'SHA-256 hash for receipt tamper detection';
