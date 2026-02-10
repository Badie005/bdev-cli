# Copy B.DEV to AppData\Local\bin
$binDir = "$env:LOCALAPPDATA\bin"
$projectDir = "C:\Users\B.LAPTOP\Dev\Projects\bdev-cli"

Write-Host "[INFO] Copying B.DEV files to $binDir..." -ForegroundColor Cyan

# Create bin directory if it doesn't exist
if (-not (Test-Path $binDir)) {
    New-Item -ItemType Directory -Path $binDir -Force | Out-Null
    Write-Host "[OK] Created directory: $binDir" -ForegroundColor Green
}

# Copy batch files
Copy-Item "$projectDir\bdev.cmd" "$binDir\bdev.cmd" -Force
Copy-Item "$projectDir\B.DEV.bat" "$binDir\B.DEV.bat" -Force

Write-Host "[OK] Copied batch files" -ForegroundColor Green

# Add to user PATH if not already there
$userPath = [Environment]::GetEnvironmentVariable("Path", "User")
if ($userPath -notlike "*$binDir*") {
    Write-Host "[INFO] Adding $binDir to user PATH..." -ForegroundColor Yellow
    $newPath = "$userPath;$binDir"
    [Environment]::SetEnvironmentVariable("Path", $newPath, "User")
    Write-Host "[OK] Added to user PATH" -ForegroundColor Green
} else {
    Write-Host "[OK] Already in user PATH" -ForegroundColor Green
}

Write-Host ""
Write-Host "[SUCCESS] B.DEV is now globally available!" -ForegroundColor Green
Write-Host ""
Write-Host "Close and restart PowerShell, then run:" -ForegroundColor Cyan
Write-Host "  bdev" -ForegroundColor White
Write-Host "  B.DEV" -ForegroundColor White
