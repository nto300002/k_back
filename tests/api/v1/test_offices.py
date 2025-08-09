import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from fastapi import status
from fastapi.encoders import jsonable_encoder
from unittest.mock import patch, AsyncMock
from sqlalchemy.exc import IntegrityError
from uuid import uuid4

from app.core.config import settings
from app.models.staff import Staff
from app.models.office import Office, OfficeStaff
from app.schemas.office import OfficeCreate
from app.models.enums import OfficeType, StaffRole
from app.api.deps import get_current_active_user, get_db
from app.main import app

# --- 正常系テスト ---

@pytest.mark.asyncio
async def test_setup_office_success(
    async_client: AsyncClient,
    db_session: AsyncSession,
    service_admin_user_factory,
):
    """
    正常系: service_administratorロールのユーザーが事業所を正常に作成できる
    """
    user: Staff = await service_admin_user_factory(
        name="テスト管理者",
        role=StaffRole.service_administrator,
    )
    # DBセッションをフラッシュして、ユーザーをDBに永続化する（コミットはしない）
    await db_session.flush()
    
    office_data = OfficeCreate(
        name="テスト事業所",
        office_type=OfficeType.type_A_office,
    )
    app.dependency_overrides[get_current_active_user] = lambda: user
    try:
        response = await async_client.post(
            f"{settings.API_V1_STR}/offices/setup",
            json=jsonable_encoder(office_data),
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["name"] == office_data.name
        office_id = data["id"]
        await db_session.refresh(user)
        db_office = await db_session.get(Office, office_id)
        assert db_office is not None
        stmt = select(OfficeStaff).where(OfficeStaff.staff_id == user.id, OfficeStaff.office_id == office_id)
        result = await db_session.execute(stmt)
        association = result.scalar_one_or_none()
        assert association is not None
    finally:
        app.dependency_overrides.clear()

# --- 異常系テスト ---

@pytest.mark.asyncio
async def test_setup_office_fail_when_already_associated(
    async_client: AsyncClient,
    db_session: AsyncSession,
    service_admin_user_factory,
    office_factory,
):
    """
    異常系: 既に事業所に所属しているユーザーは新しい事業所を作成できない
    """
    test_user: Staff = await service_admin_user_factory(
        name="既存所属管理者",
        role=StaffRole.service_administrator,
    )
    existing_office: Office = await office_factory(
        name="既存の事業所",
        created_by=test_user.id,
        last_modified_by=test_user.id,
        office_type=OfficeType.type_A_office,
    )
    association = OfficeStaff(staff_id=test_user.id, office_id=existing_office.id)
    db_session.add(association)
    await db_session.commit()
    await db_session.refresh(test_user)
    new_office_data = OfficeCreate(
        name="作成しようとする新しい事業所",
        office_type=OfficeType.type_B_office,
    )
    app.dependency_overrides[get_current_active_user] = lambda: test_user
    try:
        response = await async_client.post(
            f"{settings.API_V1_STR}/offices/setup",
            json=jsonable_encoder(new_office_data),
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.json()["detail"] == "ユーザーは既に事業所に所属しています。"
    finally:
        app.dependency_overrides.clear()

@pytest.mark.asyncio
@patch("app.api.v1.endpoints.offices.crud_office.create_with_owner", new_callable=AsyncMock)
async def test_setup_office_fail_with_duplicate_name(
    mock_create_with_owner: AsyncMock,
    async_client: AsyncClient,
    service_admin_user_factory,
    db_session: AsyncSession,
):
    """
    異常系: 既に存在する名前で事業所を作成しようとすると409エラー
    """
    user: Staff = await service_admin_user_factory(
        session=db_session, name="テスト管理者", role=StaffRole.service_administrator
    )
    await db_session.flush()

    # 正しいIntegrityErrorを生成
    error = IntegrityError(None, None, 'duplicate key value violates unique constraint "offices_name_key"')
    mock_create_with_owner.side_effect = error

    office_data = OfficeCreate(
        name="重複する名前の事業所",
        office_type=OfficeType.type_A_office,
    )
    app.dependency_overrides[get_current_active_user] = lambda: user
    try:
        response = await async_client.post(
            f"{settings.API_V1_STR}/offices/setup",
            json=jsonable_encoder(office_data),
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == status.HTTP_409_CONFLICT
    assert "すでにその名前の事務所は登録されています" in response.json()["detail"]
    mock_create_with_owner.assert_awaited_once()

@pytest.mark.asyncio
@patch("app.api.v1.endpoints.offices.crud_office.create_with_owner", new_callable=AsyncMock)
async def test_setup_office_fail_with_duplicate_name_mocked(
    mock_create_with_owner: AsyncMock,
    async_client: AsyncClient,
):
    """
    【モックテスト】異常系: サービス層で重複エラー(IntegrityError)が発生した場合、
    APIが409 Conflictを返すことを確認する
    """
    dummy_user = Staff(id=uuid4(), name="ダミーユーザー", role=StaffRole.service_administrator)
    
    mock_session = AsyncMock(spec=AsyncSession)
    mock_session.get.return_value = dummy_user
    mock_session.refresh.return_value = None
    mock_session.rollback.return_value = None

    async def override_get_db():
        yield mock_session

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_current_active_user] = lambda: dummy_user

    # 正しいIntegrityErrorを生成
    error = IntegrityError(None, None, 'duplicate key value violates unique constraint "offices_name_key"')
    mock_create_with_owner.side_effect = error

    office_data = OfficeCreate(
        name="重複する名前の事業所",
        office_type=OfficeType.type_A_office,
    )
    try:
        response = await async_client.post(
            f"{settings.API_V1_STR}/offices/setup",
            json=jsonable_encoder(office_data),
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == status.HTTP_409_CONFLICT
    assert "すでにその名前の事務所は登録されています" in response.json()["detail"]
    mock_session.get.assert_awaited_once_with(Staff, dummy_user.id)
    mock_create_with_owner.assert_awaited_once()

@pytest.mark.asyncio
async def test_setup_office_fail_with_invalid_user_role(
    async_client: AsyncClient,
    general_user,
):
    """
    異常系: general_userロールのユーザーは事業所を作成できず、403エラー
    """
    office_data = OfficeCreate(
        name="権限のないユーザーが作成する事業所",
        office_type=OfficeType.type_A_office,
    )
    app.dependency_overrides[get_current_active_user] = lambda: general_user
    try:
        response = await async_client.post(
            f"{settings.API_V1_STR}/offices/setup",
            json=jsonable_encoder(office_data),
        )
        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert response.json()["detail"] == "この操作を行う権限がありません。"
    finally:
        app.dependency_overrides.clear()