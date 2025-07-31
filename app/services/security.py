from passlib.context import CryptContext

# bcryptアルゴリズムを使用する設定
# このコンテキストはテストデータ作成時にのみ利用する
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def get_password_hash(password: str) -> str:
    """
    平文のパスワードを受け取り、bcryptハッシュを返す。
    テスト環境でのダミーユーザー作成にのみ使用する。
    """
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    平文パスワードとハッシュ化済みパスワードを比較する。
    （主にテストや、将来的に独自認証を実装する場合のため）
    """
    return pwd_context.verify(plain_password, hashed_password)