#!/usr/bin/env python
"""
Run the FastAPI recommendation system server
"""
import uvicorn
import sys
from pathlib import Path

if __name__ == "__main__":
    # Ensure we're in the right directory
    web_dir = Path(__file__).parent
    sys.path.insert(0, str(web_dir))
    
    print(f" Starting Recommendation System API Server")
    print(f" Working directory: {web_dir}")
    print(f" Access: http://localhost:8080")
    print(f" API Docs: http://localhost:8080/docs")
    print(f" Press CTRL+C to stop\n")
    
    uvicorn.run(
        "backend.main:app",
        host="127.0.0.1",
        port=8080,
        reload=True,
        log_level="info"
    )
