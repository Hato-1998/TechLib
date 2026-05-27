@echo off
REM TechLib 페이지 추가 도구 런처
REM 바탕화면 바로가기에서 이 파일을 호출.

chcp 65001 >nul
title TechLib 페이지 추가 도구

cd /d "%~dp0.."

python tools\add_page.py
set EXITCODE=%ERRORLEVEL%

echo.
echo ============================================
if %EXITCODE% EQU 0 (
    echo  완료. 아무 키나 누르면 창이 닫힙니다.
) else (
    echo  오류 코드 %EXITCODE%. 메시지를 확인 후 닫으세요.
)
echo ============================================
pause >nul
