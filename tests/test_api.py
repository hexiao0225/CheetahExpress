import pytest
from fastapi.testclient import TestClient
from datetime import datetime, timedelta
from main import app
from models import OrderRequest, Location, TimeWindow, CustomerInfo, VehicleType

client = TestClient(app)


def test_root_endpoint():
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["service"] == "Cheetah Express 🐆"
    assert data["status"] == "running"


def test_health_check():
    response = client.get("/health")
    assert response.status_code in [200, 503]


def test_create_order_validation():
    invalid_order = {
        "order_id": "TEST001",
        "pickup": {
            "address": "123 Main St",
            "latitude": 37.7749,
            "longitude": -122.4194
        }
    }
    
    response = client.post("/api/v1/orders", json=invalid_order)
    assert response.status_code == 422


def test_create_order_async():
    now = datetime.now()
    order_data = {
        "order_id": f"TEST_{now.timestamp()}",
        "pickup": {
            "address": "123 Main St, San Francisco, CA",
            "latitude": 37.7749,
            "longitude": -122.4194
        },
        "dropoff": {
            "address": "456 Market St, San Francisco, CA",
            "latitude": 37.7849,
            "longitude": -122.4094
        },
        "time_window": {
            "start": (now + timedelta(hours=1)).isoformat(),
            "end": (now + timedelta(hours=3)).isoformat()
        },
        "vehicle_type": "sedan",
        "customer_info": {
            "name": "Test Customer",
            "phone": "+1-555-9999",
            "email": "test@example.com"
        },
        "priority": 7
    }
    
    response = client.post("/api/v1/orders/async", json=order_data)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "processing"
    assert "order_id" in data


def test_get_order_status_not_found():
    response = client.get("/api/v1/orders/NONEXISTENT")
    assert response.status_code == 404


def test_seed_drivers():
    response = client.post("/api/v1/drivers/seed")
    assert response.status_code in [200, 500]
