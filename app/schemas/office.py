from uuid import UUID
from datetime import datetime
from pydantic import BaseModel
from app.models.enums import OfficeType, BillingStatus

class OfficeCreate(BaseModel):
    name: str
    office_type: OfficeType

class OfficeResponse(BaseModel):
    id: UUID
    name: str
    office_type: OfficeType
    billing_status: BillingStatus
    created_at: datetime
    updated_at: datetime


class OfficeWithStaffResponse(OfficeResponse):
    staff: list = []

class OfficeStaffAssociation(BaseModel):
    staff_id: UUID
    office_id: UUID
    is_primary: bool

