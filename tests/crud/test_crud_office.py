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

    assert db_office is not None
    assert db_office.name == office_in.name
    assert db_office.office_type == office_in.office_type
    assert db_office.created_by == owner.id

    created_office = await db_session.get(Office, db_office.id)
    assert created_office is not None

    # OfficeStaff（中間テーブル）レコードが作成されたか検証
    stmt = (
        select(Office)
        .where(Office.id == db_office.id)
        .options(selectinload(Office.staff_associations))
    )
    result = await db_session.execute(stmt)
    office_from_db = result.scalar_one_or_none()

    # OfficeがDBに存在し、関連(staff_associations)が1件存在することを確認
    assert office_from_db is not None
    assert len(office_from_db.staff_associations) == 1

    # 関連レコード(OfficeStaff)の内容を検証
    association_from_db = office_from_db.staff_associations[0]
    assert association_from_db.staff_id == owner.id
    assert association_from_db.is_primary is True
