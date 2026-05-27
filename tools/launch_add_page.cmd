@echo off
REM TechLib page-add launcher. Launched by the desktop shortcut.
REM All comments/messages kept in ASCII so cmd parses correctly regardless of
REM file encoding. Korean output from the Python script works because we set
REM chcp 65001 + PYTHONIOENCODING below.

chcp 65001 >nul
set PYTHONIOENCODING=utf-8
title TechLib Page Adder

cd /d "%~dp0.."

python tools\add_page.py
set EXITCODE=%ERRORLEVEL%

echo.
echo ============================================
if "%EXITCODE%"=="0" (
    echo  Done. Press any key to close.
) else (
    echo  Exit code %EXITCODE%. Check messages, then press any key.
)
echo ============================================
pause >nul
