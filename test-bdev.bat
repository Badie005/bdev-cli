@echo off
REM Test B.DEV in current directory
echo Testing B.DEV CLI...
echo.

REM Try lowercase
echo Testing: bdev
call "%~dp0bdev.cmd" --version
echo.

REM Try uppercase
echo Testing: B.DEV
call "%~dp0B.DEV.bat" --version
echo.

pause
