# Nexus Agent Deployment for Windows
# PowerShell script to deploy agents to Raspberry Pis

param(
    [string]$PiHost = "10.243.14.179",
    [string]$PiUser = "methinked",
    [string]$CoreHost = "10.243.29.55"
)

Write-Host "=== Nexus Agent Deployment to Raspberry Pi ===" -ForegroundColor Cyan
Write-Host "Target: $PiUser@$PiHost"
Write-Host "Core Server: $CoreHost:8000"
Write-Host ""

# Note: This script requires manual password entry for SSH
# Windows doesn't have sshpass by default

$TempDir = New-Item -ItemType Directory -Path "$env:TEMP\nexus-deploy-$(Get-Random)" -Force

try {
    Write-Host "[1/7] Creating deployment package..." -ForegroundColor Yellow
    
    # Create deployment structure
    New-Item -ItemType Directory -Path "$TempDir\nexus" -Force | Out-Null
    Copy-Item -Path "nexus\agent" -Destination "$TempDir\nexus\" -Recurse -Force
    Copy-Item -Path "nexus\shared" -Destination "$TempDir\nexus\" -Recurse -Force
    Copy-Item -Path "nexus\__init__.py" -Destination "$TempDir\nexus\" -Force
    Copy-Item -Path "requirements.txt" -Destination "$TempDir\" -Force
    Copy-Item -Path "requirements-agent.txt" -Destination "$TempDir\" -Force
    Copy-Item -Path "pyproject.toml" -Destination "$TempDir\" -Force
    
    # Create .env file
    $envContent = @"
# Nexus Agent Configuration
NEXUS_NODE_NAME=pi-$($PiHost.Split('.')[-1])
NEXUS_CORE_URL=http://${CoreHost}:8000
NEXUS_AGENT_PORT=8001
NEXUS_SHARED_SECRET=change-me-in-production
NEXUS_METRICS_INTERVAL=30
NEXUS_ENV=production
"@
    Set-Content -Path "$TempDir\.env" -Value $envContent
    
    # Create startup script
    $startScript = @"
#!/bin/bash
cd ~/nexus-agent
source venv/bin/activate
export PYTHONPATH=.
python3 -m nexus.agent.main
"@
    Set-Content -Path "$TempDir\start-agent.sh" -Value $startScript
    
    Write-Host "[2/7] Testing SSH connection..." -ForegroundColor Yellow
    Write-Host "You will be prompted for the password: 107512625" -ForegroundColor Cyan
    ssh -o StrictHostKeyChecking=no "$PiUser@$PiHost" "echo 'Connected to' `$(hostname)"
    
    if ($LASTEXITCODE -ne 0) {
        Write-Host "SSH connection failed!" -ForegroundColor Red
        exit 1
    }
    
    Write-Host "[3/7] Checking for existing agent installation..." -ForegroundColor Yellow
    $existingAgent = ssh "$PiUser@$PiHost" "test -d ~/nexus-agent && echo 'exists' || echo 'not found'"
    
    if ($existingAgent -match "exists") {
        Write-Host "Found existing agent installation. Stopping old agent..." -ForegroundColor Yellow
        ssh "$PiUser@$PiHost" "pkill -f 'nexus.agent.main' || true"
        Start-Sleep -Seconds 2
    }
    
    Write-Host "[4/7] Creating deployment directory on Pi..." -ForegroundColor Yellow
    ssh "$PiUser@$PiHost" "mkdir -p ~/nexus-agent"
    
    Write-Host "[5/7] Copying files to Pi (this may take a moment)..." -ForegroundColor Yellow
    scp -r -o StrictHostKeyChecking=no "$TempDir\*" "${PiUser}@${PiHost}:~/nexus-agent/"
    
    Write-Host "[6/7] Setting up Python environment on Pi..." -ForegroundColor Yellow
    ssh "$PiUser@$PiHost" @"
cd ~/nexus-agent && \
python3 -m venv venv && \
source venv/bin/activate && \
pip install --upgrade pip && \
pip install -r requirements-agent.txt
"@
    
    Write-Host "[7/7] Making startup script executable..." -ForegroundColor Yellow
    ssh "$PiUser@$PiHost" "chmod +x ~/nexus-agent/start-agent.sh"
    
    Write-Host ""
    Write-Host "=== Deployment Complete! ===" -ForegroundColor Green
    Write-Host ""
    Write-Host "To start the agent:" -ForegroundColor Cyan
    Write-Host "  ssh $PiUser@$PiHost" -ForegroundColor White
    Write-Host "  cd ~/nexus-agent && nohup ./start-agent.sh > agent.log 2>&1 &" -ForegroundColor White
    Write-Host ""
    Write-Host "To check status:" -ForegroundColor Cyan
    Write-Host "  curl http://${PiHost}:8001/health" -ForegroundColor White
    
} finally {
    # Cleanup
    Remove-Item -Path $TempDir -Recurse -Force -ErrorAction SilentlyContinue
}
