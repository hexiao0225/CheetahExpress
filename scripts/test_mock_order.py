import requests
import json


def test_mock_order():
    base_url = "http://localhost:8000"
    
    print("🐆 Cheetah Express - Mock Order Test\n")
    print("=" * 60)
    
    print("\n1️⃣  Fetching available mock orders...")
    response = requests.get(f"{base_url}/api/v1/mock/orders")
    
    if response.status_code == 200:
        data = response.json()
        print(f"✅ Found {data['count']} mock orders available")
        print("\nAvailable orders:")
        for order in data['orders']:
            print(f"  - {order['order_id']}: {order['pickup']['address']} → {order['dropoff']['address']}")
            print(f"    Vehicle: {order['vehicle_type']}, Priority: {order['priority']}")
    else:
        print(f"❌ Failed to fetch mock orders: {response.status_code}")
        return
    
    print("\n" + "=" * 60)
    print("\n2️⃣  Submitting mock order ORD001...")
    
    response = requests.post(f"{base_url}/api/v1/mock/orders/ORD001", timeout=120)
    
    if response.status_code == 200:
        result = response.json()
        print("\n✅ Order processed successfully!")
        print(f"\n📊 Dispatch Result:")
        print(f"  Status: {result['status']}")
        print(f"  Assigned Driver: {result.get('assigned_driver_name', 'None')}")
        print(f"  Driver ID: {result.get('assigned_driver_id', 'None')}")
        print(f"  Drivers Considered: {result['total_drivers_considered']}")
        print(f"  Drivers Called: {result['total_drivers_called']}")
        print(f"  Processing Time: {result['processing_time_seconds']:.2f}s")
        print(f"  Message: {result['message']}")
        
        print(f"\n📋 View full audit trail:")
        print(f"  {base_url}/api/v1/orders/ORD001/audit")
        
        print("\n" + "=" * 60)
        print("\n3️⃣  Fetching audit trail...")
        
        audit_response = requests.get(f"{base_url}/api/v1/orders/ORD001/audit")
        if audit_response.status_code == 200:
            audit = audit_response.json()
            print(f"\n✅ Audit trail retrieved")
            print(f"\n  Compliance Checks: {len(audit.get('compliance_checks', []))}")
            print(f"  Rankings: {len(audit.get('rankings', []))}")
            print(f"  Voice Calls: {len(audit.get('voice_calls', []))}")
            print(f"  Assignments: {len(audit.get('assignments', []))}")
            
            if audit.get('voice_calls'):
                print(f"\n  Voice Call Results:")
                for call in audit['voice_calls']:
                    print(f"    - Driver {call.get('driver_id')}: {call.get('outcome')}")
                    if call.get('sentiment'):
                        print(f"      Sentiment: {call.get('sentiment'):.2f}")
                    if call.get('decline_reason'):
                        print(f"      Reason: {call.get('decline_reason')}")
        
        return result
    else:
        print(f"\n❌ Failed to process order: {response.status_code}")
        print(f"Error: {response.text}")
        return None


if __name__ == "__main__":
    print("\n🚀 Starting Cheetah Express Mock Order Test")
    print("Make sure the server is running: python main.py\n")
    
    try:
        test_mock_order()
        print("\n" + "=" * 60)
        print("\n✅ Test completed successfully!")
    except requests.exceptions.ConnectionError:
        print("\n❌ Error: Could not connect to server")
        print("Please start the server first: python main.py")
    except Exception as e:
        print(f"\n❌ Error: {e}")
