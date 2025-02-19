# app/main.py

"""
Minimal FastAPI application entry point.
"""

from fastapi import FastAPI
from app.database.seed import init_db

app = FastAPI()

@app.on_event("startup")
async def startup_event():
    init_db()

@app.get("/")
async def read_root():
    return {"message": "Welcome to the MVP Child Book Generator API"}
