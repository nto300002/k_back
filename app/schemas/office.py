from uuid import UUID
from datetime import datetime
from pydantic import BaseModel
from app.models.enums import OfficeType, BillingStatus

class OfficeCreateRequest(BaseModel):
    name: str
    office_type: OfficeType

class OfficeResponse(BaseModel):
    id: UUID
    name: str
    office_type: OfficeType
    billing_status: BillingStatus
    is_active: bool
    created_at: datetime
    updated_at: datetime