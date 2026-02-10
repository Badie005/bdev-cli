# B.DEV CLI Setup for Current Session
# Run this to use B.DEV immediately without restarting PowerShell

Write-Host ""
Write-Host "============================================" -ForegroundColor Cyan
Write-Host "  B.DEV CLI - Session Setup" -ForegroundColor Cyan
Write-Host "============================================" -ForegroundColor Cyan
Write-Host ""

# Define the project directory
$projectDir = "C:\Users\B.LAPTOP\Dev\Projects\bdev-cli"

# Add project directory to current session PATH
if ($env:Path -notlike "*$projectDir*") {
    $env:Path = "$env:Path;$projectDir"
    Write-Host "[OK] Added B.DEV to current session PATH" -ForegroundColor Green
} else {
    Write-Host "[OK] B.DEV already in PATH" -ForegroundColor Green
}

# Create function for bdev command
function bdev {
    & "$projectDir\bdev.exe" @args
}

# Create function for B.DEV (uppercase)
function B.DEV {
    & "$projectDir\bdev.exe" @args
}

Write-Host ""
Write-Host "Commands available in this session:" -ForegroundColor Cyan
Write-Host "  bdev    - Launch B.DEV CLI" -ForegroundColor White
Write-Host "  B.DEV   - Launch B.DEV CLI (uppercase)" -ForegroundColor White
Write-Host ""
Write-Host "Try it now:" -ForegroundColor Yellow
Write-Host "  bdev --version" -ForegroundColor Yellow
Write-Host "  bdev" -ForegroundColor Yellow
Write-Host ""
Write-Host "============================================" -ForegroundColor Cyan
Write-Host ""

# Test if working
Write-Host "Testing installation..." -ForegroundColor Yellow
& "$projectDir\bdev.exe" --version
