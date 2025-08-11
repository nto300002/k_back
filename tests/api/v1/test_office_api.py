import pytest
from httpx import AsyncClient
from fastapi import status, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.main import app
from app.api import deps
from app.models.staff import Staff
from app.models.enums import StaffRole

# --- 認証をバイパスするための新しい依存性注入 ---
# この関数自体はシンプルにしておく
async def override_get_current_active_user() -> Staff:
    # この中身はテストごとに変わるので、実際にはあまり使われない
    raise NotImplementedError("This should be overridden in the test function.")

# --- テストの実行 ---
app.dependency_overrides[deps.get_current_active_user] = override_get_current_active_user

@pytest.mark.asyncio
async def test_setup_office_with_persistent_mock_auth(
    async_client: AsyncClient, 
    db_session: AsyncSession,
    service_admin_user_factory
):
    """
    永続化されたモックユーザーで認証した場合に、エンドポイントが正常に動作するかテスト
    """
    # --- テスト関数内で、具体的なモックユーザーを作成 ---
    test_user = await service_admin_user_factory(
        name="永続化テストユーザー",
        role=StaffRole.service_administrator
    )

    # --- テスト関数内で、依存性注入を上書き ---
    # これにより、このテストの実行中だけ get_current_active_user は
    # 上記で作成した test_user を返すようになる
    def get_mock_user() -> Staff:
        return test_user
    
    app.dependency_overrides[deps.get_current_active_user] = get_mock_user

    office_data = {"name": "APIテスト事業所", "office_type": "type_A_office"}
    response = await async_client.post("/api/v1/offices/setup", json=office_data)

    assert response.status_code == status.HTTP_200_OK
    assert response.json()["name"] == office_data["name"]

    # --- テスト後のクリーンアップ ---
    # 他のテストに影響を与えないように、オーバーライドを元に戻す
    app.dependency_overrides.pop(deps.get_current_active_user)
