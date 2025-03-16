from fastapi import APIRouter
from app.api import users, characters, auth, stories, generations, images

api_router = APIRouter()
api_router.include_router(auth.router, prefix="/auth")
api_router.include_router(users.router, prefix="/users")
api_router.include_router(characters.router, prefix="/characters")
api_router.include_router(stories.router, prefix="/stories")
api_router.include_router(generations.router, prefix="/generations")
api_router.include_router(images.router, prefix="/images") 