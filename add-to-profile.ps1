# PowerShell Profile Script - Auto-load B.DEV
# Run this once to add B.DEV to your PowerShell profile

$profileDir = Split-Path -Parent $PROFILE
if (-not (Test-Path $profileDir)) {
    New-Item -ItemType Directory -Path $profileDir -Force | Out-Null
}

$profileContent = @'
# B.DEV CLI - Auto-load on startup
$binDir = "$env:LOCALAPPDATA\bin"
if (Test-Path $binDir) {
    if ($env:Path -notlike "*$binDir*") {
        $env:Path += ";$binDir"
    }
}

# Create aliases (optional)
function bdev { & "$binDir\bdev.cmd" @args }
function B.DEV { & "$binDir\B.DEV.bat" @args }
'@

Add-Content -Path $PROFILE -Value $profileContent

Write-Host "[OK] B.DEV added to PowerShell profile" -ForegroundColor Green
Write-Host ""
Write-Host "B.DEV will auto-load in new PowerShell windows!" -ForegroundColor Cyan
Write-Host "Restart PowerShell to apply changes." -ForegroundColor Yellow
