# B.DEV CLI Installation Verification
Write-Host ""
Write-Host "============================================" -ForegroundColor Cyan
Write-Host "  B.DEV CLI - Installation Verification" -ForegroundColor Cyan
Write-Host "============================================" -ForegroundColor Cyan
Write-Host ""

# Check directories
$projectDir = "C:\Users\B.LAPTOP\Dev\Projects\bdev-cli"
$binDir = "$env:LOCALAPPDATA\bin"

Write-Host "[CHECK] Project directory:" -ForegroundColor Yellow
Write-Host "  $projectDir" -ForegroundColor $(if (Test-Path $projectDir) { "Green" } else { "Red" })
Write-Host "  Status: $(if (Test-Path $projectDir) { 'EXISTS' } else { 'NOT FOUND' })" -ForegroundColor $(if (Test-Path $projectDir) { "Green" } else { "Red" })
Write-Host ""

Write-Host "[CHECK] Virtual environment:" -ForegroundColor Yellow
$venvExe = "$projectDir\venv\Scripts\python.exe"
Write-Host "  $venvExe" -ForegroundColor $(if (Test-Path $venvExe) { "Green" } else { "Red" })
Write-Host "  Status: $(if (Test-Path $venvExe) { 'EXISTS' } else { 'NOT FOUND' })" -ForegroundColor $(if (Test-Path $venvExe) { "Green" } else { "Red" })
Write-Host ""

Write-Host "[CHECK] Global bin directory:" -ForegroundColor Yellow
Write-Host "  $binDir" -ForegroundColor $(if (Test-Path $binDir) { "Green" } else { "Red" })
Write-Host "  Status: $(if (Test-Path $binDir) { 'EXISTS' } else { 'NOT FOUND' })" -ForegroundColor $(if (Test-Path $binDir) { "Green" } else { "Red" })
Write-Host ""

Write-Host "[CHECK] Global batch files:" -ForegroundColor Yellow
Write-Host "  $binDir\bdev.cmd" -ForegroundColor $(if (Test-Path "$binDir\bdev.cmd") { "Green" } else { "Red" })
Write-Host "  Status: $(if (Test-Path "$binDir\bdev.cmd") { 'EXISTS' } else { 'NOT FOUND' })" -ForegroundColor $(if (Test-Path "$binDir\bdev.cmd") { "Green" } else { "Red" })
Write-Host ""
Write-Host "  $binDir\B.DEV.bat" -ForegroundColor $(if (Test-Path "$binDir\B.DEV.bat") { "Green" } else { "Red" })
Write-Host "  Status: $(if (Test-Path "$binDir\B.DEV.bat") { 'EXISTS' } else { 'NOT FOUND' })" -ForegroundColor $(if (Test-Path "$binDir\B.DEV.bat") { "Green" } else { "Red" })
Write-Host ""

Write-Host "[CHECK] User PATH:" -ForegroundColor Yellow
$userPath = [Environment]::GetEnvironmentVariable("Path", "User")
if ($userPath -like "*$binDir*") {
    Write-Host "  Status: CONTAINS $binDir" -ForegroundColor Green
} else {
    Write-Host "  Status: DOES NOT CONTAIN $binDir" -ForegroundColor Red
}
Write-Host ""

Write-Host "[CHECK] Current session PATH:" -ForegroundColor Yellow
if ($env:Path -like "*$binDir*") {
    Write-Host "  Status: CONTAINS $binDir" -ForegroundColor Green
} Write-Host "  Status: DOES NOT CONTAIN $binDir" -ForegroundColor Yellow
Write-Host ""

Write-Host "[TEST] Running B.DEV from global location..." -ForegroundColor Yellow
try {
    & "$binDir\bdev.cmd" --version
    Write-Host "  Status: WORKS" -ForegroundColor Green
} catch {
    Write-Host "  Status: FAILED - $_" -ForegroundColor Red
}
Write-Host ""

Write-Host "============================================" -ForegroundColor Cyan
Write-Host "  Installation Summary" -ForegroundColor Cyan
Write-Host "============================================" -ForegroundColor Cyan

$allGood = $true
if (-not (Test-Path $projectDir)) { $allGood = $false }
if (-not (Test-Path $venvExe)) { $allGood = $false }
if (-not (Test-Path $binDir)) { $allGood = $false }
if (-not (Test-Path "$binDir\bdev.cmd")) { $allGood = $false }
if (-not (Test-Path "$binDir\B.DEV.bat")) { $allGood = $false }

if ($allGood) {
    Write-Host ""
    Write-Host "[SUCCESS] B.DEV is installed globally!" -ForegroundColor Green
    Write-Host ""
    Write-Host "To use B.DEV:" -ForegroundColor Cyan
    Write-Host "  1. Close this PowerShell window" -ForegroundColor White
    Write-Host "  2. Open a new PowerShell window" -ForegroundColor White
    Write-Host "  3. Type: bdev" -ForegroundColor White
    Write-Host "  4. Or type: B.DEV" -ForegroundColor White
    Write-Host ""
} else {
    Write-Host ""
    Write-Host "[WARNING] Some components are missing." -ForegroundColor Yellow
    Write-Host "Run install.ps1 to fix." -ForegroundColor Yellow
    Write-Host ""
}
