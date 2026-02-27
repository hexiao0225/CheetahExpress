import httpx
from typing import List, Dict, Any
import structlog
from config import settings
from models import DriverInfo, RoutingResult, OrderRequest, Location

logger = structlog.get_logger()


class RoutingAgent:
    
    def __init__(self):
        self.google_maps_api_key = settings.google_maps_api_key
        self.yutori_base_url = settings.yutori_base_url
        self.yutori_api_key = settings.yutori_api_key
    
    async def calculate_routes(
        self, 
        drivers: List[DriverInfo], 
        order: OrderRequest
    ) -> List[RoutingResult]:
        routing_results = []
        
        for driver in drivers:
            result = await self._calculate_single_route(driver, order)
            if result:
                routing_results.append(result)
        
        logger.info(
            "Route calculations completed",
            total_drivers=len(drivers),
            successful_routes=len(routing_results)
        )
        
        return routing_results
    
    async def _calculate_single_route(
        self, 
        driver: DriverInfo, 
        order: OrderRequest
    ) -> RoutingResult | None:
        try:
            origins = f"{driver.current_location.latitude},{driver.current_location.longitude}"
            destinations = f"{order.pickup.latitude},{order.pickup.longitude}"
            
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    "https://maps.googleapis.com/maps/api/distancematrix/json",
                    params={
                        "origins": origins,
                        "destinations": destinations,
                        "key": self.google_maps_api_key,
                        "mode": "driving",
                        "departure_time": "now"
                    },
                    timeout=10.0
                )
                response.raise_for_status()
                data = response.json()
                
                if data["status"] != "OK":
                    logger.error("Google Maps API error", status=data["status"])
                    return None
                
                element = data["rows"][0]["elements"][0]
                if element["status"] != "OK":
                    logger.error("Route calculation failed", driver_id=driver.driver_id)
                    return None
                
                eta_to_pickup_seconds = element["duration"]["value"]
                eta_to_pickup_minutes = eta_to_pickup_seconds / 60
                
                pickup_to_dropoff_origins = f"{order.pickup.latitude},{order.pickup.longitude}"
                pickup_to_dropoff_destinations = f"{order.dropoff.latitude},{order.dropoff.longitude}"
                
                response2 = await client.get(
                    "https://maps.googleapis.com/maps/api/distancematrix/json",
                    params={
                        "origins": pickup_to_dropoff_origins,
                        "destinations": pickup_to_dropoff_destinations,
                        "key": self.google_maps_api_key,
                        "mode": "driving"
                    },
                    timeout=10.0
                )
                response2.raise_for_status()
                data2 = response2.json()
                
                element2 = data2["rows"][0]["elements"][0]
                eta_pickup_to_dropoff_seconds = element2["duration"]["value"]
                eta_pickup_to_dropoff_minutes = eta_pickup_to_dropoff_seconds / 60
                distance_meters = element2["distance"]["value"]
                distance_km = distance_meters / 1000
                
                total_trip_time_minutes = eta_to_pickup_minutes + eta_pickup_to_dropoff_minutes
                
                time_window_minutes = (
                    order.time_window.end - order.time_window.start
                ).total_seconds() / 60
                
                fits_sla = total_trip_time_minutes <= time_window_minutes
                
                result = RoutingResult(
                    driver_id=driver.driver_id,
                    eta_to_pickup_minutes=eta_to_pickup_minutes,
                    eta_pickup_to_dropoff_minutes=eta_pickup_to_dropoff_minutes,
                    total_trip_time_minutes=total_trip_time_minutes,
                    distance_km=distance_km,
                    fits_sla=fits_sla
                )
                
                logger.info(
                    "Route calculated",
                    driver_id=driver.driver_id,
                    eta_minutes=total_trip_time_minutes,
                    fits_sla=fits_sla
                )
                
                return result
                
        except Exception as e:
            logger.error(
                "Failed to calculate route",
                driver_id=driver.driver_id,
                error=str(e)
            )
            return None
    
    def filter_sla_compliant_routes(
        self, 
        routing_results: List[RoutingResult]
    ) -> List[RoutingResult]:
        sla_compliant = [r for r in routing_results if r.fits_sla]
        
        logger.info(
            "Filtered SLA-compliant routes",
            total=len(routing_results),
            sla_compliant=len(sla_compliant)
        )
        
        return sla_compliant
