@echo off
REM B.DEV CLI Direct Mode - Simple command interface for Windows
REM Works without terminal emulator requirements

setlocal
set "PROJECT_DIR=C:\Users\B.LAPTOP\Dev\Projects\bdev-cli"
set "PYTHON_EXE=%PROJECT_DIR%\venv\Scripts\python.exe"
set "DIRECT_SCRIPT=%PROJECT_DIR%\bdev_direct.py"

if exist "%PYTHON_EXE%" (
    "%PYTHON_EXE%" "%DIRECT_SCRIPT%"
) else (
    echo [ERROR] Python virtual environment not found
    echo Please run install.ps1 from the bdev-cli directory
    exit /b 1
)

endlocal
