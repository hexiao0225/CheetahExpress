from typing import List, Optional
import structlog
from models import DriverInfo, VoiceCallResult, CallOutcome, RankingScore, OrderRequest
from database.neo4j_client import neo4j_client
import random

logger = structlog.get_logger()


class MockVoiceDispatchAgent:
    
    def __init__(self):
        self.neo4j = neo4j_client
        self.acceptance_rate = 0.7
    
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
                "Mock calling driver",
                driver_id=driver.driver_id,
                driver_name=driver.name,
                rank=rankings.index(ranking) + 1
            )
            
            call_result = await self._mock_call_driver(driver, order, ranking)
            
            self.neo4j.log_voice_call_outcome(
                order_id=order.order_id,
                driver_id=driver.driver_id,
                call_result={
                    "outcome": call_result.outcome.value,
                    "sentiment_score": call_result.sentiment_score,
                    "decline_reason": call_result.decline_reason,
                    "call_duration_seconds": call_result.call_duration_seconds
                }
            )
            
            if call_result.outcome == CallOutcome.ACCEPTED:
                logger.info(
                    "Mock driver accepted assignment",
                    driver_id=driver.driver_id,
                    driver_name=driver.name
                )
                return call_result
            else:
                logger.info(
                    "Mock driver declined or unavailable",
                    driver_id=driver.driver_id,
                    outcome=call_result.outcome.value,
                    reason=call_result.decline_reason
                )
        
        logger.warning("No driver accepted the assignment (mock)", order_id=order.order_id)
        return None
    
    async def _mock_call_driver(
        self,
        driver: DriverInfo,
        order: OrderRequest,
        ranking: RankingScore
    ) -> VoiceCallResult:
        accepts = random.random() < self.acceptance_rate
        
        if accepts:
            outcome = CallOutcome.ACCEPTED
            sentiment_score = random.uniform(0.6, 1.0)
            decline_reason = None
        else:
            outcome = CallOutcome.DECLINED
            sentiment_score = random.uniform(0.2, 0.5)
            decline_reasons = [
                "Already have another delivery",
                "Too far from current location",
                "Taking a break",
                "Vehicle maintenance needed",
                "End of shift approaching"
            ]
            decline_reason = random.choice(decline_reasons)
        
        call_duration = random.uniform(15, 45)
        
        result = VoiceCallResult(
            driver_id=driver.driver_id,
            outcome=outcome,
            sentiment_score=sentiment_score,
            decline_reason=decline_reason,
            transcript=f"Mock call to {driver.name}",
            call_duration_seconds=call_duration
        )
        
        logger.info(
            "Mock voice call completed",
            driver_id=driver.driver_id,
            outcome=outcome.value,
            sentiment=sentiment_score
        )
        
        return result
