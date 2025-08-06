from pydantic import BaseModel
from uuid import UUID

class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str

class TokenPayload(BaseModel):
    aud: str
    exp: int
    iat: int
    iss: str | None = None
    sub: str  # SupabaseではユーザーID(UUID)が文字列として入っている
    email: str | None = None
    phone: str | None = None
    role: str | None = None