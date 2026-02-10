# B.DEV CLI - Load in Current Session
# Run this script to reload PATH and use B.DEV immediately

Write-Host "[INFO] Reloading PATH for current session..." -ForegroundColor Cyan

# Get current PATH from registry
$userPath = [Environment]::GetEnvironmentVariable("Path", "User")

# Update current session PATH
$env:Path = $userPath

# Add alias for current session
function bdev {
    python -m cli.main @args
}
Set-Alias -Name "bdev" -Value "bdev" -Force

# Add alias for uppercase
function B.DEV {
    python -m cli.main @args
}
Set-Alias -Name "B.DEV" -Value "B.DEV" -Force

Write-Host "[OK] B.DEV loaded in current session!" -ForegroundColor Green
Write-Host ""
Write-Host "You can now use:" -ForegroundColor Cyan
Write-Host "  bdev    - Launch B.DEV CLI"
Write-Host "  B.DEV   - Launch B.DEV CLI (uppercase)"
Write-Host ""
Write-Host "To make this permanent for new terminals, restart PowerShell" -ForegroundColor Yellow
