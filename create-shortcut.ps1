# Create Desktop Shortcut for B.DEV
Write-Host "[INFO] Creating desktop shortcut..." -ForegroundColor Cyan

$desktopPath = [Environment]::GetFolderPath("Desktop")
$shortcutPath = "$desktopPath\B.DEV CLI.lnk"
$targetPath = "C:\Users\B.LAPTOP\AppData\Local\bin\bdev.cmd"

Write-Host "Desktop: $desktopPath" -ForegroundColor Yellow
Write-Host "Shortcut: $shortcutPath" -ForegroundColor Yellow

# Create WScript Shell object
$WshShell = New-Object -ComObject WScript.Shell

# Create shortcut
$Shortcut = $WshShell.CreateShortcut($shortcutPath)
$Shortcut.TargetPath = $targetPath
$Shortcut.WorkingDirectory = "C:\Users\B.LAPTOP"
$Shortcut.Description = "B.DEV CLI - Your Personal Development Assistant"
$Shortcut.Save()

Write-Host "[OK] Desktop shortcut created!" -ForegroundColor Green
Write-Host ""
Write-Host "Double-click 'B.DEV CLI' on your desktop to launch B.DEV" -ForegroundColor Yellow
