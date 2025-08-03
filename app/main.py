from fastapi import FastAPI

from app.api.v1.endpoints import office

app = FastAPI()

app.include_router(office.router, prefix="/api/v1/offices", tags=["offices"])


@app.get("/")
def read_root():
    return {"message": "Hello from k_back API"}


@app.get("/api/v1/items/{item_id}")
def read_item(item_id: int, q: str | None = None):
    return {"item_id": item_id, "q": q}
