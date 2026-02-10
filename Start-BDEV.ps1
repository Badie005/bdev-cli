@echo off
REM Start PowerShell with B.DEV loaded
REM This opens a new PowerShell window with B.DEV available

echo Starting PowerShell with B.DEV CLI...
echo.

powershell -NoExit -Command "$env:Path = [Environment]::GetEnvironmentVariable('Path', 'Machine') + ';' + [Environment]::GetEnvironmentVariable('Path', 'User'); Write-Host '[OK] B.DEV is available!' -ForegroundColor Green; Write-Host 'Type: bdev or B.DEV' -ForegroundColor Cyan; Write-Host ''"
