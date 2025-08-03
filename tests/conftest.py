# tests/conftest.py
import pytest
import pytest_asyncio
from typing import AsyncGenerator, Generator
from httpx import AsyncClient, ASGITransport 
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, AsyncEngine
from sqlalchemy.orm import sessionmaker
from sqlalchemy import text
from typing import Optional

import uuid
from fastapi import HTTPException
from app.main import app
from app.db.base import Base
from app.core.config import settings
from app.api import deps
from app.api.deps import get_current_active_user
from app.services.security import get_password_hash
import subprocess
import asyncio
import time
from asyncpg.exceptions import InvalidCatalogNameError

from app.models.staff import Staff
from app.models.office import Office, OfficeStaff
from app.models.enums import StaffRole, OfficeType, BillingStatus

# --- 1. 【修正】DBの存在を保証するフィクスチャ (sessionスコープ) ---
@pytest_asyncio.fixture(scope="session", autouse=True)
async def setup_test_database():
    """
    テストセッションの開始時にDBを作成し、接続可能になるまで待機する。
    終了時にDBを削除する。
    """
 
    db_name = settings.TEST_DATABASE_URL.rsplit('/', 1)[-1]
    admin_url = settings.TEST_DATABASE_URL.replace(f"/{db_name}", "/postgres")
    admin_engine = create_async_engine(admin_url, isolation_level="AUTOCOMMIT")
    
    async with admin_engine.connect() as conn:
        await conn.execute(text(f'DROP DATABASE IF EXISTS "{db_name}" WITH (FORCE)'))
        await conn.execute(text(f'CREATE DATABASE "{db_name}"'))
    await admin_engine.dispose()
    
    # --- 接続リトライロジック ---
    # DBが実際に接続可能になるまで待機する
    test_engine = create_async_engine(settings.TEST_DATABASE_URL)
    retries = 5
    delay = 1  # 秒
    for i in range(retries):
        try:
            async with test_engine.connect() as conn:
                # 接続に成功したら、ループを抜ける
 
                break
        except (InvalidCatalogNameError, OSError) as e:
            if i == retries - 1:
                # リトライ上限に達したらエラーを発生させる
 
                raise e
    
            await asyncio.sleep(delay)
    await test_engine.dispose()

    yield # テストセッションを実行
    
    async with admin_engine.connect() as conn:
        await conn.execute(text(f'DROP DATABASE "{db_name}" WITH (FORCE)'))
    await admin_engine.dispose()



# --- 2. 【デバッグ用】テストごとのDBセッションを提供するフィクスチャ ---
@pytest_asyncio.fixture(scope="function")
async def db_session(setup_test_database) -> AsyncGenerator[AsyncSession, None]:
    """
    【デバッグ用】テーブル作成とテスト実行のトランザクションを分離する。
    これにより、問題がトランザクション内のDDLにあるのかを切り分ける。
    """
    # 1. テスト関数ごとのエンジンを作成
    engine = create_async_engine(settings.TEST_DATABASE_URL)

    # 2. テスト実行前に、トランザクションの外でテーブルを確定させる
    #    まず、前のテストの残骸を完全に削除する
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    #    次に、このテストで使うテーブルをすべて作成する
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    # 3. テスト自体は、テーブルが確定した後に、独立したトランザクション内で実行する
    async with engine.connect() as connection:
        async with connection.begin() as transaction:
            session = AsyncSession(bind=connection)
            yield session
            # テスト中の変更のみをロールバック
            await transaction.rollback()
    
    # 4. エンジンを破棄
    await engine.dispose()


# --- 3. ファクトリフィクスチャ (変更なし) ---
@pytest_asyncio.fixture
async def service_admin_user_factory(db_session: AsyncSession):
    async def _create_user(**kwargs) -> Staff:
        new_user = Staff(**kwargs)
        db_session.add(new_user)
        await db_session.flush()
        await db_session.refresh(new_user)
        return new_user
    yield _create_user

@pytest_asyncio.fixture
async def office_factory(db_session: AsyncSession):
    async def _create_office(**kwargs) -> Office:
        new_office = Office(**kwargs)
        db_session.add(new_office)
        await db_session.flush()
        await db_session.refresh(new_office)
        return new_office
    yield _create_office


@pytest_asyncio.fixture
async def office_staff_factory(db_session: AsyncSession):
    """
    テスト用のOfficeStaffをDBに作成し、
    そのオブジェクトを返すファクトリフィクスチャ。
    """
    
    async def _create_office_staff(
        staff_id: uuid.UUID,
        office_id: uuid.UUID,
        is_primary: bool = False,
    ) -> OfficeStaff:
        
        new_office_staff = OfficeStaff(
            staff_id=staff_id,
            office_id=office_id,
            is_primary=is_primary,
        )
        db_session.add(new_office_staff)
        await db_session.flush()
        await db_session.refresh(new_office_staff)
        
        return new_office_staff

    yield _create_office_staff


# --- 4. テスト用の依存性オーバーライド関連フィクスチャ ---
@pytest_asyncio.fixture
async def async_client(db_session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    """
    テスト用のHTTPクライアント。
    DBセッションの依存性をオーバーライドして、テスト用セッションを使用する。
    """
    # DBセッションの依存性をオーバーライド
    async def override_get_db():
        yield db_session
    
    app.dependency_overrides[deps.get_db] = override_get_db
    
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac
    
    # テスト後にオーバーライドをクリア
    app.dependency_overrides.clear()


@pytest_asyncio.fixture
def mock_current_user(request):
    """
    認証済みユーザーをモックするためのフィクスチャ。
    テスト関数で使用するユーザーを指定できる。
    
    使用方法:
    @pytest.mark.parametrize("mock_current_user", [user_instance], indirect=True)
    async def test_something(mock_current_user):
        # テスト実行時にget_current_active_userがuser_instanceを返す
    """
    user = getattr(request, 'param', None)
    
    def override_get_current_user():
        if user is None:
            raise HTTPException(status_code=401, detail="Not authenticated")
        return user
    
    app.dependency_overrides[get_current_active_user] = override_get_current_user
    
    yield user
    
    # テスト後にオーバーライドをクリア
    if get_current_active_user in app.dependency_overrides:
        del app.dependency_overrides[get_current_active_user]


