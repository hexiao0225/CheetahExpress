from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum


class VehicleType(str, Enum):
    SEDAN = "sedan"
    SUV = "suv"
    VAN = "van"
    TRUCK = "truck"
    MOTORCYCLE = "motorcycle"


class OrderStatus(str, Enum):
    RECEIVED = "received"
    PROCESSING = "processing"
    DRIVER_ASSIGNED = "driver_assigned"
    DECLINED = "declined"
    FAILED = "failed"


class Location(BaseModel):
    address: str
    latitude: float
    longitude: float


class TimeWindow(BaseModel):
    start: datetime
    end: datetime


class CustomerInfo(BaseModel):
    name: str
    phone: str
    email: Optional[str] = None


class OrderRequest(BaseModel):
    order_id: str
    pickup: Location
    dropoff: Location
    time_window: TimeWindow
    vehicle_type: VehicleType
    customer_info: CustomerInfo
    special_instructions: Optional[str] = None
    priority: int = Field(default=5, ge=1, le=10)


class DriverInfo(BaseModel):
    driver_id: str
    name: str
    phone: str
    current_location: Location
    vehicle_type: VehicleType
    is_available: bool
    license_number: str
    license_expiry: datetime


class ComplianceResult(BaseModel):
    driver_id: str
    is_compliant: bool
    reasons: List[str]
    checks: Dict[str, bool] = Field(default_factory=dict)


class RoutingResult(BaseModel):
    driver_id: str
    eta_to_pickup_minutes: float
    eta_pickup_to_dropoff_minutes: float
    total_trip_time_minutes: float
    distance_km: float
    fits_sla: bool


class RankingScore(BaseModel):
    driver_id: str
    score: float
    eta_to_pickup_minutes: float
    total_trip_time_minutes: float
    vehicle_match: bool
    license_expiry_buffer_days: int
    remaining_km_budget: float
    reasoning: str


class CallOutcome(str, Enum):
    ACCEPTED = "accepted"
    DECLINED = "declined"
    NO_ANSWER = "no_answer"
    FAILED = "failed"


class VoiceCallResult(BaseModel):
    driver_id: str
    outcome: CallOutcome
    sentiment_score: Optional[float] = None
    decline_reason: Optional[str] = None
    transcript: Optional[str] = None
    call_duration_seconds: Optional[float] = None


class DispatchResult(BaseModel):
    order_id: str
    status: OrderStatus
    assigned_driver_id: Optional[str] = None
    assigned_driver_name: Optional[str] = None
    total_drivers_considered: int
    total_drivers_called: int
    processing_time_seconds: float
    audit_graph_id: str
    message: str
