"""
Orchestrator Agent — coordinates the full Cheetah Express dispatch pipeline.

Uses GPT-4o to:
  - Parse and normalise potentially messy order webhook payloads
  - Handle edge cases and ambiguous fields before passing data downstream

Pipeline (deterministic, sequenced by the orchestrator):
  1. Parse order (GPT-4o)
  2. Fetch active drivers (Yutori via DriverContextAgent)
  3. Compliance check (ComplianceAgent)          ← pure Python rules
  4. Real-time routing / ETA (Google Maps)       ← SLA feasibility gate
  5. Rank eligible drivers (RankingEngine)
  6. Voice dispatch loop (Modulate)
  7. Log post-dispatch decisions to Neo4j (ranking + call outcomes)
"""

import json
import logging
from typing import Any, Dict

from openai import AsyncOpenAI

from agents.compliance import ComplianceAgent
from agents.driver_context import DriverContextAgent
from agents.ranking import RankingEngine
from agents.routing import RoutingAgent
from agents.voice_dispatch import VoiceDispatchAgent
from config import settings
from db.audit_logger import AuditLogger
from models.order import Order

logger = logging.getLogger(__name__)

ORDER_PARSE_SYSTEM_PROMPT = """
You are an order normalisation agent for Cheetah Express, a last-mile delivery platform.
Your only job is to extract and normalise delivery order data from a raw webhook payload.

Return ONLY a valid JSON object. No explanation, no markdown, no extra keys.

Required schema:
{
  "order_id": "string",
  "pickup": {"lat": <float>, "lng": <float>, "address": "<string or null>"},
  "dropoff": {"lat": <float>, "lng": <float>, "address": "<string or null>"},
  "time_window": {
    "pickup_by": "<ISO8601 datetime with timezone>",
    "deliver_by": "<ISO8601 datetime with timezone>"
  },
  "vehicle_type": "<one of: bike | motorcycle | car | van | truck>",
  "customer_info": {"name": "<string>", "phone": "<string>", "email": "<string or null>"},
  "package_description": "<string or null>",
  "priority": <integer 1–5, default 1>
}
""".strip()


class OrchestratorAgent:
    def __init__(self):
        self.openai = AsyncOpenAI(api_key=settings.openai_api_key)
        self.driver_context = DriverContextAgent()
        self.compliance = ComplianceAgent()
        self.routing = RoutingAgent()
        self.ranking = RankingEngine()
        self.voice = VoiceDispatchAgent()
        self.audit = AuditLogger()

    async def process_order(self, raw_payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Main entry point. Accepts a raw webhook payload and runs the full pipeline.
        Returns a summary dict with the dispatch outcome.
        """
        order_id = raw_payload.get("order_id", "unknown")
        logger.info(f"=== Cheetah Express: processing order {order_id} ===")

        # ── Step 0: Parse & normalise via GPT-4o ──────────────────────────────
        order = await self._parse_order(raw_payload)
        await self.audit.log_order(order)

        # ── Step 1: Fetch active driver pool (Yutori) ──────────────────────────
        all_drivers = await self.driver_context.get_active_drivers()
        logger.info(f"Active driver pool: {len(all_drivers)} drivers")

        if not all_drivers:
            await self.audit.log_dispatch_failed(order.order_id, "no_active_drivers")
            return {"status": "failed", "reason": "no_active_drivers", "order_id": order.order_id}

        # ── Step 2: Compliance check (pure Python rules) ──────────────────────
        compliance_results = await self.compliance.check_all(all_drivers, order)

        eligible_ids = {r.driver_id for r in compliance_results if r.eligible}
        eligible_drivers = [d for d in all_drivers if d.driver_id in eligible_ids]

        if not eligible_drivers:
            await self.audit.log_dispatch_failed(order.order_id, "no_eligible_drivers")
            return {"status": "failed", "reason": "no_eligible_drivers", "order_id": order.order_id}

        # ── Step 3: Routing — ETA + SLA feasibility (Google Maps) ──────────────
        routing_results = await self.routing.compute_etas(eligible_drivers, order)

        # ── Step 4: Rank eligible + SLA-feasible drivers ───────────────────────
        ranked_drivers = self.ranking.rank(all_drivers, compliance_results, routing_results)
        await self.audit.log_ranking(order.order_id, ranked_drivers)

        if not ranked_drivers:
            await self.audit.log_dispatch_failed(order.order_id, "no_sla_feasible_drivers")
            return {
                "status": "failed",
                "reason": "no_sla_feasible_drivers",
                "order_id": order.order_id,
            }

        # ── Step 5: Voice dispatch loop (Modulate) ─────────────────────────────
        outcome = await self.voice.dispatch(ranked_drivers, order)

        if outcome and outcome.outcome == "accepted":
            await self.audit.log_assignment(order.order_id, outcome)
            return {
                "status": "assigned",
                "order_id": order.order_id,
                "assigned_driver_id": outcome.driver_id,
                "calls_attempted": next(
                    (d.rank for d in ranked_drivers if d.driver_id == outcome.driver_id), None
                ),
            }

        await self.audit.log_dispatch_failed(order.order_id, "all_drivers_declined")
        return {
            "status": "failed",
            "reason": "all_drivers_declined",
            "order_id": order.order_id,
        }

    async def _parse_order(self, raw: Dict[str, Any]) -> Order:
        """Use GPT-4o to normalise a raw webhook payload into a typed Order."""
        response = await self.openai.chat.completions.create(
            model="gpt-4o",
            response_format={"type": "json_object"},
            messages=[
                {"role": "system", "content": ORDER_PARSE_SYSTEM_PROMPT},
                {
                    "role": "user",
                    "content": f"Normalise this order payload:\n{json.dumps(raw, indent=2)}",
                },
            ],
            temperature=0,
        )
        parsed = json.loads(response.choices[0].message.content)
        return Order(**parsed)

    async def close(self):
        await self.driver_context.close()
        await self.routing.close()
        await self.voice.close()
