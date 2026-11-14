@echo off
setlocal
powershell.exe -NoLogo -NoProfile -ExecutionPolicy Bypass -File "%~dp0Start-Arcadia.ps1" %*
set "arcadia_exit=%ERRORLEVEL%"
if not "%arcadia_exit%"=="0" pause
exit /b %arcadia_exit%
