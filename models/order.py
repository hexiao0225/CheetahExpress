from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class VehicleType(str, Enum):
    BIKE = "bike"
    MOTORCYCLE = "motorcycle"
    CAR = "car"
    VAN = "van"
    TRUCK = "truck"


class Coordinates(BaseModel):
    lat: float
    lng: float
    address: Optional[str] = None


class TimeWindow(BaseModel):
    pickup_by: datetime   # Latest time driver must arrive at pickup
    deliver_by: datetime  # Latest time package must be at dropoff


class CustomerInfo(BaseModel):
    name: str
    phone: str
    email: Optional[str] = None


class Order(BaseModel):
    order_id: str
    pickup: Coordinates
    dropoff: Coordinates
    time_window: TimeWindow
    vehicle_type: VehicleType
    customer_info: CustomerInfo
    package_description: Optional[str] = None
    priority: int = Field(default=1, ge=1, le=5)  # 1=normal, 5=urgent
    created_at: datetime = Field(default_factory=datetime.utcnow)


class OrderStatus(str, Enum):
    PENDING = "pending"
    DISPATCHING = "dispatching"
    ASSIGNED = "assigned"
    FAILED = "failed"
