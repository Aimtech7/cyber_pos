@echo off
echo Starting CyberCafe POS...

REM Start Backend
echo Starting Backend...
start "POS Backend" cmd /k "cd backend && venv\Scripts\activate && uvicorn app.main:app --reload --host 127.0.0.1 --port 8000"

REM Start Frontend
echo Starting Frontend...
start "POS Frontend" cmd /k "cd frontend && npm run dev"

echo.
echo Services started!
echo Backend: http://127.0.0.1:8000/docs
echo Frontend: http://localhost:5173
echo.
pause
