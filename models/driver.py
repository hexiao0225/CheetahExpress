from __future__ import annotations

from datetime import date, datetime
from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, Field

from models.order import Coordinates


class DriverStatus(str, Enum):
    ACTIVE = "active"
    BUSY = "busy"
    OFFLINE = "offline"


class Driver(BaseModel):
    driver_id: str
    name: str
    phone: str
    current_gps: Coordinates
    status: DriverStatus
    vehicle_type: str
    license_expiry: date
    km_budget_remaining_today: float  # km left in today's daily budget
    shift_start: datetime
    shift_end: datetime


class ComplianceResult(BaseModel):
    driver_id: str
    eligible: bool
    failure_reasons: List[str] = []
    license_days_remaining: int
    vehicle_match: bool
    km_budget_ok: bool
    shift_window_ok: bool


class RoutingResult(BaseModel):
    driver_id: str
    eta_to_pickup_minutes: float
    eta_total_trip_minutes: float
    total_distance_km: float
    fits_sla: bool


class RankedDriver(BaseModel):
    driver_id: str
    name: str
    phone: str
    score: float
    rank: int
    eta_to_pickup_minutes: float
    eta_total_trip_minutes: float
    compliance: ComplianceResult
    routing: RoutingResult


class DispatchOutcome(BaseModel):
    driver_id: str
    outcome: str  # "accepted" | "declined" | "no_answer" | "error"
    sentiment_score: Optional[float] = None
    decline_reason: Optional[str] = None
    call_duration_seconds: Optional[int] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)
