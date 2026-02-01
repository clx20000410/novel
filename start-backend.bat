@echo off
chcp 65001 >nul 2>&1
title Arboris Novel - Backend

echo.
echo ============================================================
echo            Arboris Novel - Backend
echo ============================================================
echo   API:  http://localhost:8000
echo   Docs: http://localhost:8000/docs
echo   Close this window to stop the service
echo ============================================================
echo.

:: Get script directory
set "ROOT_DIR=%~dp0"
if "%ROOT_DIR:~-1%"=="\" set "ROOT_DIR=%ROOT_DIR:~0,-1%"

:: Check backend directory
if not exist "%ROOT_DIR%\backend" (
    echo [ERROR] Backend directory not found: %ROOT_DIR%\backend
    goto :error
)

:: Change to backend directory
cd /d "%ROOT_DIR%\backend"
if errorlevel 1 (
    echo [ERROR] Cannot change to backend directory
    goto :error
)

:: Check virtual environment
if not exist ".venv\Scripts\python.exe" (
    echo [ERROR] Python venv not found: .venv\Scripts\python.exe
    echo [TIP] Run: python -m venv .venv
    goto :error
)

echo Starting backend service...
echo.

.venv\Scripts\python.exe -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
if errorlevel 1 (
    echo.
    echo [ERROR] Backend service exited abnormally
    goto :error
)

goto :end

:error
echo.
echo ============================================================
echo   Error occurred! Check the messages above.
echo ============================================================
pause
exit /b 1

:end
pause
