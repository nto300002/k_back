# k_back/tests/test_main.py

from fastapi.testclient import TestClient
from app.main import app 

# TestClientインスタンスを作成
client = TestClient(app)


def test_read_root():
    """
    ルートエンドポイント ("/") のテスト
    """
    # 1. APIにリクエストを送信
    response = client.get("/")

    # 2. ステータスコードを検証
    assert response.status_code == 200

    # 3. レスポンスのJSONボディを検証
    assert response.json() == {"message": "Hello from k_back API"}


def test_read_item():
    """
    アイテム取得エンドポイント ("/api/v1/items/{item_id}") のテスト
    """
    # APIにリクエストを送信
    response = client.get("/api/v1/items/42?q=test_query")

    # ステータスコードを検証
    assert response.status_code == 200

    # レスポンスのJSONボディを検証
    assert response.json() == {
        "item_id": 42,
        "q": "test_query"
    }


def test_read_item_not_found():
    """
    存在しないアイテムIDに対するテスト (FastAPIが自動で422を返すことを確認)
    """
    # FastAPIは型ヒントに基づき、整数でないパスパラメータを無効と判断する
    response = client.get("/api/v1/items/not-an-int")

    # 不正なリクエストとして 422 Unprocessable Entity が返ることを検証
    assert response.status_code == 422