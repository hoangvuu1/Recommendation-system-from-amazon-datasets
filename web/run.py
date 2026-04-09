#!/usr/bin/env python3
"""
Quick script to run FastAPI backend for Recommendation System
Usage: python run.py
"""

import subprocess
import sys
import os
from pathlib import Path

def main():
    backend_dir = Path(__file__).parent / "backend"
    os.chdir(backend_dir)
    
    print("=" * 60)
    print(" Starting Recommendation System API Server")
    print("=" * 60)
    print(f" Backend directory: {backend_dir}")
    print(f" API URL: http://localhost:8000")
    print(f" API Docs: http://localhost:8000/docs")
    print(f" ReDoc: http://localhost:8000/redoc")
    print("=" * 60)
    print()
    print("Press Ctrl+C to stop the server")
    print()
    
    # Run uvicorn
    subprocess.run(
        [sys.executable, "-m", "uvicorn", "main:app", "--reload", "--host", "0.0.0.0", "--port", "8000"],
        cwd=backend_dir
    )

if __name__ == "__main__":
    main()
