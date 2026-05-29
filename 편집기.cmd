@echo off
REM TechLib Wiki Editor - root launcher (portable).
REM Resolves repo root from this file's own location (%~dp0),
REM so it works on any computer / any clone location.

chcp 65001 >nul
set PYTHONIOENCODING=utf-8
title TechLib Wiki Editor

cd /d "%~dp0"

echo Starting TechLib editor server...
echo Browser will open at http://127.0.0.1:7700/
echo Press Ctrl+C in this window to stop the server.
echo.

python tools\editor\server.py
set EXITCODE=%ERRORLEVEL%

echo.
echo ============================================
if "%EXITCODE%"=="0" (
    echo  Server stopped. Press any key to close.
) else (
    echo  Exit code %EXITCODE%. Check messages above.
)
echo ============================================
pause >nul
