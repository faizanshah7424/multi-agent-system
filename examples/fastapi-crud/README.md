# CodeOrbit AI — FastAPI CRUD Example

This example demonstrates a structured FastAPI CRUD web service. It serves as a target workspace for verifying CodeOrbit AI's ability to refactor REST API routes, modify schema schemas, and validate endpoint health using standard python test harnesses.

---

## 🏗️ Architecture Overview

The application features:
1. **API Router & Logic** (`main.py`): Exposes REST endpoints (`/`, `/items/{id}`) and manages an in-memory dictionary database.
2. **Endpoint Validation** (`test_main.py`): Performs HTTP client calls using FastAPI `TestClient` to verify status codes and JSON payloads.

```mermaid
graph TD
    Client[HTTP Client] -->|GET / | API[FastAPI app in main.py]
    Client -->|POST /items/{id}| API
    API <-->|Read / Write| DB[(In-memory DB)]
    Test[test_main.py] -->|Simulates Requests| API
```

---

## 🛠️ Getting Started & Commands

### Prerequisites
* Python 3.11+
* FastAPI, Uvicorn, and Pytest:
  ```bash
  pip install fastapi uvicorn pytest httpx
  ```

### Run the API Server
To start the server locally:
```bash
uvicorn main:app --reload
```
The interactive documentation will be available at [http://localhost:8000/docs](http://localhost:8000/docs).

### Run the Tests
To run the integration tests:
```bash
pytest test_main.py
```

### Expected Output
```text
============================= test session starts =============================
collected 2 items

test_main.py ..                                                          [100%]
============================== 2 passed in 0.28s ==============================
```

---

## 🤖 CodeOrbit AI Integration & Usage Notes

Developers can direct CodeOrbit AI to alter schemas or build out missing routes:

### Example Tasks to Run
1. **Add Delete Endpoint**:
   ```bash
   python codeorbit.py run "Create a DELETE /items/{item_id} endpoint inside examples/fastapi-crud/main.py that removes the item from items_db. Return a confirmation message or raise 404 if missing. Write tests in test_main.py."
   ```

CodeOrbit AI will automatically branch, execute changes, run the TestClient integration suite inside the container sandbox, and merge changes on success.