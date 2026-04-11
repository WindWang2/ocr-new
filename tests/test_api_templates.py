import pytest
from fastapi.testclient import TestClient
from backend.api.main import app
from backend.models.database import get_connection

client = TestClient(app)

def test_create_and_list_template():
    payload = {
        "instrument_type": "test_instrument_api",
        "name": "Test Instrument API",
        "description": "A test instrument template via API",
        "prompt_template": "Read the {field} carefully.",
        "fields": [
            {
                "name": "test_field",
                "label": "Test Field",
                "unit": "mg",
                "type": "float"
            }
        ],
        "keywords": ["api", "test"],
        "example_images": ["api_test.jpg"],
        "default_tier": 1
    }
    
    # POST
    response = client.post("/templates", json=payload)
    assert response.status_code == 200
    assert response.json()["success"] is True
    
    # GET
    response = client.get("/templates")
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    
    templates = data["templates"]
    found = None
    for t in templates:
        if t["instrument_type"] == "test_instrument_api":
            found = t
            break
            
    assert found is not None
    assert found["name"] == "Test Instrument API"
    assert found["description"] == "A test instrument template via API"
    assert found["prompt_template"] == "Read the {field} carefully."
    assert len(found["fields"]) == 1
    assert found["fields"][0]["name"] == "test_field"
    assert found["fields"][0]["label"] == "Test Field"
    assert found["fields"][0]["unit"] == "mg"
    assert found["keywords"] == ["api", "test"]
    assert found["example_images"] == ["api_test.jpg"]
    assert found["default_tier"] == 1
    
    # Cleanup DB
    conn = get_connection()
    c = conn.cursor()
    c.execute("DELETE FROM instrument_templates WHERE instrument_type = ?", ("test_instrument_api",))
    conn.commit()
    conn.close()
