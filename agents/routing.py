"""
Routing Agent — computes real-time ETAs using the Google Maps Distance Matrix API.

For each compliance-eligible driver:
  driver current GPS → pickup location → dropoff location

Determines which drivers can physically fulfil the order within the SLA time window.

Uses batch Distance Matrix requests to minimise API calls:
  - One call:  all drivers → pickup  (N origins, 1 destination)
  - One call:  pickup → dropoff      (1 origin, 1 destination, reused for all)
"""

import logging
from datetime import datetime
from typing import Dict, List

import httpx

from config import settings
from models.driver import Driver, RoutingResult
from models.order import Order

logger = logging.getLogger(__name__)

GOOGLE_MAPS_URL = "https://maps.googleapis.com/maps/api/distancematrix/json"


class RoutingAgent:
    def __init__(self):
        self.client = httpx.AsyncClient(timeout=15.0)

    async def compute_etas(
        self, eligible_drivers: List[Driver], order: Order
    ) -> List[RoutingResult]:
        """
        Batch ETA computation for all eligible drivers.
        Returns RoutingResult for every driver; check fits_sla to filter.
        """
        if not eligible_drivers:
            return []

        origins = "|".join(
            f"{d.current_gps.lat},{d.current_gps.lng}" for d in eligible_drivers
        )
        pickup_coord = f"{order.pickup.lat},{order.pickup.lng}"
        dropoff_coord = f"{order.dropoff.lat},{order.dropoff.lng}"

        # Batch call 1: all drivers → pickup
        drivers_to_pickup = await self._distance_matrix(
            origins=origins, destinations=pickup_coord
        )

        # Call 2: pickup → dropoff (single leg, shared across all drivers)
        pickup_to_dropoff = await self._distance_matrix(
            origins=pickup_coord, destinations=dropoff_coord
        )

        leg2 = pickup_to_dropoff["rows"][0]["elements"][0]
        leg2_duration_s = leg2["duration"]["value"]
        leg2_distance_m = leg2["distance"]["value"]

        now = datetime.utcnow()
        seconds_until_deliver_by = (order.time_window.deliver_by - now).total_seconds()

        results: List[RoutingResult] = []
        for i, driver in enumerate(eligible_drivers):
            element = drivers_to_pickup["rows"][i]["elements"][0]
            if element["status"] != "OK":
                logger.warning(f"No route for driver {driver.driver_id}: {element['status']}")
                continue

            leg1_duration_s = element["duration"]["value"]
            leg1_distance_m = element["distance"]["value"]
            total_trip_s = leg1_duration_s + leg2_duration_s
            total_distance_km = (leg1_distance_m + leg2_distance_m) / 1000

            results.append(
                RoutingResult(
                    driver_id=driver.driver_id,
                    eta_to_pickup_minutes=leg1_duration_s / 60,
                    eta_total_trip_minutes=total_trip_s / 60,
                    total_distance_km=total_distance_km,
                    fits_sla=total_trip_s <= seconds_until_deliver_by,
                )
            )

        feasible = sum(1 for r in results if r.fits_sla)
        logger.info(f"Routing: {feasible}/{len(eligible_drivers)} drivers can meet SLA")
        return results

    async def _distance_matrix(self, origins: str, destinations: str) -> Dict:
        response = await self.client.get(
            GOOGLE_MAPS_URL,
            params={
                "origins": origins,
                "destinations": destinations,
                "mode": "driving",
                "departure_time": "now",
                "traffic_model": "best_guess",
                "key": settings.google_maps_api_key,
            },
        )
        response.raise_for_status()
        data = response.json()
        if data["status"] != "OK":
            raise ValueError(
                f"Google Maps API error: {data['status']} — {data.get('error_message', '')}"
            )
        return data

    async def close(self):
        await self.client.aclose()
