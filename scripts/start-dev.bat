@echo off
@rem Ensure UTF-8 code page
chcp 65001 >nul 2>&1

setlocal enabledelayedexpansion

echo =======================================================
echo     JHTracker AI Job Hunter - Developer Start (Full Build)
echo =======================================================
echo.

set "SCRIPT_DIR=%~dp0"
for %%I in ("%SCRIPT_DIR%..") do set "ROOT_DIR=%%~fI"

cd /d "%ROOT_DIR%"

echo [1/3] Full rebuilding frontend assets (tsc ^&^& vite build)...
cd /d "%ROOT_DIR%\frontend"
call npm run build
if %ERRORLEVEL% neq 0 (
    echo [ERROR] Frontend build failed with error code %ERRORLEVEL%.
    pause
    exit /b %ERRORLEVEL%
)
cd /d "%ROOT_DIR%"

echo [2/3] Setting up environment...
set "PYTHONPATH=%ROOT_DIR%\backend;%PYTHONPATH%"

echo [3/3] Starting JHTracker server on http://localhost:8000 ...
echo -------------------------------------------------------
echo Web UI:  http://localhost:8000
echo API Doc: http://localhost:8000/docs
echo Dev Tip: For instant HMR UI dev, run 'npm run dev' in frontend/
echo Press Ctrl + C to stop the service.
echo -------------------------------------------------------
echo.

start "" "http://localhost:8000"

python "%ROOT_DIR%\backend\src\main.py"

if %ERRORLEVEL% neq 0 (
    echo.
    echo Server exited with error code %ERRORLEVEL%.
    pause
)
