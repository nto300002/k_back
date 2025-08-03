from typing import AsyncGenerator
from fastapi import Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.db.session import SessionLocal
from app.models.staff import Staff

async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    APIエンドポイントで使うためのDBセッションを供給する依存性注入関数。
    リクエストの開始時にセッションを提供し、終了時に自動で閉じる。
    """
    async with SessionLocal() as session:
        yield session


async def get_current_active_user(db: AsyncSession = Depends(get_db)) -> Staff:
    """
    認証済みのアクティブなユーザーを取得する依存性注入関数。
    実際のプロダクションではSupabaseのJWTトークンを検証してユーザーを特定するが、
    テスト環境では依存性注入のオーバーライドでモックユーザーを返す。
    """
    # 実際の実装では、リクエストヘッダーからJWTトークンを取得・検証し、
    # Supabase APIまたはローカルDBからユーザー情報を取得する
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Not authenticated",
        headers={"WWW-Authenticate": "Bearer"},
    )
