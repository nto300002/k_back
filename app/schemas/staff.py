from typing import Optional 
from datetime import datetime
from uuid import UUID
from pydantic import BaseModel, EmailStr
from app.models.enums import StaffRole, BillingStatus

class StaffCreate(BaseModel):
    id: UUID
    name: str
    email: EmailStr
    role: StaffRole
    is_active: bool
    created_at: datetime
    updated_at: datetime

class StaffUpdate(BaseModel):
    name: Optional[str] = None
    email: Optional[EmailStr] = None
    role: Optional[StaffRole] = None
    is_active: Optional[bool] = None

class StaffResponse(BaseModel):
    id: UUID
    name: str
    email: EmailStr
    role: StaffRole
    is_active: bool
    created_at: datetime
    updated_at: datetime

class LoginRequest(BaseModel):
    email: EmailStr
    password: str

class AdminSignupRequest(BaseModel):
    name: str
    email: EmailStr
    password: str

class StaffInviteRequest(BaseModel):
    email: EmailStr
    role: StaffRole


    