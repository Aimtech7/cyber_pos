-- Migration: Production Hardening
-- Adds indexes and tenant support columns

-- Transactions
CREATE INDEX IF NOT EXISTS idx_transactions_created_at ON transactions(created_at);
ALTER TABLE transactions ADD COLUMN IF NOT EXISTS tenant_id VARCHAR(50);
CREATE INDEX IF NOT EXISTS idx_transactions_tenant_id ON transactions(tenant_id);
ALTER TABLE transactions ADD COLUMN IF NOT EXISTS branch_id VARCHAR(50) DEFAULT 'Main';

-- Transaction Items
CREATE INDEX IF NOT EXISTS idx_transaction_items_transaction_id ON transaction_items(transaction_id);

-- Inventory Items
ALTER TABLE inventory_items ADD COLUMN IF NOT EXISTS tenant_id VARCHAR(50);
CREATE INDEX IF NOT EXISTS idx_inventory_items_tenant_id ON inventory_items(tenant_id);

-- Stock Movements
CREATE INDEX IF NOT EXISTS idx_stock_movements_created_at ON stock_movements(created_at);
ALTER TABLE stock_movements ADD COLUMN IF NOT EXISTS tenant_id VARCHAR(50);
CREATE INDEX IF NOT EXISTS idx_stock_movements_tenant_id ON stock_movements(tenant_id);

-- Sessions
CREATE INDEX IF NOT EXISTS idx_sessions_computer_id ON sessions(computer_id);
ALTER TABLE sessions ADD COLUMN IF NOT EXISTS tenant_id VARCHAR(50);
CREATE INDEX IF NOT EXISTS idx_sessions_tenant_id ON sessions(tenant_id);

-- Audit Logs (in case it wasn't created by create_tables because it's new)
-- create_tables.py usually only creates MISSING tables, so this might be needed if using raw SQL
-- But since we added it to create_tables.py, it should be fine if we run that.
