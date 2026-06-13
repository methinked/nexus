#!/bin/bash
# Wait for Moria-Pi to come online and then deploy
# Usage: ./wait-and-deploy-moria.sh [HDD_path] [retries] [retry_interval_seconds]

HDD_PATH="${1:-/mnt/nexus-storage}"
MAX_RETRIES="${2:-60}"
RETRY_INTERVAL="${3:-5}"

PI_HOST="10.243.14.179"
PI_USER="methinked"
PI_PASS="107512625"

echo "⏳ Waiting for moria-pi to come online..."
echo "   Host: $PI_HOST"
echo "   Will retry up to $MAX_RETRIES times (every ${RETRY_INTERVAL}s)"
echo ""

RETRY_COUNT=0
while [ $RETRY_COUNT -lt $MAX_RETRIES ]; do
    echo -n "[$((RETRY_COUNT + 1))/$MAX_RETRIES] Testing SSH... "
    
    if timeout 3 sshpass -p "$PI_PASS" ssh -o StrictHostKeyChecking=no \
       "$PI_USER@$PI_HOST" "echo 'Online'" > /dev/null 2>&1; then
        echo "✅ ONLINE!"
        echo ""
        echo "🚀 Moria-pi is reachable! Starting deployment..."
        echo ""
        
        # Run the deployment script
        cd "$(dirname "$0")/.." || exit 1
        ./scripts/deploy-moria-pi.sh "$HDD_PATH"
        exit $?
    fi
    
    echo "not responding yet"
    RETRY_COUNT=$((RETRY_COUNT + 1))
    
    if [ $RETRY_COUNT -lt $MAX_RETRIES ]; then
        sleep $RETRY_INTERVAL
    fi
done

echo ""
echo "❌ Moria-pi did not come online after ${RETRY_COUNT} retries (${RETRY_COUNT}*${RETRY_INTERVAL}s)"
echo ""
echo "Troubleshooting:"
echo "  1. Check if moria-pi is powered on"
echo "  2. Verify network connectivity: ping 10.243.14.179"
echo "  3. Check ZeroTier status (if using VPN)"
echo "  4. Verify SSH credentials are correct"
echo ""
echo "Manual SSH test:"
echo "  ssh methinked@10.243.14.179"
echo ""
