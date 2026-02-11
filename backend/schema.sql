-- Enable UUID extension if not already enabled
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- 1. Create ENUM Types
CREATE TYPE userrole AS ENUM ('ADMIN', 'MANAGER', 'ATTENDANT');
CREATE TYPE computerstatus AS ENUM ('AVAILABLE', 'IN_USE', 'OFFLINE', 'MAINTENANCE');
CREATE TYPE sessionstatus AS ENUM ('ACTIVE', 'COMPLETED', 'CANCELLED');
CREATE TYPE expensecategory AS ENUM ('RENT', 'UTILITIES', 'REPAIRS', 'SUPPLIES', 'OTHER');
CREATE TYPE pricingmode AS ENUM ('PER_PAGE', 'PER_MINUTE', 'PER_JOB', 'BUNDLE');
CREATE TYPE shiftstatus AS ENUM ('OPEN', 'CLOSED');
CREATE TYPE movementtype AS ENUM ('PURCHASE', 'USAGE', 'ADJUSTMENT');
CREATE TYPE paymentmethod AS ENUM ('CASH', 'MPESA');
CREATE TYPE transactionstatus AS ENUM ('COMPLETED', 'VOIDED', 'REFUNDED');

-- 2. Create Independent Tables

-- Users Table
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    username VARCHAR(50) NOT NULL UNIQUE,
    email VARCHAR(255) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    full_name VARCHAR(255) NOT NULL,
    role userrole NOT NULL,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL
);

-- Inventory Items Table
CREATE TABLE inventory_items (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(255) NOT NULL,
    unit VARCHAR(50) NOT NULL,
    current_stock NUMERIC(10, 2) NOT NULL DEFAULT 0,
    min_stock_level NUMERIC(10, 2) NOT NULL DEFAULT 0,
    unit_cost NUMERIC(10, 2) NOT NULL DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL
);
CREATE INDEX ix_inventory_items_name ON inventory_items(name);

-- 3. Create Dependent Tables

-- Audit Logs
CREATE TABLE audit_logs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id),
    action VARCHAR(100) NOT NULL,
    entity_type VARCHAR(50) NOT NULL,
    entity_id VARCHAR(255) NOT NULL,
    old_value JSONB,
    new_value JSONB,
    ip_address VARCHAR(45),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL
);
CREATE INDEX ix_audit_logs_action ON audit_logs(action);

-- Expenses
CREATE TABLE expenses (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    category expensecategory NOT NULL,
    description VARCHAR(500) NOT NULL,
    amount NUMERIC(10, 2) NOT NULL,
    expense_date DATE NOT NULL,
    recorded_by UUID NOT NULL REFERENCES users(id),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL
);

-- Services
CREATE TABLE services (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(255) NOT NULL,
    pricing_mode pricingmode NOT NULL,
    base_price NUMERIC(10, 2) NOT NULL,
    description VARCHAR(500),
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    requires_stock BOOLEAN NOT NULL DEFAULT FALSE,
    stock_item_id UUID REFERENCES inventory_items(id),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL
);
CREATE INDEX ix_services_name ON services(name);

-- Shifts
CREATE TABLE shifts (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id),
    opened_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL,
    closed_at TIMESTAMP WITH TIME ZONE,
    opening_cash NUMERIC(10, 2) NOT NULL,
    expected_cash NUMERIC(10, 2),
    counted_cash NUMERIC(10, 2),
    cash_difference NUMERIC(10, 2),
    total_sales NUMERIC(10, 2) NOT NULL DEFAULT 0,
    total_mpesa NUMERIC(10, 2) NOT NULL DEFAULT 0,
    status shiftstatus NOT NULL DEFAULT 'OPEN',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL
);

-- Stock Movements
CREATE TABLE stock_movements (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    item_id UUID NOT NULL REFERENCES inventory_items(id),
    movement_type movementtype NOT NULL,
    quantity NUMERIC(10, 2) NOT NULL,
    reference_id VARCHAR(255),
    notes VARCHAR(500),
    created_by UUID NOT NULL REFERENCES users(id),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL
);

-- Transactions
CREATE TABLE transactions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    transaction_number SERIAL UNIQUE,
    created_by UUID NOT NULL REFERENCES users(id),
    shift_id UUID NOT NULL REFERENCES shifts(id),
    total_amount NUMERIC(10, 2) NOT NULL,
    discount_amount NUMERIC(10, 2) NOT NULL DEFAULT 0,
    final_amount NUMERIC(10, 2) NOT NULL,
    payment_method paymentmethod NOT NULL,
    mpesa_code VARCHAR(50),
    status transactionstatus NOT NULL DEFAULT 'COMPLETED',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL
);

-- 4. Circular Dependency Handling: Computers & Sessions

-- Create Computers (without FK initially)
CREATE TABLE computers (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(50) NOT NULL UNIQUE,
    status computerstatus NOT NULL DEFAULT 'AVAILABLE',
    current_session_id UUID, -- FK to sessions added later
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL
);
CREATE INDEX ix_computers_name ON computers(name);

-- Create Sessions (FK to computers is fine now)
CREATE TABLE sessions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    computer_id UUID NOT NULL REFERENCES computers(id),
    started_by UUID NOT NULL REFERENCES users(id),
    start_time TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL,
    end_time TIMESTAMP WITH TIME ZONE,
    duration_minutes INTEGER,
    amount_charged NUMERIC(10, 2),
    transaction_id UUID REFERENCES transactions(id),
    status sessionstatus NOT NULL DEFAULT 'ACTIVE',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL
);

-- Transaction Items (depends on sessions/transactions/services)
CREATE TABLE transaction_items (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    transaction_id UUID NOT NULL REFERENCES transactions(id),
    service_id UUID REFERENCES services(id),
    session_id UUID REFERENCES sessions(id),
    description VARCHAR(500) NOT NULL,
    quantity NUMERIC(10, 2) NOT NULL,
    unit_price NUMERIC(10, 2) NOT NULL,
    total_price NUMERIC(10, 2) NOT NULL
);

-- 5. Add Circular Foreign Key
ALTER TABLE computers 
ADD CONSTRAINT fk_computers_current_session 
FOREIGN KEY (current_session_id) REFERENCES sessions(id);
