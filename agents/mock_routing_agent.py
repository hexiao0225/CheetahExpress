from typing import List
import structlog
from models import DriverInfo, RoutingResult, OrderRequest
import random

logger = structlog.get_logger()


class MockRoutingAgent:
    
    async def calculate_routes(
        self, 
        drivers: List[DriverInfo], 
        order: OrderRequest
    ) -> List[RoutingResult]:
        routing_results = []
        
        for driver in drivers:
            result = self._calculate_mock_route(driver, order)
            if result:
                routing_results.append(result)
        
        logger.info(
            "Mock route calculations completed",
            total_drivers=len(drivers),
            successful_routes=len(routing_results)
        )
        
        return routing_results
    
    def _calculate_mock_route(
        self, 
        driver: DriverInfo, 
        order: OrderRequest
    ) -> RoutingResult:
        import math
        
        def haversine_distance(lat1, lon1, lat2, lon2):
            R = 6371
            
            lat1_rad = math.radians(lat1)
            lat2_rad = math.radians(lat2)
            delta_lat = math.radians(lat2 - lat1)
            delta_lon = math.radians(lon2 - lon1)
            
            a = math.sin(delta_lat/2)**2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(delta_lon/2)**2
            c = 2 * math.asin(math.sqrt(a))
            
            return R * c
        
        distance_to_pickup = haversine_distance(
            driver.current_location.latitude,
            driver.current_location.longitude,
            order.pickup.latitude,
            order.pickup.longitude
        )
        
        distance_pickup_to_dropoff = haversine_distance(
            order.pickup.latitude,
            order.pickup.longitude,
            order.dropoff.latitude,
            order.dropoff.longitude
        )
        
        avg_speed_kmh = 30
        eta_to_pickup_minutes = (distance_to_pickup / avg_speed_kmh) * 60
        eta_pickup_to_dropoff_minutes = (distance_pickup_to_dropoff / avg_speed_kmh) * 60
        
        eta_to_pickup_minutes += random.uniform(-2, 5)
        eta_pickup_to_dropoff_minutes += random.uniform(-2, 5)
        
        total_trip_time_minutes = eta_to_pickup_minutes + eta_pickup_to_dropoff_minutes
        
        time_window_minutes = (
            order.time_window.end - order.time_window.start
        ).total_seconds() / 60
        
        fits_sla = total_trip_time_minutes <= time_window_minutes
        
        result = RoutingResult(
            driver_id=driver.driver_id,
            eta_to_pickup_minutes=max(1, eta_to_pickup_minutes),
            eta_pickup_to_dropoff_minutes=max(1, eta_pickup_to_dropoff_minutes),
            total_trip_time_minutes=max(2, total_trip_time_minutes),
            distance_km=distance_to_pickup + distance_pickup_to_dropoff,
            fits_sla=fits_sla
        )
        
        logger.info(
            "Mock route calculated",
            driver_id=driver.driver_id,
            eta_minutes=total_trip_time_minutes,
            fits_sla=fits_sla
        )
        
        return result
    
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
