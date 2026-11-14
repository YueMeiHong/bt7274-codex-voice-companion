@echo off
cd /d "%~dp0"
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0Stop-BT.ps1"
if errorlevel 1 (
  echo Stop failed. Please check the message above.
) else (
  echo Done. BT background services are stopped.
)
pause
