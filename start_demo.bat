@echo off
setlocal
cd /d "%~dp0"

echo [Creative Workshop] Checking virtual environment...
if not exist ".venv\Scripts\python.exe" (
  python -m venv .venv
)

call ".venv\Scripts\activate.bat"

echo [Creative Workshop] Checking MySQL driver...
python -c "import pymysql" >nul 2>nul
if errorlevel 1 (
  echo [Creative Workshop] Installing PyMySQL...
  python -m pip install PyMySQL==1.1.1
  if errorlevel 1 (
    echo [Creative Workshop] Failed to install PyMySQL. Please run: python -m pip install PyMySQL==1.1.1
    pause
    exit /b 1
  )
)

echo [Creative Workshop] Initializing database...
python scripts\init_db.py
if errorlevel 1 (
  echo [Creative Workshop] Database init failed. Check .env DATABASE_URL and MySQL service.
  pause
  exit /b 1
)

echo.
echo [Creative Workshop] Starting server...
echo Open http://127.0.0.1:8000
echo Press Ctrl+C to stop.
echo.
python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
