# app/main.py

"""
Main FastAPI application entry point.
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.auth import router as auth_router
from app.api.users import router as users_router
from app.database.seed import init_db

app = FastAPI()

# Include routers
app.include_router(auth_router)
app.include_router(users_router)

# Configure CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # Adjust based on your frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan event handler to perform startup and shutdown tasks.
    """
    init_db()  # Startup task
    yield
    # Perform any necessary cleanup here


app.router.lifespan_context = lifespan


@app.get("/")
def read_root():
    """
    Root endpoint returning a welcome message.
    """
    return {"message": "Welcome to the MVP Child Book Generator API"}
