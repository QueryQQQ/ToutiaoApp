@echo off
chcp 936 >nul
setlocal
title 头条资讯 - 开发环境

set "ROOT=D:\Projects\vscodeProjects\ToutiaoApp"
set "FRONT=%ROOT%\xwzx-news"

cd /d "%ROOT%"
if errorlevel 1 (
  echo [错误] 找不到项目目录: %ROOT%
  pause
  exit /b 1
)

echo ============================================
echo    头条资讯 - 一键开发环境
echo    后端  http://127.0.0.1:8000
echo    前端  http://localhost:5173
echo ============================================
echo.

rem ------------------- 后端 FastAPI -------------------
netstat -ano | findstr ":8000 " | findstr "LISTENING" >nul
if not errorlevel 1 (
  echo [后端] 8000 端口已在监听，跳过启动
) else (
  echo [后端] 正在启动 FastAPI ...
  start "后端 FastAPI :8000" cmd /k ".venv\Scripts\python.exe -m uvicorn main:app --reload --host 127.0.0.1 --port 8000"
)

ping -n 3 127.0.0.1 >nul

rem ------------------- 前端 Vite -------------------
netstat -ano | findstr ":5173 " | findstr "LISTENING" >nul
if not errorlevel 1 (
  echo [前端] 5173 端口已在监听，直接打开浏览器
  start "" http://localhost:5173
  echo.
  echo 前端已在另一个窗口运行，本窗口可以关闭。
  pause
  exit /b 0
)

cd /d "%FRONT%"
if errorlevel 1 (
  echo [错误] 找不到前端目录: %FRONT%
  pause
  exit /b 1
)

if not exist "node_modules" (
  echo [前端] 未检测到 node_modules，正在安装依赖 ...
  call npm install
  if errorlevel 1 (
    echo [错误] 依赖安装失败，请检查网络或手动执行 npm install
    pause
    exit /b 1
  )
)

echo [前端] 正在启动 Vite，就绪后会自动打开浏览器 ...
echo.
call npm run dev -- --open

echo.
echo 前端服务已停止。关闭本窗口即可。
pause
