# B.DEV CLI Uninstaller for Windows
# Run this script as Administrator

$ErrorActionPreference = "Stop"

Write-Host "[INFO] B.DEV CLI Uninstaller" -ForegroundColor Cyan
Write-Host ""

# Get the script directory
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $ScriptDir

# Remove from PATH
$userPath = [Environment]::GetEnvironmentVariable("Path", "User")
$scriptPath = $ScriptDir

if ($userPath -like "*$scriptPath*") {
    Write-Host "[INFO] Removing B.DEV from PATH..." -ForegroundColor Yellow
    $newPath = ($userPath -split ';' | Where-Object { $_ -ne $scriptPath }) -join ';'
    [Environment]::SetEnvironmentVariable("Path", $newPath, "User")
    Write-Host "[OK] B.DEV removed from PATH" -ForegroundColor Green
} else {
    Write-Host "[OK] B.DEV not in PATH" -ForegroundColor Green
}

# Deactivate and uninstall
if (Test-Path "venv")) {
    Write-Host "[INFO] Uninstalling B.DEV CLI..." -ForegroundColor Yellow
    & ".\venv\Scripts\Activate.ps1"
    pip uninstall bdev-cli -y
    
    Write-Host "[INFO] Deactivating virtual environment..." -ForegroundColor Yellow
    deactivate
}

# Ask if user wants to remove venv
Write-Host ""
$removeVenv = Read-Host "[QUESTION] Remove virtual environment (venv)? (y/N)"
if ($removeVenv -eq 'y' -or $removeVenv -eq 'Y') {
    if (Test-Path "venv")) {
        Write-Host "[INFO] Removing virtual environment..." -ForegroundColor Yellow
        Remove-Item -Path "venv" -Recurse -Force
        Write-Host "[OK] Virtual environment removed" -ForegroundColor Green
    }
}

# Remove batch file
if (Test-Path "bdev.cmd") {
    Write-Host "[INFO] Removing batch file..." -ForegroundColor Yellow
    Remove-Item -Path "bdev.cmd" -Force
    Write-Host "[OK] Batch file removed" -ForegroundColor Green
}

Write-Host ""
Write-Host "[SUCCESS] B.DEV CLI uninstalled!" -ForegroundColor Green
Write-Host "Restart your terminal to complete the uninstallation." -ForegroundColor Yellow
