"""
Driver Context Agent — fetches live driver data from the Yutori API.

Yutori provides: live GPS positions, active/available status, driver profiles,
phone numbers, vehicle info, license data, shift windows, and km budgets.

TODO: Adapt endpoint paths and response field names to the actual Yutori API docs.
"""

import logging
from datetime import datetime
from typing import List

import httpx

from config import settings
from models.driver import Driver, DriverStatus
from models.order import Coordinates

logger = logging.getLogger(__name__)


class DriverContextAgent:
    def __init__(self):
        self.client = httpx.AsyncClient(
            base_url=settings.yutori_base_url,
            headers={"Authorization": f"Bearer {settings.yutori_api_key}"},
            timeout=10.0,
        )

    async def get_active_drivers(self) -> List[Driver]:
        """
        Fetch all currently active/available drivers from Yutori.
        Returns only drivers whose status is ACTIVE (not BUSY or OFFLINE).

        TODO: Confirm Yutori's exact endpoint and response schema.
        """
        try:
            response = await self.client.get("/drivers", params={"status": "active"})
            response.raise_for_status()
            data = response.json()

            drivers = []
            for d in data.get("drivers", []):
                drivers.append(
                    Driver(
                        driver_id=d["id"],
                        name=d["name"],
                        phone=d["phone"],
                        current_gps=Coordinates(
                            lat=d["location"]["lat"],
                            lng=d["location"]["lng"],
                        ),
                        status=DriverStatus(d.get("status", "active")),
                        vehicle_type=d.get("vehicle_type", "car"),
                        license_expiry=d["license"]["expiry_date"],
                        km_budget_remaining_today=d.get("km_budget_remaining", 200.0),
                        shift_start=datetime.fromisoformat(d["shift"]["start"]),
                        shift_end=datetime.fromisoformat(d["shift"]["end"]),
                    )
                )

            logger.info(f"Fetched {len(drivers)} active drivers from Yutori")
            return drivers

        except httpx.HTTPError as e:
            logger.error(f"Yutori API error: {e}")
            raise

    async def close(self):
        await self.client.aclose()
