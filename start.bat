@echo off
title Alpha Station v4.0
color 0A

echo.
echo  ╔═══════════════════════════════════════════════════════╗
echo  ║         ALPHA STATION v4.0 — STARTUP SEQUENCE        ║
echo  ║     Exponential Growth Detection Engine               ║
echo  ╚═══════════════════════════════════════════════════════╝
echo.

:: ── Install backend dependencies ──────────────────────────────────────────
echo [1/4] Installing backend dependencies...
cd /d "%~dp0backend"
py -m pip install -r requirements.txt -q
if errorlevel 1 (
    echo  ERROR: Backend pip install failed
    pause & exit /b 1
)
echo  OK

:: ── Start FastAPI backend ─────────────────────────────────────────────────
echo [2/4] Starting FastAPI backend on port 8000...
start "Alpha Station Backend" cmd /k "cd /d %~dp0backend && py -m uvicorn main:app --reload --port 8000 --host 0.0.0.0"
timeout /t 3 /nobreak >nul
echo  OK → http://localhost:8000

:: ── Install frontend dependencies ─────────────────────────────────────────
echo [3/4] Installing frontend dependencies...
cd /d "%~dp0frontend"
call npm install --silent
if errorlevel 1 (
    echo  ERROR: npm install failed
    pause & exit /b 1
)
echo  OK

:: ── Start Next.js frontend ────────────────────────────────────────────────
echo [4/4] Starting Next.js frontend on port 3000...
start "Alpha Station Frontend" cmd /k "cd /d %~dp0frontend && npm run dev -- -H 0.0.0.0"
timeout /t 4 /nobreak >nul
echo  OK → http://localhost:3000

echo.
echo  ╔═══════════════════════════════════════════════════════╗
echo  ║  ALPHA STATION v4.0 ONLINE                           ║
echo  ║                                                       ║
echo  ║  Frontend:  http://localhost:3000                     ║
echo  ║  API Docs:  http://localhost:8000/docs                ║
echo  ║  Health:    http://localhost:8000/health              ║
echo  ╚═══════════════════════════════════════════════════════╝
echo.

:: Open browser
start "" "http://localhost:3000"

pause
