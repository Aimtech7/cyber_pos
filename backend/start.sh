#!/bin/bash
set -e

echo "🚀 Starting CyberCafe POS Backend..."

# Wait a moment for network to be ready
sleep 2

echo "✅ Ready to connect to Supabase!"

# Migrations should be run manually or via init container
# echo "🔄 Running database migrations..."
# alembic upgrade head

# Seed database (continue even if it fails - data might already exist)
echo "🌱 Seeding database..."
python -m app.seed || echo "⚠️  Seeding skipped (data may already exist)"

# Start the application
echo "🎯 Starting FastAPI server..."
exec uvicorn app.main:app --host 0.0.0.0 --port 8000
