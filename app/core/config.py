from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    """
    アプリケーションの設定を管理するクラス。
    .envファイルから環境変数を読み込み、型を検証します。
    """
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding='utf-8', extra='ignore')

    # --- プロジェクト情報 ---
    PROJECT_NAME: str = "ケイカくん API"
    API_V1_STR: str = "/api/v1"

    # --- データベース設定 ---
    DATABASE_URL: str
    TEST_DATABASE_URL: str

    # --- Supabase設定 ---
    SUPABASE_URL: str
    SUPABASE_SERVICE_ROLE_KEY: str # 招待などに使うAdmin用のキー
    SUPABASE_JWT_SECRET: str       # JWTトークンの検証に使うシークレットキー

    # --- CORS設定 ---
    BACKEND_CORS_ORIGINS: list[str] = ["http://localhost:3000"]

# --- グローバルに使うための設定オブジェクト ---
settings = Settings()