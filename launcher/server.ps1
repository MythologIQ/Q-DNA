$ErrorActionPreference = "SilentlyContinue"

# Configuration
$Port = 5500
$LauncherDir = $PSScriptRoot
$ProjectRoot = Join-Path $LauncherDir ".."
$HtmlPath = Join-Path $LauncherDir "Launcher.html"

# Initialize HttpListener
$Listener = New-Object System.Net.HttpListener
$Url = "http://localhost:$Port/"
$Listener.Prefixes.Add($Url)
$Listener.Start()

Write-Host "🚀 QoreLogic Launcher listening on $Url" -ForegroundColor Cyan
Write-Host "   Open this URL in your browser to start." -ForegroundColor Gray

# Open Browser
Start-Process $Url

while ($Listener.IsListening) {
    $Context = $Listener.GetContext()
    $Request = $Context.Request
    $Response = $Context.Response
    
    $Path = $Request.Url.LocalPath
    
    # Simple Router
    if ($Path -eq "/" -or $Path -eq "/Launcher.html") {
        # Serve HTML
        $Content = Get-Content $HtmlPath -Raw -Encoding UTF8
        $Buffer = [System.Text.Encoding]::UTF8.GetBytes($Content)
        $Response.ContentEncoding = [System.Text.Encoding]::UTF8
        $Response.ContentType = "text/html; charset=utf-8"
        $Response.ContentLength64 = $Buffer.Length
        $Response.OutputStream.Write($Buffer, 0, $Buffer.Length)
    }
    elseif ($Path -eq "/api/health") {
        $Json = '{"status": "ok"}'
        $Buffer = [System.Text.Encoding]::UTF8.GetBytes($Json)
        $Response.ContentType = "application/json"
        $Response.OutputStream.Write($Buffer, 0, $Buffer.Length)
    }
    elseif ($Path -eq "/api/launch" -and $Request.HttpMethod -eq "POST") {
        # Trigger the Deployment Script in a new process to avoid blocking
        $DeployScript = Join-Path $ProjectRoot "local_fortress\deploy_isolated.ps1"
        
        # We start the wrapper/build script
        # Note: deploy_isolated.ps1 rebuilds the container.
        # Maybe we assume it's built or we rebuild active?
        # User said "Start the dockerfile". Implies run.
        
        Write-Host "   [CMD] Launching QoreLogic Container..." -ForegroundColor Yellow
        
        # We start the container wrapper directly if it exists, else deploy
        $WrapperPath = Join-Path $ProjectRoot "local_fortress\qorelogic-check.bat"
        
        if (Test-Path $WrapperPath) {
             # Run the bat with --dashboard
             $Args = "--dashboard"
             Start-Process -FilePath $WrapperPath -ArgumentList $Args -WindowStyle Minimized
             $Msg = "Container launched"
        } else {
             # First time init
             Start-Process -FilePath "powershell.exe" -ArgumentList "-File `"$DeployScript`"" -WindowStyle Minimized -Wait
             Start-Process -FilePath $WrapperPath -ArgumentList "--dashboard" -WindowStyle Minimized
             $Msg = "Build complete and launched"
        }
        
        $Json = '{"status": "ok", "message": "' + $Msg + '"}'
        $Buffer = [System.Text.Encoding]::UTF8.GetBytes($Json)
        $Response.ContentType = "application/json"
        $Response.OutputStream.Write($Buffer, 0, $Buffer.Length)
    }
    elseif ($Path -eq "/api/config" -and $Request.HttpMethod -eq "POST") {
        # Parse Body for Env Vars
        # Simplified for demo
        $Json = '{"status": "saved"}'
        $Buffer = [System.Text.Encoding]::UTF8.GetBytes($Json)
        $Response.OutputStream.Write($Buffer, 0, $Buffer.Length)
    }
    else {
        $Response.StatusCode = 404
    }
    
    $Response.Close()
}
