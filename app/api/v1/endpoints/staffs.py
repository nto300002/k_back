from typing import Any

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.api import deps
from app.crud.crud_office import crud_office
from app.models import Staff

router = APIRouter()


@router.get("/me")
async def get_staff_me(
    *,
    db: AsyncSession = Depends(deps.get_db),
    current_user: Staff = Depends(deps.get_current_active_user),
) -> Any:
    """
    現在のスタッフ情報と所属事業所情報を取得する
    """
    user_in_db = await db.merge(current_user)
    await db.refresh(user_in_db, attribute_names=["office_associations"])

    offices = await crud_office.get_offices_by_staff(db=db, staff_id=user_in_db.id)
    
    office_data = []
    for office in offices:
        office_data.append({
            "name": office.name,
            "office_type": office.office_type.value,
        })

    return {
        "id": str(user_in_db.id),
        "name": user_in_db.name,
        "role": user_in_db.role.value,
        "offices": office_data,
    }