#!/bin/bash
# Quick script to run FastAPI backend for Recommendation System
# Usage: bash run.sh

echo ""
echo "============================================================"
echo "  🚀 Starting Recommendation System API Server"
echo "============================================================"
echo "  🌐 API URL: http://localhost:8000"
echo "  📚 API Docs: http://localhost:8000/docs"
echo "  📖 ReDoc: http://localhost:8000/redoc"
echo "============================================================"
echo ""
echo "Press Ctrl+C to stop the server"
echo ""

cd "$(dirname "$0")/backend"
python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000
