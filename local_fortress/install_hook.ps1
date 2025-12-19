param([string]$TargetRepo)

$ErrorActionPreference = "Stop"

if (-not $TargetRepo) {
    Write-Error "Usage: .\install_hook.ps1 -TargetRepo <PathToRepo>"
}

G:\MythologIQ\Q-DNA\Q-DNA\local_fortress = "$PSScriptRoot"
$HookPath = Join-Path $TargetRepo ".git\hooks\pre-commit"
$WrapperPath = Join-Path $ScriptDir "qorelogic-check.bat"

# Ensure target is a git repo
if (-not (Test-Path (Join-Path $TargetRepo ".git"))) {
    Write-Error "Target is not a git repository: $TargetRepo"
}

# Content for the pre-commit hook (Shell script for Git Bash compatibility)
$HookContent = "#!/bin/sh
# QoreLogic Pre-Commit Hook
# Delegates to the sterile appliance wrapper

echo '🛡️  QoreLogic Gatekeeper Scanning...'

# Escape backslashes for bash compatibility if needed, or invoke via cmd
# We invoke the .bat wrapper directly
"G:\MythologIQ\Q-DNA\Q-DNA\local_fortress\qorelogic-check.bat" --monitor ."

Set-Content -Path $HookPath -Value $HookContent
# No chmod needed on Windows usually, but good practice if using WSL interaction

Write-Host "✅ Hook installed in $TargetRepo"
