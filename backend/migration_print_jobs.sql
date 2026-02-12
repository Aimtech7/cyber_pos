-- Migration: Print Job Queue System
-- Creates print_jobs table with status workflow and tracking

CREATE TABLE IF NOT EXISTS print_jobs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    job_number VARCHAR(50) UNIQUE NOT NULL,
    
    -- Job details
    computer_id UUID NOT NULL REFERENCES computers(id) ON DELETE CASCADE,
    requested_by VARCHAR(255) NOT NULL,
    description VARCHAR(500),
    pages_bw INTEGER NOT NULL DEFAULT 0,
    pages_color INTEGER NOT NULL DEFAULT 0,
    
    -- Pricing
    total_amount NUMERIC(10, 2) NOT NULL,
    
    -- Status
    status VARCHAR(20) NOT NULL DEFAULT 'pending',
    
    -- Transaction link
    transaction_id UUID REFERENCES transactions(id),
    
    -- Approval tracking
    approved_by UUID REFERENCES users(id),
    approved_at TIMESTAMPTZ,
    
    -- Rejection tracking
    rejected_by UUID REFERENCES users(id),
    rejected_at TIMESTAMPTZ,
    rejection_reason VARCHAR(500),
    
    -- Printed tracking
    printed_by UUID REFERENCES users(id),
    printed_at TIMESTAMPTZ,
    
    -- Timestamps
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Indexes for print_jobs
CREATE INDEX IF NOT EXISTS idx_print_jobs_job_number ON print_jobs(job_number);
CREATE INDEX IF NOT EXISTS idx_print_jobs_computer_id ON print_jobs(computer_id);
CREATE INDEX IF NOT EXISTS idx_print_jobs_status ON print_jobs(status);
CREATE INDEX IF NOT EXISTS idx_print_jobs_created_at ON print_jobs(created_at);
CREATE INDEX IF NOT EXISTS idx_print_jobs_transaction_id ON print_jobs(transaction_id);

-- Check constraints
ALTER TABLE print_jobs ADD CONSTRAINT chk_print_jobs_status 
    CHECK (status IN ('pending', 'approved', 'rejected', 'printed', 'cancelled'));

ALTER TABLE print_jobs ADD CONSTRAINT chk_print_jobs_pages 
    CHECK (pages_bw >= 0 AND pages_color >= 0 AND (pages_bw + pages_color) > 0);

ALTER TABLE print_jobs ADD CONSTRAINT chk_print_jobs_amount 
    CHECK (total_amount >= 0);

-- Trigger to update updated_at
CREATE OR REPLACE FUNCTION update_print_jobs_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_update_print_jobs_updated_at
    BEFORE UPDATE ON print_jobs
    FOR EACH ROW
    EXECUTE FUNCTION update_print_jobs_updated_at();
