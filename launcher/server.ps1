$ErrorActionPreference = "SilentlyContinue"

# Configuration
$Port = 5500
$LauncherDir = $PSScriptRoot
$ProjectRoot = Join-Path $LauncherDir ".."
$HtmlPath = Join-Path $LauncherDir "Launcher.html"

# Create TCP Listener (No Admin Rights Needed)
$Address = [System.Net.IPAddress]::Loopback

try {
    $Listener = [System.Net.Sockets.TcpListener]::new($Address, $Port)
    $Listener.Start()
} catch {
    Write-Error "Failed to start listener on port $Port. It might be in use."
    Write-Error $_
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
            $Url = $Parts[1]
            
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
            elseif ($Url -eq "/api/launch" -and $Method -eq "POST") {
                $Header = "HTTP/1.1 200 OK`r`n${BaseHeaders}Content-Type: application/json`r`nConnection: close`r`n`r`n"
                
                Write-Host "   [CMD] Launching QoreLogic Container..." -ForegroundColor Yellow
                
                $DeployScript = Join-Path $ProjectRoot "local_fortress\deploy_isolated.ps1"
                $WrapperPath = Join-Path $ProjectRoot "local_fortress\qorelogic-check.bat"
                
                if (Test-Path $WrapperPath) {
                     $ArgsList = "/c start /min $WrapperPath --dashboard"
                     Start-Process -FilePath "cmd.exe" -ArgumentList $ArgsList -WindowStyle Minimized
                     $Msg = "Container launched"
                } else {
                     Start-Process -FilePath "powershell.exe" -ArgumentList "-File `"$DeployScript`"" -WindowStyle Normal -Wait
                     Start-Process -FilePath "cmd.exe" -ArgumentList "/c start /min $WrapperPath --dashboard" -WindowStyle Minimized
                     $Msg = "Build complete and launched"
                }
                $Body = '{"status": "ok", "message": "' + $Msg + '"}'
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
