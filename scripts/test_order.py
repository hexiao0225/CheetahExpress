import requests
from datetime import datetime, timedelta
import json


def create_test_order():
    url = "http://localhost:8000/api/v1/orders"
    
    now = datetime.now()
    
    order = {
        "order_id": f"ORD_{int(now.timestamp())}",
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
            "name": "John Doe",
            "phone": "+1-555-1234",
            "email": "john@example.com"
        },
        "special_instructions": "Handle with care - fragile items",
        "priority": 8
    }
    
    print("🐆 Creating test order...")
    print(f"Order ID: {order['order_id']}")
    print(f"Pickup: {order['pickup']['address']}")
    print(f"Dropoff: {order['dropoff']['address']}")
    print(f"Vehicle: {order['vehicle_type']}")
    print("\nSending request...\n")
    
    try:
        response = requests.post(url, json=order, timeout=120)
        response.raise_for_status()
        
        result = response.json()
        
        print("✅ Order processed successfully!")
        print(f"\nStatus: {result['status']}")
        print(f"Assigned Driver: {result.get('assigned_driver_name', 'None')}")
        print(f"Driver ID: {result.get('assigned_driver_id', 'None')}")
        print(f"Drivers Considered: {result['total_drivers_considered']}")
        print(f"Drivers Called: {result['total_drivers_called']}")
        print(f"Processing Time: {result['processing_time_seconds']:.2f}s")
        print(f"Message: {result['message']}")
        
        print(f"\n📊 View audit trail:")
        print(f"http://localhost:8000/api/v1/orders/{order['order_id']}/audit")
        
        return result
        
    except requests.exceptions.RequestException as e:
        print(f"❌ Error: {e}")
        if hasattr(e, 'response') and e.response is not None:
            print(f"Response: {e.response.text}")
        return None


if __name__ == "__main__":
    create_test_order()
