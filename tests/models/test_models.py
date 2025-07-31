import pytest
from datetime import datetime
from sqlalchemy import select # selectをインポート
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

# --- テスト対象のモデルとEnum ---
from app.models import Staff, Office, OfficeStaff
from app.models.enums import StaffRole, OfficeType

from tests.conftest import service_admin_user_factory, office_factory

# このファイル内のすべてのテストを非同期テストとしてマークする
pytestmark = pytest.mark.asyncio


async def test_create_staff_in_db(
    db_session: AsyncSession, 
    service_admin_user_factory
):
    """
    インテグレーションテスト: service_admin_user_factoryを使い、DBにStaffレコードが正しく作成されるか。
    DBのデフォルト値(created_at)も検証する。
    """
    # 1. ファクトリを使ってDBにテストユーザーを作成
    staff_member = await service_admin_user_factory(
        name="DBテストスタッフ",
        role=StaffRole.employee
    )

    # 2. DBから直接データを取得して検証
    retrieved_staff = await db_session.get(Staff, staff_member.id)
    
    assert retrieved_staff is not None
    assert retrieved_staff.id == staff_member.id
    assert retrieved_staff.name == "DBテストスタッフ"
    assert retrieved_staff.role == StaffRole.employee
    # DBに保存されたので、datetime型になっているはず
    assert isinstance(retrieved_staff.created_at, datetime)
    assert isinstance(retrieved_staff.updated_at, datetime)

async def test_create_office_in_db(
    db_session: AsyncSession,
    office_factory,
    service_admin_user_factory
):
    """
    インテグレーションテスト: office_factoryを使い、DBにOfficeレコードが正しく作成されるか。
    """
    # 1. ファクトリを使ってDBにテスト事業所を作成
    staff_member = await service_admin_user_factory(
        name="DBテストスタッフ",
        role=StaffRole.employee
    )

    office_instance = await office_factory(
        name="DBテスト事業所",
        office_type=OfficeType.type_A_office,
        created_by=staff_member.id,
        last_modified_by=staff_member.id
    )

    # 2. DBから直接データを取得して検証
    retrieved_office = await db_session.get(Office, office_instance.id)

    assert retrieved_office is not None
    assert retrieved_office.id == office_instance.id
    assert retrieved_office.name == "DBテスト事業所"
    assert retrieved_office.office_type == OfficeType.type_A_office
    assert isinstance(retrieved_office.created_at, datetime)


async def test_create_office_staff_association_in_db(
    db_session: AsyncSession,
    service_admin_user_factory,
    office_factory
):
    """
    インテグレーションテスト: StaffとOfficeを関連付け、
    中間テーブル(OfficeStaff)とリレーションシップが正しく機能するか。
    """

    # 1. テスト用のStaffとOfficeをDBに作成
    staff_member = await service_admin_user_factory(
        name="DBテストスタッフ",
        role=StaffRole.employee
    )
    office_instance = await office_factory(
        name="DBテスト事業所",
        office_type=OfficeType.type_A_office,
        created_by=staff_member.id,
        last_modified_by=staff_member.id
    )

    # 2. 中間テーブルのオブジェクトを直接作成し、DBにflush
    association = OfficeStaff(staff_id=staff_member.id, office_id=office_instance.id)
    db_session.add(association)
    await db_session.flush()


    # 3. select()文を使い、Eager Loadingを確実に実行する
    #    これがドキュメントに沿った最も確実な方法
    stmt_staff = select(Staff).where(Staff.id == staff_member.id).options(selectinload(Staff.offices))
    result_staff = await db_session.execute(stmt_staff)
    reloaded_staff = result_staff.scalar_one()

    stmt_office = select(Office).where(Office.id == office_instance.id).options(selectinload(Office.staffs))
    result_office = await db_session.execute(stmt_office)
    reloaded_office = result_office.scalar_one()
    
    print("[DEBUG] Re-fetch with select() and selectinload completed.")

    # 4. 再取得したオブジェクトでリレーションシップを検証
    assert reloaded_office in reloaded_staff.offices
    assert reloaded_staff in reloaded_office.staffs
    print("[DEBUG] Relationship assertions passed.")

    # 5. 中間テーブルのレコードを直接確認
    retrieved_association = await db_session.get(OfficeStaff, association.id)
    assert retrieved_association is not None
    assert retrieved_association.staff_id == staff_member.id
    assert retrieved_association.office_id == office_instance.id
    print("[DEBUG] Direct association assertion passed.")
