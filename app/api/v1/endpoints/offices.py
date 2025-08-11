from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.api import deps
from app.crud.crud_office import crud_office
from app.models import Staff, StaffRole
from app.schemas.office import OfficeCreate, OfficeResponse
from app.schemas.staff import StaffResponse

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
    if current_user.role != StaffRole.service_administrator:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="この操作を行う権限がありません。",
        )
    # 外部から渡されたcurrent_userをそのまま使わず、IDを使ってDBから再取得する
    user_in_db = await db.get(Staff, current_user.id)
    if not user_in_db:
        # 通常、get_current_active_userが有効なユーザーを返すため、このケースは稀
        raise HTTPException(status_code=404, detail="User not found")

    await db.refresh(user_in_db, attribute_names=["office_associations"])

    if user_in_db.office_associations:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="ユーザーは既に事業所に所属しています。",
        )

    try:
        office = await crud_office.create_with_owner(
            db=db, obj_in=office_in, user=user_in_db
        )
    except IntegrityError as e:
        await db.rollback()
        if 'duplicate key value violates unique constraint "offices_name_key"' in str(e.orig):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="すでにその名前の事務所は登録されています。",
            )
        # 他のIntegrityErrorの場合は、より一般的なエラーメッセージを返す
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"データベースの整合性エラーが発生しました: {e.orig}",
        )

    return office