from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession

from app.core.config import settings

# データベースエンジンを作成
engine = create_async_engine(settings.DATABASE_URL, pool_pre_ping=True)

# データベースセッションを作成するためのファクトリ
# autocommit=False, autoflush=False は非同期セッションの標準設定
SessionLocal = async_sessionmaker(autocommit=False, autoflush=False, bind=engine)

async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    APIエンドポイントで使うためのDBセッションを供給する依存性注入関数。
    リクエストの開始時にセッションを提供し、終了時に自動で閉じる。
    """
    async with SessionLocal() as session:
        yield session