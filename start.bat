@echo off
cd /d "%~dp0"

REM Find python: prefer "python", fallback to "py" launcher
set "PYCMD="
where python >nul 2>nul && set "PYCMD=python"
if not defined PYCMD (
    where py >nul 2>nul && set "PYCMD=py"
)

if not defined PYCMD (
    echo.
    echo [ERROR] Python not found in PATH.
    echo.
    echo Please install Python 3.10+ from https://www.python.org/downloads/
    echo During install, CHECK "Add Python to PATH" (important^).
    echo.
    echo Or if already installed, add Python to PATH manually.
    echo.
    pause
    exit /b 1
)

echo [INFO] Using Python: %PYCMD%

REM Create venv if missing
if not exist "venv\Scripts\activate.bat" (
    echo [SETUP] Creating virtual environment...
    %PYCMD% -m venv venv
    if errorlevel 1 (
        echo [ERROR] Failed to create venv.
        pause
        exit /b 1
    )
)

call venv\Scripts\activate.bat

REM Install deps if flask missing (fast proxy check)
python -c "import flask" 2>nul
if errorlevel 1 (
    echo [SETUP] Installing dependencies...
    pip install -r requirements.txt
    if errorlevel 1 (
        echo [ERROR] Failed to install dependencies.
        pause
        exit /b 1
    )
)

REM Ensure data dirs
if not exist data mkdir data
if not exist data\resumes mkdir data\resumes

echo.
echo ============================================
echo  JHTracker running at http://127.0.0.1:5000
echo  Press Ctrl+C to stop. Browser opens in 2s.
echo ============================================
echo.

REM Open browser after 2s, then start server
start "" cmd /c "timeout /t 2 >nul && start http://127.0.0.1:5000"

python app.py
pause
