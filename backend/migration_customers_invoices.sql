-- Migration: Customer Accounts & Invoicing System
-- Creates customers, invoices, invoice_items, invoice_payments tables
-- Alters transactions table to add customer_id and invoice_id

-- ============================================
-- CUSTOMERS TABLE
-- ============================================
CREATE TABLE IF NOT EXISTS customers (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    customer_number VARCHAR(50) UNIQUE NOT NULL,
    
    -- Customer details
    name VARCHAR(255) NOT NULL,
    phone VARCHAR(20),
    email VARCHAR(255),
    type VARCHAR(20) NOT NULL DEFAULT 'individual',
    notes TEXT,
    
    -- Credit management
    credit_limit NUMERIC(10, 2) NOT NULL DEFAULT 0,
    current_balance NUMERIC(10, 2) NOT NULL DEFAULT 0,
    
    -- Status
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    
    -- Timestamps
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Indexes for customers
CREATE INDEX IF NOT EXISTS idx_customers_customer_number ON customers(customer_number);
CREATE INDEX IF NOT EXISTS idx_customers_name ON customers(name);
CREATE INDEX IF NOT EXISTS idx_customers_is_active ON customers(is_active);

-- Check constraints for customers
ALTER TABLE customers ADD CONSTRAINT chk_customers_type 
    CHECK (type IN ('individual', 'institution'));

ALTER TABLE customers ADD CONSTRAINT chk_customers_credit_limit 
    CHECK (credit_limit >= 0);

ALTER TABLE customers ADD CONSTRAINT chk_customers_balance 
    CHECK (current_balance >= 0);


-- ============================================
-- INVOICES TABLE
-- ============================================
CREATE TABLE IF NOT EXISTS invoices (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    invoice_number VARCHAR(50) UNIQUE NOT NULL,
    
    -- Customer link
    customer_id UUID NOT NULL REFERENCES customers(id) ON DELETE CASCADE,
    
    -- Status and dates
    status VARCHAR(20) NOT NULL DEFAULT 'draft',
    issue_date DATE,
    due_date DATE,
    
    -- Amounts
    subtotal NUMERIC(10, 2) NOT NULL DEFAULT 0,
    tax_amount NUMERIC(10, 2) NOT NULL DEFAULT 0,
    total_amount NUMERIC(10, 2) NOT NULL DEFAULT 0,
    paid_amount NUMERIC(10, 2) NOT NULL DEFAULT 0,
    
    -- Notes
    notes TEXT,
    
    -- Audit
    created_by UUID NOT NULL REFERENCES users(id),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Indexes for invoices
CREATE INDEX IF NOT EXISTS idx_invoices_invoice_number ON invoices(invoice_number);
CREATE INDEX IF NOT EXISTS idx_invoices_customer_id ON invoices(customer_id);
CREATE INDEX IF NOT EXISTS idx_invoices_status ON invoices(status);
CREATE INDEX IF NOT EXISTS idx_invoices_due_date ON invoices(due_date);

-- Check constraints for invoices
ALTER TABLE invoices ADD CONSTRAINT chk_invoices_status 
    CHECK (status IN ('draft', 'issued', 'part_paid', 'paid', 'overdue', 'cancelled'));

ALTER TABLE invoices ADD CONSTRAINT chk_invoices_amounts 
    CHECK (subtotal >= 0 AND tax_amount >= 0 AND total_amount >= 0 AND paid_amount >= 0);


-- ============================================
-- INVOICE ITEMS TABLE
-- ============================================
CREATE TABLE IF NOT EXISTS invoice_items (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    invoice_id UUID NOT NULL REFERENCES invoices(id) ON DELETE CASCADE,
    
    -- Optional transaction link
    transaction_id UUID REFERENCES transactions(id),
    
    -- Item details
    description VARCHAR(500) NOT NULL,
    quantity NUMERIC(10, 2) NOT NULL,
    unit_price NUMERIC(10, 2) NOT NULL,
    total_price NUMERIC(10, 2) NOT NULL
);

-- Indexes for invoice_items
CREATE INDEX IF NOT EXISTS idx_invoice_items_invoice_id ON invoice_items(invoice_id);
CREATE INDEX IF NOT EXISTS idx_invoice_items_transaction_id ON invoice_items(transaction_id);

-- Check constraints for invoice_items
ALTER TABLE invoice_items ADD CONSTRAINT chk_invoice_items_quantity 
    CHECK (quantity > 0);

ALTER TABLE invoice_items ADD CONSTRAINT chk_invoice_items_prices 
    CHECK (unit_price >= 0 AND total_price >= 0);


-- ============================================
-- INVOICE PAYMENTS TABLE
-- ============================================
CREATE TABLE IF NOT EXISTS invoice_payments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    invoice_id UUID NOT NULL REFERENCES invoices(id) ON DELETE CASCADE,
    
    -- Payment details
    payment_date TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    amount NUMERIC(10, 2) NOT NULL,
    payment_method VARCHAR(20) NOT NULL,
    reference VARCHAR(100),
    notes TEXT,
    
    -- Audit
    recorded_by UUID NOT NULL REFERENCES users(id),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Indexes for invoice_payments
CREATE INDEX IF NOT EXISTS idx_invoice_payments_invoice_id ON invoice_payments(invoice_id);
CREATE INDEX IF NOT EXISTS idx_invoice_payments_payment_date ON invoice_payments(payment_date);

-- Check constraints for invoice_payments
ALTER TABLE invoice_payments ADD CONSTRAINT chk_invoice_payments_method 
    CHECK (payment_method IN ('cash', 'mpesa', 'bank_transfer'));

ALTER TABLE invoice_payments ADD CONSTRAINT chk_invoice_payments_amount 
    CHECK (amount > 0);


-- ============================================
-- ALTER TRANSACTIONS TABLE
-- ============================================
-- Add customer_id and invoice_id columns
ALTER TABLE transactions ADD COLUMN IF NOT EXISTS customer_id UUID REFERENCES customers(id);
ALTER TABLE transactions ADD COLUMN IF NOT EXISTS invoice_id UUID REFERENCES invoices(id);

-- Add indexes
CREATE INDEX IF NOT EXISTS idx_transactions_customer_id ON transactions(customer_id);
CREATE INDEX IF NOT EXISTS idx_transactions_invoice_id ON transactions(invoice_id);


-- ============================================
-- TRIGGERS
-- ============================================
-- Trigger to update customers.updated_at
CREATE OR REPLACE FUNCTION update_customers_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_update_customers_updated_at
    BEFORE UPDATE ON customers
    FOR EACH ROW
    EXECUTE FUNCTION update_customers_updated_at();

-- Trigger to update invoices.updated_at
CREATE OR REPLACE FUNCTION update_invoices_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_update_invoices_updated_at
    BEFORE UPDATE ON invoices
    FOR EACH ROW
    EXECUTE FUNCTION update_invoices_updated_at();
