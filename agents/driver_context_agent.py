import httpx
from typing import List, Dict, Any
import structlog
from config import settings
from models import DriverInfo, Location, VehicleType
from datetime import datetime
import os

logger = structlog.get_logger()


class DriverContextAgent:
    
    def __init__(self, use_mock: bool = None):
        self.yutori_base_url = settings.yutori_base_url
        self.api_key = settings.yutori_api_key
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        if use_mock is None:
            self.use_mock = os.getenv("USE_MOCK_DATA", "true").lower() == "true"
        else:
            self.use_mock = use_mock
    
    async def get_active_drivers(self) -> List[DriverInfo]:
        if self.use_mock:
            return self._get_mock_drivers()
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(
                    f"{self.yutori_base_url}/drivers/active",
                    headers=self.headers,
                    timeout=10.0
                )
                response.raise_for_status()
                drivers_data = response.json()
                
                drivers = []
                for driver_data in drivers_data.get("drivers", []):
                    driver = DriverInfo(
                        driver_id=driver_data["driver_id"],
                        name=driver_data["name"],
                        phone=driver_data["phone"],
                        current_location=Location(
                            address=driver_data["location"]["address"],
                            latitude=driver_data["location"]["latitude"],
                            longitude=driver_data["location"]["longitude"]
                        ),
                        vehicle_type=VehicleType(driver_data["vehicle_type"]),
                        is_available=driver_data.get("is_available", True),
                        license_number=driver_data["license_number"],
                        license_expiry=datetime.fromisoformat(driver_data["license_expiry"])
                    )
                    drivers.append(driver)
                
                logger.info("Retrieved active drivers", count=len(drivers))
                return drivers
                
            except httpx.HTTPError as e:
                logger.error("Failed to fetch active drivers from Yutori", error=str(e))
                return []
            except Exception as e:
                logger.error("Unexpected error fetching drivers", error=str(e))
                return []
    
    async def get_driver_by_id(self, driver_id: str) -> DriverInfo | None:
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(
                    f"{self.yutori_base_url}/drivers/{driver_id}",
                    headers=self.headers,
                    timeout=10.0
                )
                response.raise_for_status()
                driver_data = response.json()
                
                driver = DriverInfo(
                    driver_id=driver_data["driver_id"],
                    name=driver_data["name"],
                    phone=driver_data["phone"],
                    current_location=Location(
                        address=driver_data["location"]["address"],
                        latitude=driver_data["location"]["latitude"],
                        longitude=driver_data["location"]["longitude"]
                    ),
                    vehicle_type=VehicleType(driver_data["vehicle_type"]),
                    is_available=driver_data.get("is_available", True),
                    license_number=driver_data["license_number"],
                    license_expiry=datetime.fromisoformat(driver_data["license_expiry"])
                )
                
                logger.info("Retrieved driver by ID", driver_id=driver_id)
                return driver
                
            except httpx.HTTPError as e:
                logger.error("Failed to fetch driver from Yutori", driver_id=driver_id, error=str(e))
                return None
            except Exception as e:
                logger.error("Unexpected error fetching driver", driver_id=driver_id, error=str(e))
                return None
    
    def _get_mock_drivers(self) -> List[DriverInfo]:
        from mock_data import get_mock_drivers
        drivers = get_mock_drivers()
        logger.info("Using mock driver data", count=len(drivers))
        return drivers
