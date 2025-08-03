from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.api import deps
from app.crud.crud_office import crud_office
from app.models import Staff
from app.schemas.office import OfficeCreate, OfficeResponse

router = APIRouter()


@router.post("/setup", response_model=OfficeResponse)
async def setup_office(
    *,
    db: AsyncSession = Depends(deps.get_db),
    office_in: OfficeCreate,
    current_user: Staff = Depends(deps.get_current_active_user),
) -> Any:
    """
    事業所を新規作成し、作成したユーザーを事業所に所属させる
    """
    # 依存性注入で渡されたユーザーは別セッションの可能性があるため、現在のセッションにマージする
    user_in_db = await db.merge(current_user)
    # 必要なリレーションを明示的に読み込む
    await db.refresh(user_in_db, attribute_names=["office_associations"])

    # ユーザーが既に事業所に所属しているか確認
    if user_in_db.office_associations:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="ユーザーは既に事業所に所属しています。",
        )

    office = await crud_office.create_with_owner(
        db=db, obj_in=office_in, user=user_in_db
    )
    return office
