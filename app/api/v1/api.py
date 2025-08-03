from fastapi import APIRouter
from .endpoints import office # auth, staff, 

api_router = APIRouter()
# api_router.include_router(auth.router, prefix="/auth", tags=["Auth"])
# api_router.include_router(staff.router, prefix="/staff", tags=["Staff"])
api_router.include_router(office.router, prefix="/office", tags=["Offices"])  