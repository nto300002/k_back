from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import SessionLocal

async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    APIエンドポイントで使うためのDBセッションを供給する依存性注入関数。
    リクエストの開始時にセッションを提供し、終了時に自動で閉じる。
    """
    async with SessionLocal() as session:
        yield session
