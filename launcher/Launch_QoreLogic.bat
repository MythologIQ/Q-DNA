@echo off
title QoreLogic Launcher
echo Starting QoreLogic System...
cd /d "%~dp0"
powershell -NoProfile -ExecutionPolicy Bypass -File server.ps1
pause
