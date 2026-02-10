# Load B.DEV in Current Session (Temporary)
# Run this to use B.DEV immediately without restarting

Write-Host ""
Write-Host "============================================" -ForegroundColor Cyan
Write-Host "  B.DEV CLI - Load in Current Session" -ForegroundColor Cyan
Write-Host "============================================" -ForegroundColor Cyan
Write-Host ""

# Reload PATH from registry
Write-Host "[INFO] Reloading PATH from registry..." -ForegroundColor Yellow
$env:Path = [Environment]::GetEnvironmentVariable("Path", "Machine") + ";" + [Environment]::GetEnvironmentVariable("Path", "User")

Write-Host "[OK] PATH reloaded" -ForegroundColor Green
Write-Host ""

# Test if B.DEV is accessible
Write-Host "[TEST] Testing B.DEV command..." -ForegroundColor Yellow
try {
    bdev --version
    Write-Host ""
    Write-Host "[SUCCESS] B.DEV is now available!" -ForegroundColor Green
    Write-Host ""
    Write-Host "You can now use:" -ForegroundColor Cyan
    Write-Host "  bdev" -ForegroundColor White
    Write-Host "  B.DEV" -ForegroundColor White
    Write-Host ""
} catch {
    Write-Host "[ERROR] B.DEV not accessible: $_" -ForegroundColor Red
    Write-Host ""
    Write-Host "Troubleshooting:" -ForegroundColor Yellow
    Write-Host "  1. Make sure installation completed successfully" -ForegroundColor White
    Write-Host "  2. Run: verify-install.ps1" -ForegroundColor White
    Write-Host "  3. Close and restart PowerShell" -ForegroundColor White
    Write-Host ""
}

Write-Host "============================================" -ForegroundColor Cyan
Write-Host ""
