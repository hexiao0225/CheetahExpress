from typing import List, Dict
import structlog
from models import DriverInfo, RoutingResult, RankingScore, OrderRequest
from database.neo4j_client import neo4j_client
from datetime import datetime

logger = structlog.get_logger()


class RankingAgent:
    
    def __init__(self):
        self.neo4j = neo4j_client
    
    async def rank_drivers(
        self,
        drivers: List[DriverInfo],
        routing_results: List[RoutingResult],
        order: OrderRequest
    ) -> List[RankingScore]:
        driver_map = {d.driver_id: d for d in drivers}
        routing_map = {r.driver_id: r for r in routing_results}
        
        rankings = []
        
        for driver_id in routing_map.keys():
            driver = driver_map.get(driver_id)
            routing = routing_map.get(driver_id)
            
            if not driver or not routing:
                continue
            
            score = self._calculate_score(driver, routing, order)
            rankings.append(score)
        
        rankings.sort(key=lambda x: x.score, reverse=True)
        
        ranking_data = [
            {
                "driver_id": r.driver_id,
                "score": r.score,
                "eta_to_pickup_minutes": r.eta_to_pickup_minutes,
                "reasoning": r.reasoning
            }
            for r in rankings
        ]
        self.neo4j.log_ranking_decision(order.order_id, ranking_data)
        
        logger.info(
            "Driver ranking completed",
            total_drivers=len(rankings),
            top_driver=rankings[0].driver_id if rankings else None
        )
        
        return rankings
    
    def _calculate_score(
        self,
        driver: DriverInfo,
        routing: RoutingResult,
        order: OrderRequest
    ) -> RankingScore:
        score = 100.0
        
        eta_penalty = routing.eta_to_pickup_minutes * 0.5
        score -= eta_penalty
        
        vehicle_match = driver.vehicle_type == order.vehicle_type
        if vehicle_match:
            score += 20.0
        else:
            score -= 10.0
        
        days_until_expiry = (driver.license_expiry - datetime.now()).days
        if days_until_expiry > 90:
            score += 10.0
        elif days_until_expiry > 30:
            score += 5.0
        
        workload = self.neo4j.get_driver_workload_today(driver.driver_id)
        remaining_km = 300 - workload["km_today"]
        if remaining_km > 100:
            score += 15.0
        elif remaining_km > 50:
            score += 5.0
        
        total_trip_penalty = routing.total_trip_time_minutes * 0.2
        score -= total_trip_penalty
        
        reasoning = (
            f"ETA to pickup: {routing.eta_to_pickup_minutes:.1f}min "
            f"(penalty: -{eta_penalty:.1f}), "
            f"Vehicle match: {vehicle_match} "
            f"({'bonus: +20' if vehicle_match else 'penalty: -10'}), "
            f"License expiry: {days_until_expiry}d "
            f"(bonus: +{10 if days_until_expiry > 90 else 5 if days_until_expiry > 30 else 0}), "
            f"Remaining km: {remaining_km:.1f}km "
            f"(bonus: +{15 if remaining_km > 100 else 5 if remaining_km > 50 else 0}), "
            f"Total trip time: {routing.total_trip_time_minutes:.1f}min "
            f"(penalty: -{total_trip_penalty:.1f})"
        )
        
        return RankingScore(
            driver_id=driver.driver_id,
            score=score,
            eta_to_pickup_minutes=routing.eta_to_pickup_minutes,
            total_trip_time_minutes=routing.total_trip_time_minutes,
            vehicle_match=vehicle_match,
            license_expiry_buffer_days=days_until_expiry,
            remaining_km_budget=remaining_km,
            reasoning=reasoning
        )
