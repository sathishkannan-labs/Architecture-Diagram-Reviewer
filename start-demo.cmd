@echo off
powershell -NoProfile -File "%~dp0start-demo.ps1" %*
if errorlevel 1 pause
