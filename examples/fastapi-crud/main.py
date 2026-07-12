from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Dict

app = FastAPI(title="Example FastAPI CRUD")


class Item(BaseModel):
    name: str
    price: float


items_db: Dict[int, Item] = {}


@app.get("/")
def index():
    return {"status": "ok", "items_count": len(items_db)}


@app.post("/items/{item_id}", response_model=Item)
def create_item(item_id: int, item: Item):
    if item_id in items_db:
        raise HTTPException(status_code=400, detail="Item already exists")
    items_db[item_id] = item
    return item


@app.get("/items/{item_id}", response_model=Item)
def get_item(item_id: int):
    if item_id not in items_db:
        raise HTTPException(status_code=404, detail="Item not found")
    return items_db[item_id]
