@echo off
chcp 65001 >nul 2>&1
title Arboris Novel - Frontend

echo.
echo ============================================================
echo            Arboris Novel - Frontend
echo ============================================================
echo   URL: http://localhost:5173
echo   Close this window to stop the service
echo ============================================================
echo.

:: Get script directory
set "ROOT_DIR=%~dp0"
if "%ROOT_DIR:~-1%"=="\" set "ROOT_DIR=%ROOT_DIR:~0,-1%"

:: Check frontend directory
if not exist "%ROOT_DIR%\frontend" (
    echo [ERROR] Frontend directory not found: %ROOT_DIR%\frontend
    goto :error
)

:: Change to frontend directory
cd /d "%ROOT_DIR%\frontend"
if errorlevel 1 (
    echo [ERROR] Cannot change to frontend directory
    goto :error
)

:: Check node_modules
if not exist "node_modules" (
    echo [WARN] node_modules not found, installing dependencies...
    call npm install
    if errorlevel 1 (
        echo [ERROR] npm install failed
        goto :error
    )
)

echo Starting frontend service...
echo.

call npm run dev
if errorlevel 1 (
    echo.
    echo [ERROR] Frontend service exited abnormally
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
