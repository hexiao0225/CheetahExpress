"""
Audit Logger — stores post-dispatch decisions in Neo4j for tracing and ops review.

Graph relationships written per order:
  (Order)-[:RANKED             {score, rank, eta_pickup_min}]->(Driver)
  (Order)-[:DISPATCH_ATTEMPTED {outcome, sentiment, decline_reason, ...}]->(Driver)
  (Order)-[:ASSIGNED_TO        {assigned_at}]->(Driver)

Example queries:
  "Which driver was ranked #1 for order Y?"
  "Show all orders where every driver declined."
  "Average calls attempted before a successful assignment."
"""

import logging
from datetime import datetime
from typing import List

from db.client import get_driver
from models.driver import DispatchOutcome, RankedDriver
from models.order import Order

logger = logging.getLogger(__name__)


class AuditLogger:
    async def log_order(self, order: Order) -> None:
        driver = await get_driver()
        async with driver.session() as session:
            await session.run(
                """
                MERGE (o:Order {order_id: $order_id})
                SET o.status        = 'dispatching',
                    o.vehicle_type  = $vehicle_type,
                    o.pickup_addr   = $pickup_addr,
                    o.dropoff_addr  = $dropoff_addr,
                    o.deliver_by    = $deliver_by,
                    o.priority      = $priority,
                    o.created_at    = $created_at
                """,
                {
                    "order_id": order.order_id,
                    "vehicle_type": order.vehicle_type.value,
                    "pickup_addr": order.pickup.address,
                    "dropoff_addr": order.dropoff.address,
                    "deliver_by": order.time_window.deliver_by.isoformat(),
                    "priority": order.priority,
                    "created_at": order.created_at.isoformat(),
                },
            )
        logger.debug(f"Neo4j: logged order {order.order_id}")

    async def log_ranking(self, order_id: str, ranked: List[RankedDriver]) -> None:
        driver = await get_driver()
        async with driver.session() as session:
            for r in ranked:
                await session.run(
                    """
                    MERGE (o:Order  {order_id:  $order_id})
                    MERGE (d:Driver {driver_id: $driver_id})
                    CREATE (o)-[:RANKED {
                        score:          $score,
                        rank:           $rank,
                        eta_pickup_min: $eta,
                        ranked_at:      $now
                    }]->(d)
                    """,
                    {
                        "order_id": order_id,
                        "driver_id": r.driver_id,
                        "score": r.score,
                        "rank": r.rank,
                        "eta": r.eta_to_pickup_minutes,
                        "now": datetime.utcnow().isoformat(),
                    },
                )
        logger.debug(f"Neo4j: logged ranking for {len(ranked)} drivers on order {order_id}")

    async def log_dispatch_attempt(self, order_id: str, outcome: DispatchOutcome) -> None:
        driver = await get_driver()
        async with driver.session() as session:
            await session.run(
                """
                MERGE (o:Order  {order_id:  $order_id})
                MERGE (d:Driver {driver_id: $driver_id})
                CREATE (o)-[:DISPATCH_ATTEMPTED {
                    outcome:           $outcome,
                    sentiment_score:   $sentiment,
                    decline_reason:    $reason,
                    call_duration_s:   $duration,
                    called_at:         $timestamp
                }]->(d)
                """,
                {
                    "order_id": order_id,
                    "driver_id": outcome.driver_id,
                    "outcome": outcome.outcome,
                    "sentiment": outcome.sentiment_score,
                    "reason": outcome.decline_reason,
                    "duration": outcome.call_duration_seconds,
                    "timestamp": outcome.timestamp.isoformat(),
                },
            )

    async def log_assignment(self, order_id: str, outcome: DispatchOutcome) -> None:
        await self.log_dispatch_attempt(order_id, outcome)
        driver = await get_driver()
        async with driver.session() as session:
            await session.run(
                """
                MERGE (o:Order  {order_id:  $order_id})
                SET o.status = 'assigned', o.assigned_at = $now
                MERGE (d:Driver {driver_id: $driver_id})
                CREATE (o)-[:ASSIGNED_TO {assigned_at: $now}]->(d)
                """,
                {
                    "order_id": order_id,
                    "driver_id": outcome.driver_id,
                    "now": datetime.utcnow().isoformat(),
                },
            )
        logger.info(f"Neo4j: order {order_id} assigned to driver {outcome.driver_id}")

    async def log_dispatch_failed(self, order_id: str, reason: str) -> None:
        driver = await get_driver()
        async with driver.session() as session:
            await session.run(
                """
                MERGE (o:Order {order_id: $order_id})
                SET o.status = 'failed',
                    o.failure_reason = $reason,
                    o.failed_at = $now
                """,
                {
                    "order_id": order_id,
                    "reason": reason,
                    "now": datetime.utcnow().isoformat(),
                },
            )
        logger.warning(f"Neo4j: order {order_id} failed — {reason}")
