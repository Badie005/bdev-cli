# B.DEV CLI Installer for Windows
# Run this script as Administrator

$ErrorActionPreference = "Stop"

Write-Host "[INFO] B.DEV CLI Installer" -ForegroundColor Cyan
Write-Host ""

# Check if Python is installed
try {
    $pythonVersion = python --version 2>&1
    Write-Host "[OK] Python found: $pythonVersion" -ForegroundColor Green
} catch {
    Write-Host "[ERROR] Python is not installed. Please install Python 3.10+ first." -ForegroundColor Red
    exit 1
}

# Get the script directory
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $ScriptDir

# Check if venv exists, if not create it
if (-not (Test-Path "venv")) {
    Write-Host "[INFO] Creating virtual environment..." -ForegroundColor Yellow
    python -m venv venv
} else {
    Write-Host "[OK] Virtual environment already exists" -ForegroundColor Green
}

# Activate virtual environment
Write-Host "[INFO] Activating virtual environment..." -ForegroundColor Yellow
& ".\venv\Scripts\Activate.ps1"

# Upgrade pip
Write-Host "[INFO] Upgrading pip..." -ForegroundColor Yellow
python -m pip install --upgrade pip

# Install requirements
Write-Host "[INFO] Installing dependencies..." -ForegroundColor Yellow
pip install rich>=13.0 prompt_toolkit>=3.0 typer>=0.9 pyotp>=2.9 "passlib[bcrypt]>=1.7" cryptography>=41.0

# Install the package in development mode
Write-Host "[INFO] Installing B.DEV CLI..." -ForegroundColor Yellow
pip install -e .

# Copy batch files to AppData\Local\bin for global access
$binDir = "$env:LOCALAPPDATA\bin"
Write-Host "[INFO] Installing B.DEV globally to $binDir..." -ForegroundColor Yellow

if (-not (Test-Path $binDir)) {
    New-Item -ItemType Directory -Path $binDir -Force | Out-Null
}

# Create global batch files
$globalBatchContent = @"
@echo off
REM B.DEV CLI Launcher - Global installation
set "PROJECT_DIR=C:\Users\B.LAPTOP\Dev\Projects\bdev-cli"
set "PYTHON_EXE=%PROJECT_DIR%\venv\Scripts\python.exe"
if exist "%PYTHON_EXE%" (
    "%PYTHON_EXE%" -m cli.main %*
) else (
    echo [ERROR] Virtual environment not found. Please reinstall B.DEV CLI.
)
"@

$globalBatchContent | Out-File -FilePath "$binDir\bdev.cmd" -Encoding ASCII
$globalBatchContent | Out-File -FilePath "$binDir\B.DEV.bat" -Encoding ASCII

# Add bin directory to user PATH
$userPath = [Environment]::GetEnvironmentVariable("Path", "User")
if ($userPath -notlike "*$binDir*") {
    Write-Host "[INFO] Adding $binDir to PATH..." -ForegroundColor Yellow
    [Environment]::SetEnvironmentVariable("Path", "$userPath;$binDir", "User")
    Write-Host "[OK] B.DEV added to PATH" -ForegroundColor Green
} else {
    Write-Host "[OK] B.DEV already in PATH" -ForegroundColor Green
}

Write-Host ""
Write-Host "[SUCCESS] B.DEV CLI installed successfully!" -ForegroundColor Green
Write-Host ""
Write-Host "Usage:" -ForegroundColor Cyan
Write-Host "  bdev          - Show help"
Write-Host "  B.DEV         - Show help (uppercase also works)"
Write-Host "  bdev repl     - Start interactive mode"
Write-Host "  bdev version  - Show version"
Write-Host ""
Write-Host "Just type 'bdev' or 'B.DEV' in your terminal to start!" -ForegroundColor Yellow
