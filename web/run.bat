@echo off
REM Quick script to run FastAPI backend for Recommendation System
REM Usage: run.bat

echo.
echo ============================================================
echo   Starting Recommendation System API Server
echo ============================================================
echo   API URL: http://localhost:8000
echo   API Docs: http://localhost:8000/docs
echo   ReDoc: http://localhost:8000/redoc
echo ============================================================
echo.

cd backend
python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000

pause
