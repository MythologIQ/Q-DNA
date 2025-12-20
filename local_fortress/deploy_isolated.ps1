# deploy_isolated.ps1
# Builds QoreLogic Gatekeeper in a sterile Docker container.
# Prevents local pollution (No 'pip install' on host).

$ErrorActionPreference = "Stop"

Write-Host "-> Initializing QoreLogic Sterile Build..." -ForegroundColor Cyan

# 1. Check for Docker
if (-not (Get-Command "docker" -ErrorAction SilentlyContinue)) {
    Write-Error "Docker is required for isolated deployment."
}

# 2. Setup Build Context
$ScriptDir = $PSScriptRoot
# Assuming script is run from local_fortress root
$DistDir = Join-Path $ScriptDir "dist"
$WhlFile = Get-ChildItem -Path $DistDir -Filter "qorelogic_gatekeeper-*.whl" | Select-Object -First 1

if (-not $WhlFile) {
    Write-Error "No .whl package found in $DistDir. Run 'python setup.py bdist_wheel' first?"
}

Write-Host "   - Artifact: $($WhlFile.Name)"

# Copy Dockerfile.dist to current scope for build
$SourceDocker = Join-Path $ScriptDir "Dockerfile.dist"
$DestDocker = Join-Path $DistDir "Dockerfile"
Copy-Item -Path $SourceDocker -Destination $DestDocker -Force

# Copy Dashboard Source to dist
Write-Host "   - Copying Dashboard source..."
$DashboardSource = Join-Path $ScriptDir "..\dashboard"
$DashboardDest = Join-Path $DistDir "dashboard"
if (Test-Path $DashboardSource) {
    Copy-Item -Path $DashboardSource -Destination $DashboardDest -Recurse -Force
} else {
    Write-Warning "Dashboard source not found at $DashboardSource"
}

# 3. Build Container
Write-Host "-> Building Sterile Container (qorelogic:latest)..." -ForegroundColor Yellow
# Build context is the dist/ folder where the wheel is
docker build --no-cache -t qorelogic:latest $DistDir

# 4. Create Wrapper Scripts
Write-Host "-> Creating Wrapper Scripts..." -ForegroundColor Yellow

$WrapperContent = @"
@echo off
rem Wrapper for QoreLogic Check running inside Docker

rem Ensure local ledger directory exists
if not exist "%USERPROFILE%\.qorelogic\ledger" mkdir "%USERPROFILE%\.qorelogic\ledger"

rem Run container with persistent ledger volume
docker run --rm --name qorelogic-runtime -v "%CD%:/src" -v "%USERPROFILE%\.qorelogic\ledger:/app/ledger" -p 8000:8000 -w /src qorelogic:latest -m qorelogic_gatekeeper.cli %*
"@

$WrapperPath = Join-Path $ScriptDir "qorelogic-check.bat"
Set-Content -Path $WrapperPath -Value $WrapperContent


# 5. Create Git Hook Installer
Write-Host "-> Creating Hook Installer (install_hook.ps1)..." -ForegroundColor Yellow

$HookInstallerContent = @"
param([string]`$TargetRepo)

`$ErrorActionPreference = "Stop"

if (-not `$TargetRepo) {
    Write-Error "Usage: .\install_hook.ps1 -TargetRepo <PathToRepo>"
}

$ScriptDir = "`$PSScriptRoot"
`$HookPath = Join-Path `$TargetRepo ".git\hooks\pre-commit"
`$WrapperPath = Join-Path `$ScriptDir "qorelogic-check.bat"

# Ensure target is a git repo
if (-not (Test-Path (Join-Path `$TargetRepo ".git"))) {
    Write-Error "Target is not a git repository: `$TargetRepo"
}

# Content for the pre-commit hook (Shell script for Git Bash compatibility)
`$HookContent = "#!/bin/sh
# QoreLogic Pre-Commit Hook
# Delegates to the sterile appliance wrapper

echo '🛡️  QoreLogic Gatekeeper Scanning...'

# Escape backslashes for bash compatibility if needed, or invoke via cmd
# We invoke the .bat wrapper directly
`"$WrapperPath`" --monitor ."

Set-Content -Path `$HookPath -Value `$HookContent
# No chmod needed on Windows usually, but good practice if using WSL interaction

Write-Host "✅ Hook installed in `$TargetRepo"
"@

$HookInstallerPath = Join-Path $ScriptDir "install_hook.ps1"
Set-Content -Path $HookInstallerPath -Value $HookInstallerContent

Write-Host "`n- Build Complete." -ForegroundColor Green
Write-Host "   - Container: qorelogic:latest"
Write-Host "   - Wrapper: $WrapperPath"
Write-Host "   - Hook Installer: $HookInstallerPath"
Write-Host "`nTo usage:"
Write-Host "   Local: .\qorelogic-check.bat --monitor your_file.py"
Write-Host "   Dashboard: .\qorelogic-check.bat --dashboard"
Write-Host "   Install Hook: .\install_hook.ps1 -TargetRepo ..\MyProject"

