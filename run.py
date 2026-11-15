#!/usr/bin/env python3
"""
NutriLens Unified Server Runner
Starts the FastAPI backend and serves the React frontend at http://127.0.0.1:8000
"""
import os
import sys

# Ensure backend directory is in Python path
ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
BACKEND_DIR = os.path.join(ROOT_DIR, "backend")
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

import uvicorn

if __name__ == "__main__":
    print("\n🌿 Starting NutriLens Server...")
    print("📍 Web Interface: http://localhost:8000")
    print("📚 API Documentation: http://localhost:8000/docs\n")
    uvicorn.run("app.main:app", host="127.0.0.1", port=8000, reload=True)

