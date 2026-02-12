-- Anti-Theft Analytics & Alerts System Migration
-- Creates alerts table for security monitoring

-- Create alerts table
CREATE TABLE IF NOT EXISTS alerts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    
    -- Alert classification
    type VARCHAR(50) NOT NULL,
    severity VARCHAR(20) NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'open',
    
    -- Alert details
    message TEXT NOT NULL,
    description TEXT,
    
    -- Related entities and metadata (JSON)
    related_entity JSONB,
    metadata JSONB,
    
    -- Assignment and resolution
    assigned_to UUID REFERENCES users(id),
    acknowledged_by UUID REFERENCES users(id),
    acknowledged_at TIMESTAMP WITH TIME ZONE,
    resolved_by UUID REFERENCES users(id),
    resolved_at TIMESTAMP WITH TIME ZONE,
    resolution_notes TEXT,
    
    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL
);

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_alerts_type ON alerts(type);
CREATE INDEX IF NOT EXISTS idx_alerts_severity ON alerts(severity);
CREATE INDEX IF NOT EXISTS idx_alerts_status ON alerts(status);
CREATE INDEX IF NOT EXISTS idx_alerts_assigned_to ON alerts(assigned_to);
CREATE INDEX IF NOT EXISTS idx_alerts_created_at ON alerts(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_alerts_status_severity ON alerts(status, severity);

-- Create index on JSONB columns for querying
CREATE INDEX IF NOT EXISTS idx_alerts_related_entity ON alerts USING GIN (related_entity);
CREATE INDEX IF NOT EXISTS idx_alerts_metadata ON alerts USING GIN (metadata);

-- Trigger to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_alerts_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_update_alerts_updated_at
    BEFORE UPDATE ON alerts
    FOR EACH ROW
    EXECUTE FUNCTION update_alerts_updated_at();

-- Add check constraints for enum values
ALTER TABLE alerts ADD CONSTRAINT check_alert_type 
    CHECK (type IN ('void_abuse', 'discount_abuse', 'cash_discrepancy', 'inventory_manipulation', 'price_tampering'));

ALTER TABLE alerts ADD CONSTRAINT check_alert_severity 
    CHECK (severity IN ('low', 'medium', 'high', 'critical'));

ALTER TABLE alerts ADD CONSTRAINT check_alert_status 
    CHECK (status IN ('open', 'acknowledged', 'resolved'));

-- Comments for documentation
COMMENT ON TABLE alerts IS 'Security alerts for anti-theft analytics';
COMMENT ON COLUMN alerts.type IS 'Type of security alert';
COMMENT ON COLUMN alerts.severity IS 'Severity level of the alert';
COMMENT ON COLUMN alerts.status IS 'Current status of the alert';
COMMENT ON COLUMN alerts.related_entity IS 'JSON object with related entity details (type, id, name)';
COMMENT ON COLUMN alerts.metadata IS 'Additional alert metadata (thresholds, counts, etc.)';
