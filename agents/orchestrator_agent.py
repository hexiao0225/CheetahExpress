from openai import AsyncOpenAI
import structlog
from typing import Dict, Any, Optional
from config import settings
from models import OrderRequest, DispatchResult, OrderStatus
from agents.driver_context_agent import DriverContextAgent
from agents.compliance_agent import ComplianceAgent
from agents.routing_agent import RoutingAgent
from agents.ranking_agent import RankingAgent
from agents.voice_dispatch_agent import VoiceDispatchAgent
from database.neo4j_client import neo4j_client
import time
import os

logger = structlog.get_logger()


class OrchestratorAgent:
    
    def __init__(self, use_mock: bool = None):
        if use_mock is None:
            use_mock = os.getenv("USE_MOCK_DATA", "true").lower() == "true"
        
        self.use_mock = use_mock
        self.openai_client = AsyncOpenAI(api_key=settings.openai_api_key)
        self.driver_context_agent = DriverContextAgent()
        self.compliance_agent = ComplianceAgent()
        
        if use_mock:
            from agents.mock_routing_agent import MockRoutingAgent
            from agents.mock_voice_agent import MockVoiceDispatchAgent
            self.routing_agent = MockRoutingAgent()
            self.voice_dispatch_agent = MockVoiceDispatchAgent()
            logger.info("🎭 Using MOCK MODE for routing and voice dispatch")
        else:
            self.routing_agent = RoutingAgent()
            self.voice_dispatch_agent = VoiceDispatchAgent()
            logger.info("🌐 Using REAL APIs for routing and voice dispatch")
        
        self.ranking_agent = RankingAgent()
        self.neo4j = neo4j_client
    
    async def process_order(self, order: OrderRequest) -> DispatchResult:
        start_time = time.time()
        
        logger.info(
            "🐆 Cheetah Express: Processing new order",
            order_id=order.order_id,
            pickup=order.pickup.address,
            dropoff=order.dropoff.address,
            vehicle_type=order.vehicle_type.value
        )
        
        try:
            order_data = {
                "order_id": order.order_id,
                "pickup_address": order.pickup.address,
                "dropoff_address": order.dropoff.address,
                "vehicle_type": order.vehicle_type.value,
                "time_window_start": order.time_window.start.isoformat(),
                "time_window_end": order.time_window.end.isoformat()
            }
            self.neo4j.create_order_audit_graph(order.order_id, order_data)
            
            await self._analyze_order_with_gpt(order)
            
            logger.info("Step 1: Fetching active drivers from local mock pool")
            active_drivers = await self.driver_context_agent.get_active_drivers()
            
            if not active_drivers:
                return self._create_failure_result(
                    order, start_time, "No active drivers available"
                )
            
            logger.info(f"Step 2: Running compliance checks on {len(active_drivers)} drivers")
            compliance_results = await self.compliance_agent.check_compliance(
                active_drivers, order
            )
            
            compliant_drivers = self.compliance_agent.filter_compliant_drivers(
                active_drivers, compliance_results
            )
            
            if not compliant_drivers:
                return self._create_failure_result(
                    order, start_time, "No compliant drivers found"
                )
            
            logger.info(f"Step 3: Calculating routes for {len(compliant_drivers)} compliant drivers")
            routing_results = await self.routing_agent.calculate_routes(
                compliant_drivers, order
            )
            
            sla_compliant_routes = self.routing_agent.filter_sla_compliant_routes(
                routing_results
            )
            
            if not sla_compliant_routes:
                return self._create_failure_result(
                    order, start_time, "No drivers can meet SLA time window"
                )
            
            eligible_driver_ids = {r.driver_id for r in sla_compliant_routes}
            eligible_drivers = [
                d for d in compliant_drivers if d.driver_id in eligible_driver_ids
            ]
            
            logger.info(f"Step 4: Ranking {len(eligible_drivers)} eligible drivers")
            rankings = await self.ranking_agent.rank_drivers(
                eligible_drivers, sla_compliant_routes, order
            )
            
            if not rankings:
                return self._create_failure_result(
                    order, start_time, "No drivers to rank"
                )
            
            logger.info(
                f"Step 5: Dispatching via voice calls to {len(rankings)} drivers in ranked order"
            )
            accepted_call = await self.voice_dispatch_agent.dispatch_to_drivers(
                eligible_drivers, rankings, order
            )
            
            if not accepted_call:
                self.neo4j.update_order_status(
                    order.order_id, 
                    OrderStatus.DECLINED.value,
                    "All drivers declined or were unavailable"
                )
                return self._create_failure_result(
                    order, start_time, "All drivers declined the assignment"
                )
            
            assigned_driver = next(
                (d for d in eligible_drivers if d.driver_id == accepted_call.driver_id),
                None
            )
            
            if assigned_driver:
                routing_result = next(
                    (r for r in sla_compliant_routes if r.driver_id == accepted_call.driver_id),
                    None
                )
                
                if routing_result:
                    self.neo4j.log_assignment(
                        order_id=order.order_id,
                        driver_id=assigned_driver.driver_id,
                        distance_km=routing_result.distance_km,
                        duration_hours=routing_result.total_trip_time_minutes / 60
                    )
            
            processing_time = time.time() - start_time
            
            result = DispatchResult(
                order_id=order.order_id,
                status=OrderStatus.DRIVER_ASSIGNED,
                assigned_driver_id=accepted_call.driver_id,
                assigned_driver_name=assigned_driver.name if assigned_driver else None,
                total_drivers_considered=len(active_drivers),
                total_drivers_called=len(rankings),
                processing_time_seconds=processing_time,
                audit_graph_id=order.order_id,
                message=f"Successfully assigned to driver {assigned_driver.name if assigned_driver else accepted_call.driver_id}"
            )
            
            logger.info(
                "🐆 Order successfully dispatched",
                order_id=order.order_id,
                driver_id=accepted_call.driver_id,
                driver_name=assigned_driver.name if assigned_driver else "Unknown",
                processing_time=f"{processing_time:.2f}s"
            )
            
            return result
            
        except Exception as e:
            logger.error(
                "Error processing order",
                order_id=order.order_id,
                error=str(e),
                exc_info=True
            )
            self.neo4j.update_order_status(
                order.order_id,
                OrderStatus.FAILED.value,
                f"System error: {str(e)}"
            )
            return self._create_failure_result(
                order, start_time, f"System error: {str(e)}"
            )
    
    async def _analyze_order_with_gpt(self, order: OrderRequest) -> Dict[str, Any]:
        try:
            prompt = f"""
Analyze this delivery order and provide strategic insights:

Order ID: {order.order_id}
Pickup: {order.pickup.address}
Dropoff: {order.dropoff.address}
Vehicle Type: {order.vehicle_type.value}
Time Window: {order.time_window.start} to {order.time_window.end}
Priority: {order.priority}/10
Special Instructions: {order.special_instructions or 'None'}

Provide:
1. Urgency assessment
2. Potential challenges
3. Recommended driver characteristics
4. Risk factors

Keep response concise (3-4 sentences).
"""
            
            response = await self.openai_client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {
                        "role": "system",
                        "content": "You are the Cheetah Express orchestrator AI. Analyze delivery orders and provide strategic dispatch insights."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.3,
                max_tokens=200
            )
            
            analysis = response.choices[0].message.content
            logger.info("GPT-4o order analysis", analysis=analysis)
            
            return {"analysis": analysis}
            
        except Exception as e:
            logger.error("GPT analysis failed", error=str(e))
            return {"analysis": "Analysis unavailable"}
    
    def _create_failure_result(
        self, 
        order: OrderRequest, 
        start_time: float, 
        message: str
    ) -> DispatchResult:
        processing_time = time.time() - start_time
        
        return DispatchResult(
            order_id=order.order_id,
            status=OrderStatus.FAILED,
            assigned_driver_id=None,
            assigned_driver_name=None,
            total_drivers_considered=0,
            total_drivers_called=0,
            processing_time_seconds=processing_time,
            audit_graph_id=order.order_id,
            message=message
        )
