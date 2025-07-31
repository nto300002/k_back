from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    """
    アプリケーションの設定を管理するクラス。
    .envファイルから環境変数を読み込み、型を検証します。
    """
    # model_configは、.envファイルの場所などをPydanticに教えるための設定です
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding='utf-8', extra='ignore')

    SUPABASE_URL: str
    SUPABASE_SERVICE_ROLE_KEY: str
    BACKEND_CORS_ORIGINS: list[str] = ["http://localhost:3000"]
    
    # --- データベース設定 ---
    DATABASE_URL: str
    TEST_DATABASE_URL: str

    # --- プロジェクト情報 ---
    PROJECT_NAME: str = "ケイカくん API"
    API_V1_STR: str = "/api/v1"

    # --- Supabase設定 (バックエンドからAdmin権限で操作するために必要) ---
    SUPABASE_URL: str
    SUPABASE_SERVICE_ROLE_KEY: str # 招待などに使うAdmin用のキー

    # --- CORS設定 ---
    BACKEND_CORS_ORIGINS: list[str] = ["http://localhost:3000"]


# --- グローバルに使うための設定オブジェクト ---
settings = Settings()