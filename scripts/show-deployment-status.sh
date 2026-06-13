#!/bin/bash
# Quick deployment reference for Moria-Pi
# This script shows you what's ready and how to proceed

echo "╔════════════════════════════════════════════════════════════╗"
echo "║        NEXUS MORIA-PI DEPLOYMENT SUMMARY                  ║"
echo "║        Ready to Deploy - March 12, 2026                   ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo ""

NEXUS_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )/nexus" && pwd )"
cd "$NEXUS_DIR" || exit 1

echo "📋 DEPLOYMENT CONFIGURATION"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  Target Host:        moria-pi (10.243.14.179)"
echo "  Core Server:        orthanc-pi (10.243.151.228:8000)"
echo "  Agent Port:         8001"
echo "  Logs Directory:     /mnt/nexus-storage/logs (External HDD)"
echo "  Data Directory:     /mnt/nexus-storage/data (External HDD)"
echo "  Hardware:           Raspberry Pi 3B+ (ARMv7)"
echo ""

echo "📦 DEPLOYMENT SCRIPTS AVAILABLE"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
if [ -x scripts/deploy-moria-pi.sh ]; then
    echo "  ✅ scripts/deploy-moria-pi.sh (READY)"
else
    echo "  ❌ scripts/deploy-moria-pi.sh (NOT EXECUTABLE)"
fi

if [ -x scripts/wait-and-deploy-moria.sh ]; then
    echo "  ✅ scripts/wait-and-deploy-moria.sh (READY)"
else
    echo "  ❌ scripts/wait-and-deploy-moria.sh (NOT EXECUTABLE)"
fi

echo "  ✅ docs/deployment/moria-pi-deployment.md (GUIDE AVAILABLE)"
echo ""

echo "🚀 DEPLOYMENT COMMANDS"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "  Option 1: Wait for moria-pi to come online (RECOMMENDED)"
echo "  ────────────────────────────────────────────────────────"
echo "    cd $NEXUS_DIR"
echo "    ./scripts/wait-and-deploy-moria.sh"
echo ""
echo "  Option 2: Deploy immediately (if device is already online)"
echo "  ────────────────────────────────────────────────────────"
echo "    cd $NEXUS_DIR"
echo "    ./scripts/deploy-moria-pi.sh /mnt/nexus-storage"
echo ""

echo "✅ CHECK STATUS"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "  Is moria-pi online?"
echo "    ping 10.243.14.179"
echo ""
echo "  Is orthanc (core) running?"
echo "    curl http://10.243.151.228:8000/health"
echo ""

echo "📝 NEXT STEPS"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "  1. Ensure external HDD is mounted on moria-pi at:"
echo "     /mnt/nexus-storage"
echo ""
echo "  2. Run deployment (choose option above)"
echo ""
echo "  3. Monitor deployment progress - it will show:"
echo "     ✓ Connection check"
echo "     ✓ Port availability"
echo "     ✓ HDD availability"
echo "     ✓ Code deployment"
echo "     ✓ Python environment setup"
echo "     ✓ Service installation"
echo "     ✓ Service startup"
echo ""

echo "🔍 VERIFY DEPLOYMENT"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "  After deployment completes:"
echo ""
echo "    # Check agent is running"
echo "    ssh methinked@10.243.14.179 'systemctl status nexus-agent'"
echo ""
echo "    # Test health endpoint"
echo "    curl http://10.243.14.179:8001/health"
echo ""
echo "    # View logs (stored on external HDD)"
echo "    ssh methinked@10.243.14.179 'tail -f /mnt/nexus-storage/logs/*.log'"
echo ""
echo "    # Check registration on orthanc"
echo "    curl http://10.243.151.228:8000/api/nodes"
echo ""

echo "📖 FULL GUIDE"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  See: docs/deployment/moria-pi-deployment.md"
echo "  Or:  MORIA_DEPLOYMENT.md"
echo ""
echo "╔════════════════════════════════════════════════════════════╗"
echo "║  Ready to deploy! Run one of the commands above.           ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo ""
