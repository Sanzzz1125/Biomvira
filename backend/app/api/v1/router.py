from fastapi import APIRouter
from app.api.v1.extract import router as extract_router
from app.api.v1.recommend import router as recommend_router
from app.api.v1.history import router as history_router
from app.api.v1.auth import router as auth_router
from app.api.v1.admin import router as admin_router
from app.api.v1.chat import router as chat_router

api_router = APIRouter()
api_router.include_router(auth_router, tags=["Auth"])
api_router.include_router(extract_router, tags=["Extraction"])
api_router.include_router(recommend_router, tags=["Recommendation"])
api_router.include_router(history_router, tags=["History"])
api_router.include_router(admin_router, tags=["Admin"])
api_router.include_router(chat_router, tags=["Assistant"])
