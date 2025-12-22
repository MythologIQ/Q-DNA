$ErrorActionPreference = "SilentlyContinue"

# Configuration
$Port = 5500
$LauncherDir = $PSScriptRoot
$ProjectRoot = Join-Path $LauncherDir ".."
$HtmlPath = Join-Path $LauncherDir "Launcher.html"

# Create TCP Listener with Port Hunting
$Address = [System.Net.IPAddress]::Loopback
$MaxRetries = 10
$Started = $false

for ($i = 0; $i -lt $MaxRetries; $i++) {
    try {
        $Listener = [System.Net.Sockets.TcpListener]::new($Address, $Port)
        $Listener.Start()
        $Started = $true
        # Ensure form support is loaded
        Add-Type -AssemblyName System.Windows.Forms
        break
    } catch {
        Write-Warning "Port $Port is in use. Trying next..."
        $Port++
    }
}

if (-not $Started) {
    Write-Error "Failed to find an open port between 5500 and 5510. Please free up a port."
    exit 1
}

Write-Host "🚀 QoreLogic Launcher listening on http://localhost:$Port/" -ForegroundColor Cyan

# Open Browser
Start-Process "http://localhost:$Port/"

try {
    while ($true) {
        if ($Listener.Pending()) {
            # ... (no change to connection logic) ...
            $Client = $Listener.AcceptTcpClient()
            $Stream = $Client.GetStream()
            $Buffer = New-Object byte[] 4096
            $BytesRead = $Stream.Read($Buffer, 0, $Buffer.Length)
            $RequestRaw = [System.Text.Encoding]::UTF8.GetString($Buffer, 0, $BytesRead)
            
            # Basic Parsing
            $RequestLine = $RequestRaw.Split("`r`n")[0]
            $Parts = $RequestLine.Split(" ")
            $Method = $Parts[0]
            $FullUrl = $Parts[1]
            
            # Split URL and Query
            if ($FullUrl.Contains("?")) {
                $Url = $FullUrl.Split("?")[0]
                $QueryString = $FullUrl.Split("?")[1]
            } else {
                $Url = $FullUrl
                $QueryString = ""
            }

            # Response Headers
            $BaseHeaders = "Access-Control-Allow-Origin: *`r`nAccess-Control-Allow-Methods: POST, GET, OPTIONS`r`nAccess-Control-Allow-Headers: Content-Type`r`nAccess-Control-Allow-Private-Network: true`r`nAccess-Control-Max-Age: 86400`r`n"
            
            # Router
            if ($Method -eq "OPTIONS") {
               # ...
               $Header = "HTTP/1.1 204 No Content`r`n${BaseHeaders}Connection: close`r`n`r`n"
               $Body = ""
            }
            elseif ($Url -eq "/" -or $Url -eq "/Launcher.html") {
                 $Header = "HTTP/1.1 200 OK`r`n${BaseHeaders}Content-Type: text/html; charset=utf-8`r`nConnection: close`r`n`r`n"
                 $Body = Get-Content $HtmlPath -Raw -Encoding UTF8
            }
            elseif ($Url -eq "/api/health") {
                 $Header = "HTTP/1.1 200 OK`r`n${BaseHeaders}Content-Type: application/json`r`nConnection: close`r`n`r`n"
                 $Body = '{"status": "ok", "service": "QoreLogic Launcher"}'
            }
            # --- UI Bridge (Phase 9/10 Extensions) ---
            elseif ($Url -match "^/api/(verification|trust|identity|ledger)") {
                $Action = ""
                # Map URL to Action
                if ($Url -match "/api/verification/config") { 
                    if ($Method -eq "POST") { $Action = "set_verification_config" } else { $Action = "get_verification_config" }
                }
                elseif ($Url -match "/api/trust/status") { $Action = "get_trust_status" }
                elseif ($Url -match "/api/identity/list") { $Action = "list_identities" }
                elseif ($Url -match "/api/identity/rotate") { $Action = "rotate_key" }
                elseif ($Url -match "/api/ledger/events") { $Action = "query_ledger" }
                
                # Extract Body for POST
                $JsonPayload = "{}"
                if ($Method -eq "POST") {
                     $HeaderBodySplit = $RequestRaw -split "`r`n`r`n"
                     if ($HeaderBodySplit.Count -lt 2) { $HeaderBodySplit = $RequestRaw -split "`n`n" }
                     if ($HeaderBodySplit.Count -ge 2) { $JsonPayload = $HeaderBodySplit[1].Trim("`0") }
                }
                
                if ($Action) {
                    $BridgeScript = Join-Path $ProjectRoot "local_fortress\bridge.py"
                    # Escape quotes for command line (PowerShell parsing madness)
                    $JsonArg = $JsonPayload.Replace('"', '\"')
                    
                    try {
                        # Invoke Python Bridge
                        $JsonOut = python "$BridgeScript" $Action --payload "$JsonArg" 2>&1
                        $Body = [string]::Join("`n", $JsonOut)
                        $Header = "HTTP/1.1 200 OK`r`n${BaseHeaders}Content-Type: application/json`r`nConnection: close`r`n`r`n"
                    } catch {
                        $Body = '{"success": false, "error": "Bridge execution failed"}'
                        $Header = "HTTP/1.1 500 Internal Error`r`n${BaseHeaders}Content-Type: application/json`r`nConnection: close`r`n`r`n"
                    }
                } else {
                    $Header = "HTTP/1.1 404 Not Found`r`n${BaseHeaders}Connection: close`r`n`r`n"
                    $Body = '{"error": "Endpoint not found"}'
                }
            }
            elseif ($Url -eq "/api/config/mode") {
                # Determine Ledger Path based on workspace param
                $LedgerPath = "$env:USERPROFILE\.qorelogic\ledger"
                
                # Check for workspace in JSON body (POST) or Query (GET/POST)
                $targetWorkspace = "default"
                
                # Simple query string parsing
                if ($QueryString -match 'workspace=([^&]*)') {
                    $targetWorkspace = $matches[1]
                }
                
                # If JSON body has workspace, override (for POST)
                if ($Method -eq "POST" -and $RequestRaw -match '"workspace"\s*:\s*"([^"]+)"') {
                    $targetWorkspace = $matches[1]
                }

                if ($targetWorkspace -ne "default" -and $targetWorkspace -ne "") {
                     $LedgerPath = "$env:USERPROFILE\.qorelogic\workspaces\$targetWorkspace\ledger"
                }

                $ModeFile = Join-Path $LedgerPath "system_mode"
                
                if (-not (Test-Path $LedgerPath)) { New-Item -ItemType Directory -Force -Path $LedgerPath | Out-Null }
                
                if ($Method -eq "GET") {
                    $Mode = "normal"
                    if (Test-Path $ModeFile) { $Mode = Get-Content $ModeFile -Raw }
                    $Header = "HTTP/1.1 200 OK`r`n${BaseHeaders}Content-Type: application/json`r`nConnection: close`r`n`r`n"
                    $Body = '{"mode": "' + $Mode.Trim() + '", "workspace": "' + $targetWorkspace + '"}'
                }
                elseif ($Method -eq "POST") {
                    # Extract JSON body by finding the double newline (header/body separator)
                    $HeaderBodySplit = $RequestRaw -split "`r`n`r`n"
                    if ($HeaderBodySplit.Count -lt 2) { $HeaderBodySplit = $RequestRaw -split "`n`n" } # Fallback for LF
                    $Json = $HeaderBodySplit[1].Trim("`0")
                    # Simple regex parsing since JSON depth is 1
                    if ($Json -match '"mode"\s*:\s*"(\w+)"') {
                        $NewMode = $matches[1]
                        Set-Content -Path $ModeFile -Value $NewMode
                        $Header = "HTTP/1.1 200 OK`r`n${BaseHeaders}Content-Type: application/json`r`nConnection: close`r`n`r`n"
                        $Body = '{"status": "ok", "mode": "' + $NewMode + '", "workspace": "' + $targetWorkspace + '"}'
                    } else {
                        $Header = "HTTP/1.1 400 Bad Request`r`n${BaseHeaders}Connection: close`r`n`r`n"
                        $Body = '{"error": "Invalid JSON"}'
                    }
                }
            }
            elseif ($Url -eq "/api/dialog/folder") {
                # In-Process Dialog (Requires -Sta on parent process)
                Add-Type -AssemblyName System.Windows.Forms
                $FolderBrowser = New-Object System.Windows.Forms.FolderBrowserDialog
                $FolderBrowser.Description = "Select Workspace Root Folder"
                $FolderBrowser.ShowNewFolderButton = $true
                
                $ResultPath = ""
                if ($FolderBrowser.ShowDialog() -eq [System.Windows.Forms.DialogResult]::OK) {
                    $ResultPath = $FolderBrowser.SelectedPath
                }
                
                $Header = "HTTP/1.1 200 OK`r`n${BaseHeaders}Content-Type: application/json`r`nConnection: close`r`n`r`n"
                # JSON escape backslashes
                $JsonPath = $ResultPath -replace "\\", "\\"
                $Body = '{"path": "' + $JsonPath + '"}'
            }
            elseif ($Url -eq "/api/launch" -and $Method -eq "POST") {
                $Header = "HTTP/1.1 200 OK`r`n${BaseHeaders}Content-Type: application/json`r`nConnection: close`r`n`r`n"
                
                # Extract Params
                $targetWorkspace = "default"
                $targetPath = ""
                
                try {
                    $JsonBodies = $RequestRaw.Split("`r`n`r`n")
                    if ($JsonBodies.Count -gt 1) {
                         $Json = $JsonBodies[1].Trim("`0")
                         # Convert JSON string to object for safer parsing (requires PS v6+ or .NET)
                         # Fallback to regex for compatibility
                         if ($Json -match '"workspace"\s*:\s*"([^"]+)"') {
                             $targetWorkspace = $matches[1]
                         }
                         # JSON path might have escaped slashes, regex needs to be loose
                         if ($Json -match '"path"\s*:\s*"((?:[^"\\]|\\.)*)"') {
                             $targetPath = $matches[1] -replace "\\\\", "\"
                         }
                    }
                } catch {
                     Write-Warning "Failed to parse launch body"
                }

                Write-Host "   [CMD] Launching QoreLogic Sovereign Container..." -ForegroundColor Yellow
                if ($targetPath) { Write-Host "         Root Context: $targetPath" -ForegroundColor Gray }
                
                # Single Ledger Path (Global History)
                $LedgerPath = "$env:USERPROFILE\.qorelogic\ledger"
                
                # Ensure Ledger Path Exists
                if (-not (Test-Path $LedgerPath)) { 
                    New-Item -ItemType Directory -Force -Path $LedgerPath | Out-Null 
                }

                $DeployScript = Join-Path $ProjectRoot "local_fortress\deploy_isolated.ps1"
                $WrapperPath = Join-Path $ProjectRoot "local_fortress\qorelogic-check.bat"
                
                # Build if necessary
                if (-not (Test-Path $WrapperPath)) {
                     Write-Host "   [CMD] Build required. Running deploy_isolated.ps1..."
                     Start-Process -FilePath "powershell.exe" -ArgumentList "-File `"$DeployScript`"" -WindowStyle Normal -Wait
                }
                
                # Determine Root Source Mount
                # Default: Mount QoreLogic itself
                $SourceMount = (Resolve-Path $ProjectRoot).Path
                
                if ($targetPath -and (Test-Path $targetPath)) {
                    $SourceMount = $targetPath
                } else {
                    if ($targetPath) { Write-Warning "Target path not found: $targetPath. Using default." }
                }

                # Check if Image Exists
                $ImageExists = docker images -q qorelogic:latest
                if (-not $ImageExists) {
                    Write-Host "   [CMD] Docker image missing. Rebuilding..." -ForegroundColor Yellow
                    Start-Process -FilePath "powershell.exe" -ArgumentList "-File `"$DeployScript`"" -Wait
                }

                # Clean up existing (Ruthless Protocol)
                # We use --force to combine stop/remove and ignore state.
                Write-Host "   [CMD] Clearing runtime application..." -ForegroundColor Gray
                
                $MaxCleanRetries = 5
                for ($i = 0; $i -lt $MaxCleanRetries; $i++) {
                    docker rm -f qorelogic-runtime 2>&1 | Out-Null
                    
                    # Verify it's gone
                    if (-not (docker ps -a -q -f name=qorelogic-runtime)) {
                        break
                    }
                    Start-Sleep -Milliseconds 500
                }
                
                # Final check before launch attempt
                if (docker ps -a -q -f name=qorelogic-runtime) {
                     Write-Error "CRITICAL: Unable to remove existing 'qorelogic-runtime' container. Docker may be locked."
                     return
                }

                # Launch:
                # 1. Mount Source Root -> /src (The "Territory" - User Code)
                # 2. Mount System Root -> /qorelogic_system (The "Police Station" - Our Code)
                # 3. Mount Global Ledger -> /app/ledger (The "Memory")
                # 4. Port 8000 for Dashboard API
                
                # We need the System Mount to ensure we run the PATCHED main.py even if user targets C:\
                $SystemMount = (Resolve-Path $ProjectRoot).Path
                
                # Command Construction (ENTRYPOINT is 'python', so we just pass the script path)
                # CRITICAL FIX: We must include /app/site-packages (where libraries actally live) 
                # AND /qorelogic_system (where our patched source lives).
                # Linux path separator is ':'
                $DockerArgs = "run --rm --name qorelogic-runtime -v `"$SourceMount`:/src`" -v `"$SystemMount`:/qorelogic_system`" -v `"$LedgerPath`:/app/ledger`" -p 8000:8000 -e QORELOGIC_DB_PATH=/app/ledger/qorelogic_soa_ledger.db -e PYTHONPATH=/app/site-packages:/qorelogic_system -e QORELOGIC_WORKSPACE_ROOT=/src -w /src qorelogic:latest /qorelogic_system/dashboard/backend/main.py"
                
                # Use -NoExit so the window stays open if Python crashes
                Start-Process -FilePath "powershell.exe" -ArgumentList "-NoExit -Command docker $DockerArgs"
                
                $Msg = "Launched QoreLogic auditing: $SourceMount"
                $Body = '{"status": "ok", "message": "' + ($Msg -replace "\\", "\\") + '"}'
            }
            elseif ($Url -eq "/api/config/agents" -and $Method -eq "POST") {
                $Header = "HTTP/1.1 200 OK`r`n${BaseHeaders}Content-Type: application/json`r`nConnection: close`r`n`r`n"
                
                try {
                    $JsonBodies = $RequestRaw.Split("`r`n`r`n")
                    $ConfigData = $JsonBodies[1].Trim("`0")
                    
                    # Save to global config
                    $ConfigDir = "$env:USERPROFILE\.qorelogic\config"
                    if (-not (Test-Path $ConfigDir)) { New-Item -ItemType Directory -Force -Path $ConfigDir | Out-Null }
                    
                    $ConfigFile = Join-Path $ConfigDir "agents.json"
                    Set-Content -Path $ConfigFile -Value $ConfigData
                    
                    Write-Host "   [CFG] Saved Agent Configuration" -ForegroundColor Cyan
                    $Body = '{"status": "ok", "message": "Configuration saved"}'
                } catch {
                    $Header = "HTTP/1.1 500 Internal Error`r`n${BaseHeaders}Connection: close`r`n`r`n"
                    $Body = '{"error": "' + $_.Exception.Message + '"}'
                }
            }
            elseif ($Url -eq "/api/stop" -and $Method -eq "POST") {
                $Header = "HTTP/1.1 200 OK`r`n${BaseHeaders}Content-Type: application/json`r`nConnection: close`r`n`r`n"
                
                Write-Host "   [CMD] Stopping QoreLogic Container..." -ForegroundColor Red
                
                # Stop the container by its fixed name
                Start-Process -FilePath "docker" -ArgumentList "stop qorelogic-runtime" -NoNewWindow -Wait
                
                $Body = '{"status": "ok", "message": "Container stopped"}'
            }
            else {
                $Header = "HTTP/1.1 404 Not Found`r`nConnection: close`r`n`r`n"
                $Body = "404 Not Found"
            }
            
            # Send Response
            $ResponseBytes = [System.Text.Encoding]::UTF8.GetBytes($Header + $Body)
            $Stream.Write($ResponseBytes, 0, $ResponseBytes.Length)
            $Client.Close()
        }
        Start-Sleep -Milliseconds 10
    }
} finally {
    $Listener.Stop()
}
