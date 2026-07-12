from fastapi.testclient import TestClient
from main import app

client = TestClient(app)


def test_read_root():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_create_and_get_item():
    item_data = {"name": "Laptop", "price": 999.99}
    response = client.post("/items/1", json=item_data)
    assert response.status_code == 200
    assert response.json()["name"] == "Laptop"

    response = client.get("/items/1")
    assert response.status_code == 200
    assert response.json()["price"] == 999.99
