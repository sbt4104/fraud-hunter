#!/usr/bin/env python3
"""
Main entry point for the Fraud Detection System
"""
from dotenv import load_dotenv

# Load environment variables FIRST
load_dotenv()

import uvicorn
from app.main import app

if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )