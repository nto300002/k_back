# tests/conftest.py
import pytest
import pytest_asyncio
from typing import AsyncGenerator, Generator
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

from app.main import app
from app.db.base import Base
from app.core.config import settings
from app.api import deps # get_dbをオーバーライドするため

# --- 1. テスト用のDB設定 ---
# 本番とは別のテスト用DBのURLを設定
engine = create_async_engine(
    TEST_DATABASE_URL,
    echo=False, # 外部DBへの接続ログは通常Falseにするのが良い
    connect_args={"ssl": "prefer"} # SSL接続を試みる設定
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine, class_=AsyncSession)

@pytest_asyncio.fixture(scope="session", autouse=True)
async def setup_database() -> AsyncGenerator[None, None]:
    """
    テストセッションの開始時に一度だけ、テストDBのテーブルを全て作成し、
    終了時に全て削除する。
    """
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

# --- 2. テスト用のDBセッションをDIで注入する設定 ---
async def override_get_db() -> AsyncGenerator[AsyncSession, None]:
    """テスト用のDBセッションを返す依存性注入（DI）の上書き関数"""
    async with TestingSessionLocal() as session:
        yield session

# アプリケーションのDI設定をテスト用に上書き
app.dependency_overrides[deps.get_db] = override_get_db

# --- 3. APIテスト用の非同期HTTPクライアント ---
@pytest_asyncio.fixture(scope="module")
async def client() -> AsyncGenerator[AsyncClient, None]:
    """
    各テストモジュールで利用する、非同期対応のTestClient
    """
    async with AsyncClient(app=app, base_url="http://test") as c:
        yield c

# --- 4. テスト用のDBセッションフィクスチャ ---
@pytest_asyncio.fixture(scope="function")
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    """
    各テスト関数で利用するDBセッション。
    テスト関数ごとに独立したトランザクションを保証する。
    """
    async with TestingSessionLocal() as session:
        yield session
        await session.rollback() # 各テストの終了時にロールバックしてクリーンな状態に戻す