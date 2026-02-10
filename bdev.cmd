@echo off
REM B.DEV CLI Launcher - Local usage (from project directory)
set "PYTHON_EXE=%~dp0venv\Scripts\python.exe"

if exist "%PYTHON_EXE%" (
    "%PYTHON_EXE%" -m cli.main %*
) else (
    echo [ERROR] Virtual environment not found. Please run install.ps1 first.
)
