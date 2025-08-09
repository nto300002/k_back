import pytest
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from app.crud import crud_office
from app.schemas.office import OfficeCreate
from app.models.office import Office, OfficeStaff
from app.models.enums import OfficeType, StaffRole
import logging

@pytest.mark.asyncio
async def test_create_office_with_owner(db_session: AsyncSession, service_admin_user_factory):
    """
    正常系: create_with_ownerがOfficeとOfficeStaffのレコードを正しく作成するかテスト
    """
    owner = await service_admin_user_factory(name="テスト管理者", role=StaffRole.service_administrator)
    office_in = OfficeCreate(name="CRUDテスト事業所", office_type=OfficeType.type_A_office)

    db_office = await crud_office.create_with_owner(
        db=db_session, obj_in=office_in, user=owner
    )

    # 5. DBから作成されたレコードを再取得して検証
    await db_session.refresh(owner) # ownerオブジェクトのセッション状態を更新
    created_office = await db_session.get(Office, db_office.id)

    assert created_office is not None
    assert created_office.name == office_in.name
    assert created_office.office_type == office_in.office_type
    assert created_office.created_by == owner.id

    # 6. OfficeStaff（中間テーブル）レコードが作成されたか検証
    stmt = (
        select(OfficeStaff)
        .where(OfficeStaff.office_id == created_office.id)
        .where(OfficeStaff.staff_id == owner.id)
    )
    result = await db_session.execute(stmt)
    association_from_db = result.scalar_one_or_none()

    assert association_from_db is not None
    assert association_from_db.is_primary is True
