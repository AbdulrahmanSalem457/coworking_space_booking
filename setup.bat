@echo off
setlocal
set PYTHONUNBUFFERED=1
title Coworking Booking Setup
cd /d "%~dp0"

echo ==========================================================
echo    COWORKING BOOKING - Backend Setup for Windows
echo ==========================================================
echo.

python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python was not found on PATH. Install Python 3.11+ from python.org and try again.
    pause
    exit /b 1
)
echo [OK] Python found

cd backend

if not exist venv (
    echo [1/5] Creating virtual environment...
    python -m venv venv
) else (
    echo [SKIP] Virtual environment already exists
)

echo [2/5] Installing dependencies...
call venv\Scripts\activate.bat
python -m pip install --disable-pip-version-check -q -r requirements.txt
if errorlevel 1 (
    echo [ERROR] Dependency installation failed. Scroll up for details.
    pause
    exit /b 1
)
echo [OK] Dependencies installed

if not exist .env (
    copy .env.example .env >nul
    echo [OK] Created .env from .env.example
)

echo [3/5] Applying database migrations...
python manage.py migrate --noinput

echo [4/5] Creating your admin account (if it doesn't exist yet)...
python manage.py ensure_admin
if errorlevel 1 (
    echo [ERROR] Set ADMIN_USERNAME, ADMIN_EMAIL and ADMIN_PASSWORD in backend\.env first.
    pause
    exit /b 1
)

echo [5/5] Starting servers...
start "Coworking Frontend" /min "%~dp0frontend\run_frontend.bat"

echo.
echo ==========================================================
echo    COWORKING BOOKING SERVER
echo ==========================================================
echo.
echo    API:          http://127.0.0.1:8000/api/
echo    Swagger UI:   http://127.0.0.1:8000/swagger/
echo    Redoc:        http://127.0.0.1:8000/redoc/
echo    Admin panel:  http://127.0.0.1:8000/admin/
echo    Frontend:     http://127.0.0.1:5500/index.html
echo.
echo    Log into /admin/ with the account configured in backend\.env
echo.
echo    Press Ctrl+C to stop the backend.
echo    (this also closes the frontend server window)
echo ==========================================================
echo.

set PYTHONUNBUFFERED=1
python manage.py runserver 8000 --noreload

taskkill /FI "WINDOWTITLE eq Coworking Frontend*" /T /F >nul 2>&1
