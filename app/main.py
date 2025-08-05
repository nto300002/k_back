from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1 import api
from app.core.config import settings

# FastAPIアプリケーションを初期化
app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json"
)

# CORSミドルウェアの設定
# これにより、フロントエンド(http://localhost:3000)からのリクエストが許可される
if settings.BACKEND_CORS_ORIGINS:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[str(origin) for origin in settings.BACKEND_CORS_ORIGINS],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

# APIルーターをインクルード
# すべての /api/v1 で始まるパスがこのルーターに送られる
app.include_router(api.api_router, prefix=settings.API_V1_STR)