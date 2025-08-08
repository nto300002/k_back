from fastapi import APIRouter

from app.api.v1.endpoints import offices, staffs

api_router = APIRouter()

api_router.include_router(offices.router, prefix="/offices", tags=["offices"])
api_router.include_router(staffs.router, prefix="/staffs", tags=["staffs"])