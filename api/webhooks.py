"""
FastAPI route handlers.

POST /webhook/order      — order intake (fires dispatch pipeline as background task)
POST /webhook/modulate   — Modulate voice call outcome callback
GET  /audit/{order_id}  — full decision audit trail from Neo4j
GET  /health            — liveness check
"""

import logging
from typing import Any, Dict

from fastapi import APIRouter, BackgroundTasks, HTTPException, Request

from agents.orchestrator import OrchestratorAgent
from db.client import get_driver as get_neo4j_driver

logger = logging.getLogger(__name__)
router = APIRouter()

# Single orchestrator instance — reuses persistent HTTP clients
_orchestrator = OrchestratorAgent()


@router.post("/webhook/order", status_code=202)
async def order_intake(payload: Dict[str, Any], background_tasks: BackgroundTasks):
    """
    Receive a new delivery order and immediately queue the dispatch pipeline.
    Returns 202 Accepted so the caller doesn't wait for the full pipeline.
    """
    order_id = payload.get("order_id")
    if not order_id:
        raise HTTPException(status_code=400, detail="order_id is required")

    logger.info(f"Order intake: {order_id}")
    background_tasks.add_task(_orchestrator.process_order, payload)
    return {"status": "accepted", "order_id": order_id}


@router.post("/webhook/modulate")
async def modulate_callback(request: Request):
    """
    Receive async call-outcome callbacks from Modulate.
    TODO: Parse Modulate's callback schema and update call state.
          Enable this when switching from polling to webhook-based flow.
    """
    payload = await request.json()
    logger.info(f"Modulate callback: {payload}")
    # TODO: look up the pending call by call_id, resolve the asyncio.Event
    return {"status": "received"}


@router.get("/audit/{order_id}")
async def get_audit_trail(order_id: str):
    """
    Return the full dispatch audit graph for a given order.
    Shows compliance decisions, routing ETAs, ranking scores, and call outcomes.
    """
    neo4j = await get_neo4j_driver()
    async with neo4j.session() as session:
        result = await session.run(
            """
            MATCH (o:Order {order_id: $order_id})
            OPTIONAL MATCH (o)-[cc:COMPLIANCE_CHECKED]->(d:Driver)
            OPTIONAL MATCH (o)-[rc:ROUTING_COMPUTED]->(d)
            OPTIONAL MATCH (o)-[rk:RANKED]->(d)
            OPTIONAL MATCH (o)-[da:DISPATCH_ATTEMPTED]->(d)
            OPTIONAL MATCH (o)-[at:ASSIGNED_TO]->(assigned_driver:Driver)
            RETURN
                properties(o) AS order,
                collect(DISTINCT {driver_id: d.driver_id, data: properties(cc)}) AS compliance,
                collect(DISTINCT {driver_id: d.driver_id, data: properties(rc)}) AS routing,
                collect(DISTINCT {driver_id: d.driver_id, data: properties(rk)}) AS ranking,
                collect(DISTINCT {driver_id: d.driver_id, data: properties(da)}) AS calls,
                properties(assigned_driver) AS assigned_driver
            """,
            {"order_id": order_id},
        )
        record = await result.single()

    if not record:
        raise HTTPException(status_code=404, detail=f"Order '{order_id}' not found")

    return {
        "order": record["order"],
        "compliance_checks": record["compliance"],
        "routing_results": record["routing"],
        "ranking": record["ranking"],
        "dispatch_calls": record["calls"],
        "assigned_driver": record["assigned_driver"],
    }


@router.get("/health")
async def health():
    return {"status": "ok", "service": "cheetah-express"}
