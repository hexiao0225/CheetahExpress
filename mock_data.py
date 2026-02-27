from datetime import datetime, timedelta
from models import DriverInfo, Location, VehicleType, OrderRequest, TimeWindow, CustomerInfo


MOCK_DRIVERS = [
    DriverInfo(
        driver_id="DRV001",
        name="John Smith",
        phone="+1-555-0101",
        current_location=Location(
            address="450 Sutter St, San Francisco, CA 94108",
            latitude=37.7897,
            longitude=-122.4072
        ),
        vehicle_type=VehicleType.SEDAN,
        is_available=True,
        license_number="DL123456",
        license_expiry=datetime.now() + timedelta(days=365)
    ),
    DriverInfo(
        driver_id="DRV002",
        name="Sarah Johnson",
        phone="+1-555-0102",
        current_location=Location(
            address="1 Market St, San Francisco, CA 94105",
            latitude=37.7939,
            longitude=-122.3959
        ),
        vehicle_type=VehicleType.SUV,
        is_available=True,
        license_number="DL234567",
        license_expiry=datetime.now() + timedelta(days=550)
    ),
    DriverInfo(
        driver_id="DRV003",
        name="Mike Chen",
        phone="+1-555-0103",
        current_location=Location(
            address="555 California St, San Francisco, CA 94104",
            latitude=37.7929,
            longitude=-122.4047
        ),
        vehicle_type=VehicleType.VAN,
        is_available=True,
        license_number="DL345678",
        license_expiry=datetime.now() + timedelta(days=75)
    ),
    DriverInfo(
        driver_id="DRV004",
        name="Emily Davis",
        phone="+1-555-0104",
        current_location=Location(
            address="100 Pine St, San Francisco, CA 94111",
            latitude=37.7921,
            longitude=-122.3989
        ),
        vehicle_type=VehicleType.SEDAN,
        is_available=True,
        license_number="DL456789",
        license_expiry=datetime.now() + timedelta(days=650)
    ),
    DriverInfo(
        driver_id="DRV005",
        name="Carlos Rodriguez",
        phone="+1-555-0105",
        current_location=Location(
            address="201 Mission St, San Francisco, CA 94105",
            latitude=37.7898,
            longitude=-122.3942
        ),
        vehicle_type=VehicleType.TRUCK,
        is_available=True,
        license_number="DL567890",
        license_expiry=datetime.now() + timedelta(days=330)
    ),
    DriverInfo(
        driver_id="DRV006",
        name="Lisa Wang",
        phone="+1-555-0106",
        current_location=Location(
            address="350 Bush St, San Francisco, CA 94104",
            latitude=37.7908,
            longitude=-122.4042
        ),
        vehicle_type=VehicleType.MOTORCYCLE,
        is_available=True,
        license_number="DL678901",
        license_expiry=datetime.now() + timedelta(days=200)
    ),
    DriverInfo(
        driver_id="DRV007",
        name="James Wilson",
        phone="+1-555-0107",
        current_location=Location(
            address="50 Fremont St, San Francisco, CA 94105",
            latitude=37.7897,
            longitude=-122.3972
        ),
        vehicle_type=VehicleType.SUV,
        is_available=True,
        license_number="DL789012",
        license_expiry=datetime.now() + timedelta(days=450)
    ),
    DriverInfo(
        driver_id="DRV008",
        name="Maria Garcia",
        phone="+1-555-0108",
        current_location=Location(
            address="123 Kearny St, San Francisco, CA 94108",
            latitude=37.7916,
            longitude=-122.4039
        ),
        vehicle_type=VehicleType.VAN,
        is_available=True,
        license_number="DL890123",
        license_expiry=datetime.now() + timedelta(days=500)
    )
]


MOCK_ORDERS = [
    {
        "order_id": "ORD001",
        "pickup": {
            "address": "123 Market St, San Francisco, CA 94103",
            "latitude": 37.7749,
            "longitude": -122.4194
        },
        "dropoff": {
            "address": "456 Mission St, San Francisco, CA 94105",
            "latitude": 37.7849,
            "longitude": -122.4094
        },
        "time_window": {
            "start": (datetime.now() + timedelta(hours=1)).isoformat(),
            "end": (datetime.now() + timedelta(hours=3)).isoformat()
        },
        "vehicle_type": "sedan",
        "customer_info": {
            "name": "Alice Cooper",
            "phone": "+1-555-2001",
            "email": "alice@example.com"
        },
        "special_instructions": "Handle with care - fragile items",
        "priority": 8
    },
    {
        "order_id": "ORD002",
        "pickup": {
            "address": "789 Howard St, San Francisco, CA 94103",
            "latitude": 37.7825,
            "longitude": -122.4039
        },
        "dropoff": {
            "address": "321 Folsom St, San Francisco, CA 94107",
            "latitude": 37.7875,
            "longitude": -122.3965
        },
        "time_window": {
            "start": (datetime.now() + timedelta(hours=2)).isoformat(),
            "end": (datetime.now() + timedelta(hours=4)).isoformat()
        },
        "vehicle_type": "suv",
        "customer_info": {
            "name": "Bob Martinez",
            "phone": "+1-555-2002",
            "email": "bob@example.com"
        },
        "special_instructions": "Call upon arrival",
        "priority": 6
    },
    {
        "order_id": "ORD003",
        "pickup": {
            "address": "555 California St, San Francisco, CA 94104",
            "latitude": 37.7929,
            "longitude": -122.4047
        },
        "dropoff": {
            "address": "888 Brannan St, San Francisco, CA 94103",
            "latitude": 37.7715,
            "longitude": -122.4041
        },
        "time_window": {
            "start": (datetime.now() + timedelta(minutes=30)).isoformat(),
            "end": (datetime.now() + timedelta(hours=2)).isoformat()
        },
        "vehicle_type": "van",
        "customer_info": {
            "name": "Carol White",
            "phone": "+1-555-2003"
        },
        "special_instructions": "Large package - needs van",
        "priority": 9
    },
    {
        "order_id": "ORD004",
        "pickup": {
            "address": "200 Pine St, San Francisco, CA 94104",
            "latitude": 37.7922,
            "longitude": -122.4012
        },
        "dropoff": {
            "address": "150 Spear St, San Francisco, CA 94105",
            "latitude": 37.7913,
            "longitude": -122.3931
        },
        "time_window": {
            "start": (datetime.now() + timedelta(hours=1, minutes=30)).isoformat(),
            "end": (datetime.now() + timedelta(hours=3, minutes=30)).isoformat()
        },
        "vehicle_type": "sedan",
        "customer_info": {
            "name": "David Lee",
            "phone": "+1-555-2004",
            "email": "david@example.com"
        },
        "priority": 7
    },
    {
        "order_id": "ORD005",
        "pickup": {
            "address": "99 Grove St, San Francisco, CA 94102",
            "latitude": 37.7765,
            "longitude": -122.4231
        },
        "dropoff": {
            "address": "1 Embarcadero Center, San Francisco, CA 94111",
            "latitude": 37.7946,
            "longitude": -122.3999
        },
        "time_window": {
            "start": (datetime.now() + timedelta(hours=3)).isoformat(),
            "end": (datetime.now() + timedelta(hours=5)).isoformat()
        },
        "vehicle_type": "motorcycle",
        "customer_info": {
            "name": "Eva Brown",
            "phone": "+1-555-2005",
            "email": "eva@example.com"
        },
        "special_instructions": "Express delivery - documents only",
        "priority": 10
    }
]


def get_mock_drivers():
    """Return list of mock drivers for testing"""
    return MOCK_DRIVERS


def get_mock_order(order_id: str = None):
    """Get a specific mock order or a random one"""
    if order_id:
        for order in MOCK_ORDERS:
            if order["order_id"] == order_id:
                return order
    return MOCK_ORDERS[0]


def get_all_mock_orders():
    """Return all mock orders"""
    return MOCK_ORDERS
