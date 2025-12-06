#!/bin/bash
set -e

echo "=== Nexus Core Server Setup ==="
echo "ZeroTier IP: 10.243.99.44"
echo ""

# Install prerequisites
echo "[1/6] Installing prerequisites..."
sudo apt update
sudo apt install -y python3.13-venv python3-pip

# Create virtual environment
echo "[2/6] Creating virtual environment..."
cd /home/methinked/Projects/nexus/nexus
python3 -m venv venv

# Activate and install dependencies
echo "[3/6] Installing Python dependencies..."
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
pip install jinja2  # For web dashboard

# Create .env file if it doesn't exist
echo "[4/6] Creating .env configuration..."
if [ ! -f .env ]; then
    cat > .env << 'EOF'
# Core Server Configuration
NEXUS_CORE_URL=http://10.243.99.44:8000
NEXUS_SHARED_SECRET=nexus-secret-key-change-in-production
NEXUS_JWT_SECRET_KEY=jwt-secret-key-change-in-production-min-32-chars
NEXUS_ENV=production

# Database
NEXUS_DB_PATH=data/nexus.db

# Log Retention
NEXUS_LOG_RETENTION_DAYS=7
NEXUS_LOG_CLEANUP_INTERVAL_HOURS=24
EOF
    echo "Created .env file"
else
    echo ".env file already exists, skipping"
fi

# Initialize database
echo "[5/6] Initializing database..."
mkdir -p data
python -m alembic upgrade head || echo "Database already initialized"

echo "[6/6] Setup complete!"
echo ""
echo "To start the Core server:"
echo "  cd /home/methinked/Projects/nexus/nexus"
echo "  source venv/bin/activate"
echo "  python -m nexus.core.main"
echo ""
echo "Server will be accessible at: http://10.243.99.44:8000"
