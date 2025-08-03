import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from fastapi import status, HTTPException
from fastapi.encoders import jsonable_encoder

from app.core.config import settings
from app.models.staff import Staff
from app.models.office import Office, OfficeStaff
from app.schemas.office import OfficeCreate
from app.models.enums import OfficeType, StaffRole
from app.api.deps import get_current_active_user
from tests.conftest import service_admin_user_factory, office_factory
from app.main import app
from app.db.session import SessionLocal

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
    # 1. テスト用のユーザーを作成（まだ事業所には所属していない）
    user: Staff = await service_admin_user_factory(
        name="テスト管理者",
        role=StaffRole.service_administrator,
        
    )
    
    # 2. APIリクエストのペイロードを準備
    office_data = OfficeCreate(
        name="テスト事業所",
        office_type=OfficeType.type_A_office,
    )
    
    # 3. APIリクエストを実行
    def override_get_current_user():
        return user
    
    app.dependency_overrides[get_current_active_user] = override_get_current_user

    try:
        response = await async_client.post(
            f"{settings.API_V1_STR}/offices/setup",
            json=jsonable_encoder(office_data),
        )

        # 4. レスポンスを検証
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["name"] == office_data.name
        assert data["office_type"] == office_data.office_type.value
        assert "id" in data

        # 5. DBの状態を検証
        #    作成されたOfficeが存在するか
        office_id = data["id"]
        db_office = await db_session.get(Office, office_id)
        assert db_office is not None
        assert db_office.name == office_data.name
        assert db_office.created_by == user.id

        #    中間テーブルの関連付けが正しく行われたか
        result = await db_session.execute(
            select(OfficeStaff).filter_by(staff_id=user.id, office_id=office_id)
        )
        association = result.scalars().one_or_none()
        assert association is not None
        assert association.is_primary is True
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
    # 1. テスト用のユーザーと事業所を準備
    user_to_create: Staff = await service_admin_user_factory(
        name="既存所属管理者",
        role=StaffRole.service_administrator,
    )
    existing_office_to_create: Office = await office_factory(
        name="既存の事業所",
        office_type=OfficeType.type_A_office,
        created_by=user_to_create.id,
        last_modified_by=user_to_create.id,
    )

    # 2. 現在のセッションでオブジェクトをDBに追加
    db_session.add(user_to_create)
    db_session.add(existing_office_to_create)
    await db_session.flush() # IDを確定させる

    # 3. ユーザーと事業所を関連付ける
    association = OfficeStaff(staff_id=user_to_create.id, office_id=existing_office_to_create.id)
    db_session.add(association)
    user_id_for_override = user_to_create.id
    await db_session.commit() # ここでテストの初期状態を確定


    # 4. APIリクエストのペイロードを準備
    new_office_data = OfficeCreate(
        name="作成しようとする新しい事業所",
        office_type=OfficeType.type_B_office,
    )

    # 5. APIリクエストを実行
    #    このテストでは、特定のユーザーとしてAPIを叩くシミュレーションが必要
    #    ここでは依存性注入をオーバーライドする手法を用いる
    def override_get_current_user():
        return user_to_create

    app.dependency_overrides[get_current_active_user] = override_get_current_user

    try:
        response = await async_client.post(
            f"{settings.API_V1_STR}/offices/setup",
            json=jsonable_encoder(new_office_data),
        )

        # 6. レスポンスを検証
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        data = response.json()
        assert "detail" in data
        assert data["detail"] == "ユーザーは既に事業所に所属しています。"

    finally:
        # 7. テスト後にオーバーライドをクリア
        app.dependency_overrides.clear()


# --- 依存性注入を使った認証済みユーザーシミュレーションテスト ---

@pytest.mark.asyncio
async def test_setup_office_with_dependency_injection(
    async_client: AsyncClient,
    db_session: AsyncSession,
    service_admin_user_factory,
):
    """
    FastAPIの依存性注入を使って認証済みユーザーをシミュレートするテスト例。
    get_current_active_userをオーバーライドして特定のユーザーを返す。
    """
    # 1. テスト用のユーザーを作成
    user: Staff = await service_admin_user_factory(
        name="依存性注入テストユーザー",
        role=StaffRole.service_administrator,
    )
    
    # 2. 依存性注入をオーバーライドして、作成したユーザーを返すようにする
    def override_get_current_user():
        return user
    
    app.dependency_overrides[get_current_active_user] = override_get_current_user
    
    try:
        # 3. APIリクエストのペイロードを準備
        office_data = OfficeCreate(
            name="依存性注入テスト事業所",
            office_type=OfficeType.type_B_office,
        )
        
        # 4. APIリクエストを実行（認証ヘッダーは不要）
        response = await async_client.post(
            f"{settings.API_V1_STR}/offices/setup",
            json=jsonable_encoder(office_data),
        )
        
        # 5. レスポンスを検証
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["name"] == office_data.name
        
    finally:
        # 6. テスト後にオーバーライドをクリア
        app.dependency_overrides.clear()


@pytest.mark.asyncio 
async def test_dependency_injection_with_mock_fixture(
    async_client: AsyncClient,
    db_session: AsyncSession, 
    service_admin_user_factory,
):
    """
    より実用的な依存性注入テストの例。
    事前に作成したmock_current_userフィクスチャを活用する。
    """
    # 1. テスト用のユーザーを作成
    user: Staff = await service_admin_user_factory(
        name="モックフィクスチャユーザー",
        role=StaffRole.service_administrator,
        
    )
    
    # 2. 手動で依存性をオーバーライド
    def mock_user():
        return user
    
    app.dependency_overrides[get_current_active_user] = mock_user
    
    try:
        # 3. 依存性が正しく動作することを確認
        # 実際のAPIエンドポイントがあれば、ここでテストを実行
        office_data = OfficeCreate(
            name="モックフィクスチャテスト事業所", 
            office_type=OfficeType.type_B_office,
        )
        
        response = await async_client.post(
            f"{settings.API_V1_STR}/offices/setup",
            json=jsonable_encoder(office_data),
        )
        
        # エンドポイント実装済みのため200を期待
        assert response.status_code == status.HTTP_200_OK
        
    finally:
        # 4. クリーンアップ
        app.dependency_overrides.clear()

