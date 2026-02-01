@echo off
chcp 65001 >nul 2>&1
title Arboris Novel

echo.
echo ╔════════════════════════════════════════════════════════════╗
echo ║            Arboris Novel - 一键启动脚本                    ║
echo ╠════════════════════════════════════════════════════════════╣
echo ║  前端: http://localhost:5173                               ║
echo ║  后端: http://localhost:8000                               ║
echo ║  文档: http://localhost:8000/docs                          ║
echo ╠════════════════════════════════════════════════════════════╣
echo ║  提示: 关闭此窗口将自动停止所有服务                        ║
echo ╚════════════════════════════════════════════════════════════╝
echo.

:: 获取脚本目录（去除末尾反斜杠）
set "ROOT_DIR=%~dp0"
if "%ROOT_DIR:~-1%"=="\" set "ROOT_DIR=%ROOT_DIR:~0,-1%"

:: 后台启动后端服务
echo [1/2] 启动后端服务...
start "" /B cmd /c "cd /d %ROOT_DIR%\backend && .venv\Scripts\python.exe -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000"

:: 等待后端启动
timeout /t 2 /nobreak >nul

:: 前台启动前端服务（阻塞主进程）
echo [2/2] 启动前端服务...
echo.
echo ════════════════════════════════════════════════════════════════
echo   服务已启动！按 Ctrl+C 或关闭窗口即可停止所有服务
echo ════════════════════════════════════════════════════════════════
echo.

cd /d "%ROOT_DIR%frontend"
call npm run dev
