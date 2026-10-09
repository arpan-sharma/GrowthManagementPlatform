from fastapi import APIRouter

from app.api.v1.institutions.auth import router as auth_router
from app.api.v1.institutions.resources import router as resources_router

institutions_router = APIRouter()
institutions_router.include_router(auth_router)
institutions_router.include_router(resources_router)
