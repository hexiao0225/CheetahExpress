import httpx
from typing import List, Dict, Any, Optional
import structlog
from config import settings
from models import DriverInfo, VoiceCallResult, CallOutcome, RankingScore, OrderRequest
from database.neo4j_client import neo4j_client

logger = structlog.get_logger()


class VoiceDispatchAgent:
    
    def __init__(self):
        self.modulate_base_url = settings.modulate_base_url
        self.api_key = settings.modulate_api_key
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        self.neo4j = neo4j_client
    
    async def dispatch_to_drivers(
        self,
        drivers: List[DriverInfo],
        rankings: List[RankingScore],
        order: OrderRequest
    ) -> Optional[VoiceCallResult]:
        driver_map = {d.driver_id: d for d in drivers}
        
        for ranking in rankings:
            driver = driver_map.get(ranking.driver_id)
            if not driver:
                continue
            
            logger.info(
                "Calling driver",
                driver_id=driver.driver_id,
                driver_name=driver.name,
                rank=rankings.index(ranking) + 1
            )
            
            call_result = await self._call_driver(driver, order, ranking)
            
            self.neo4j.log_voice_call_outcome(
                order_id=order.order_id,
                driver_id=driver.driver_id,
                call_result={
                    "outcome": call_result.outcome.value,
                    "sentiment_score": call_result.sentiment_score,
                    "decline_reason": call_result.decline_reason,
                    "transcript": call_result.transcript,
                    "call_duration_seconds": call_result.call_duration_seconds
                }
            )
            
            if call_result.outcome == CallOutcome.ACCEPTED:
                logger.info(
                    "Driver accepted assignment",
                    driver_id=driver.driver_id,
                    driver_name=driver.name
                )
                return call_result
            else:
                logger.info(
                    "Driver declined or unavailable",
                    driver_id=driver.driver_id,
                    outcome=call_result.outcome.value,
                    reason=call_result.decline_reason
                )
        
        logger.warning("No driver accepted the assignment", order_id=order.order_id)
        return None
    
    async def _call_driver(
        self,
        driver: DriverInfo,
        order: OrderRequest,
        ranking: RankingScore
    ) -> VoiceCallResult:
        try:
            call_script = self._generate_call_script(driver, order, ranking)
            
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.modulate_base_url}/voice/call",
                    headers=self.headers,
                    json={
                        "phone_number": driver.phone,
                        "script": call_script,
                        "driver_id": driver.driver_id,
                        "order_id": order.order_id,
                        "capture_response": True,
                        "sentiment_analysis": True
                    },
                    timeout=60.0
                )
                response.raise_for_status()
                data = response.json()
                
                outcome_str = data.get("outcome", "no_answer")
                outcome = CallOutcome(outcome_str)
                
                result = VoiceCallResult(
                    driver_id=driver.driver_id,
                    outcome=outcome,
                    sentiment_score=data.get("sentiment_score"),
                    decline_reason=data.get("decline_reason"),
                    transcript=data.get("transcript"),
                    call_duration_seconds=data.get("call_duration_seconds")
                )
                
                logger.info(
                    "Voice call completed",
                    driver_id=driver.driver_id,
                    outcome=outcome.value,
                    sentiment=result.sentiment_score
                )
                
                return result
                
        except httpx.HTTPError as e:
            logger.error(
                "Failed to make voice call via Modulate",
                driver_id=driver.driver_id,
                error=str(e)
            )
            return VoiceCallResult(
                driver_id=driver.driver_id,
                outcome=CallOutcome.FAILED,
                decline_reason=f"API error: {str(e)}"
            )
        except Exception as e:
            logger.error(
                "Unexpected error during voice call",
                driver_id=driver.driver_id,
                error=str(e)
            )
            return VoiceCallResult(
                driver_id=driver.driver_id,
                outcome=CallOutcome.FAILED,
                decline_reason=f"System error: {str(e)}"
            )

    def _generate_call_script(
        self,
        driver: DriverInfo,
        order: OrderRequest,
        ranking: RankingScore
    ) -> str:
        script = f"""
Hello {driver.name}, this is Cheetah Express dispatch.

We have a new delivery assignment for you:

Pickup Location: {order.pickup.address}
Dropoff Location: {order.dropoff.address}
Estimated time to pickup: {ranking.eta_to_pickup_minutes:.0f} minutes
Total delivery time: {ranking.total_trip_time_minutes:.0f} minutes
Vehicle required: {order.vehicle_type.value}
Time window: {order.time_window.start.strftime('%I:%M %p')} to {order.time_window.end.strftime('%I:%M %p')}

Customer: {order.customer_info.name}
Customer phone: {order.customer_info.phone}

{f"Special instructions: {order.special_instructions}" if order.special_instructions else ""}

Can you accept this delivery assignment? Please respond with 'yes' to accept or 'no' to decline.
If declining, please briefly state your reason.
"""
        return script.strip()
