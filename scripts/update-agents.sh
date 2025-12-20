#!/bin/bash
# Script to update agents to point to new Core server
# Usage: ./update-agents.sh

set -e

CORE_IP="10.243.151.228"
CORE_URL="http://${CORE_IP}:8000"
USERNAME="methinked"
PASSWORD="107512625"

AGENTS=(
    "10.243.14.179"      # moria-pi
    "10.243.151.228"     # raspberrypi
)

echo "=== Updating Agents to use Core Server at ${CORE_URL} ==="
echo ""

for AGENT_IP in "${AGENTS[@]}"; do
    echo "Updating agent at ${AGENT_IP}..."
    
    # Update .env file on agent
    sshpass -p "${PASSWORD}" ssh -o StrictHostKeyChecking=no ${USERNAME}@${AGENT_IP} << ENDSSH
        cd ~/nexus-agent
        
        # Backup existing .env
        if [ -f .env ]; then
            cp .env .env.backup
        fi
        
        # Update NEXUS_CORE_URL
        sed -i "s|NEXUS_CORE_URL=.*|NEXUS_CORE_URL=${CORE_URL}|g" .env || \
        echo "NEXUS_CORE_URL=${CORE_URL}" >> .env
        
        # Remove old agent state to force re-registration
        rm -f data/agent_state.json
        
        # Restart agent
        pkill -f "python.*nexus.agent.main" || true
        sleep 2
        nohup venv/bin/python -m nexus.agent.main > agent.log 2>&1 &
        
        echo "Agent restarted"
ENDSSH
    
    echo "✓ Agent at ${AGENT_IP} updated"
    echo ""
done

echo "All agents updated successfully!"
echo "They will re-register with the new Core server at ${CORE_URL}"
