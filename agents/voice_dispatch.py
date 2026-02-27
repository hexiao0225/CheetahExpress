"""
Voice Dispatch Agent — calls drivers in ranked order via the Modulate Voice API.

Flow:
  For each driver in ranked list:
    1. POST to Modulate to initiate a call with a personalised script
    2. Poll Modulate for call status until completed or timed out
    3. If accepted → return outcome, end loop
    4. If declined / no answer → log and move to next driver

TODO: Adapt endpoint paths and payload schemas to Modulate's actual API docs.
      Current implementation mirrors common voice AI API patterns (Bland / Retell style).
      For production, replace polling with Modulate's webhook callback.
"""

import asyncio
import logging
from typing import List, Optional

import httpx

from config import settings
from models.driver import DispatchOutcome, RankedDriver
from models.order import Order

logger = logging.getLogger(__name__)

CALL_POLL_INTERVAL_S = 3   # seconds between status polls
CALL_TIMEOUT_S = 120       # give up on a single call after 2 minutes


class VoiceDispatchAgent:
    def __init__(self):
        self.client = httpx.AsyncClient(
            base_url=settings.modulate_base_url,
            headers={"Authorization": f"Bearer {settings.modulate_api_key}"},
            timeout=30.0,
        )

    async def dispatch(
        self, ranked_drivers: List[RankedDriver], order: Order
    ) -> Optional[DispatchOutcome]:
        """
        Attempt voice dispatch in ranked order.
        Returns the DispatchOutcome of the first driver who accepts, or None.
        """
        for driver in ranked_drivers:
            logger.info(
                f"[Dispatch] Calling rank #{driver.rank}: {driver.name} ({driver.driver_id})"
            )
            outcome = await self._call_driver(driver, order)

            if outcome.outcome == "accepted":
                logger.info(f"Driver {driver.driver_id} ACCEPTED order {order.order_id}")
                return outcome

            logger.info(
                f"Driver {driver.driver_id} {outcome.outcome.upper()} — "
                f"reason: {outcome.decline_reason or 'none given'}"
            )

        logger.warning(
            f"All {len(ranked_drivers)} drivers declined or were unreachable "
            f"for order {order.order_id}"
        )
        return None

    async def _call_driver(self, driver: RankedDriver, order: Order) -> DispatchOutcome:
        script = self._build_script(driver, order)
        try:
            # TODO: Replace with Modulate's actual initiate-call endpoint + payload
            response = await self.client.post(
                "/calls",
                json={
                    "to": driver.phone,
                    "from": settings.modulate_caller_number,
                    "script": script,
                    "metadata": {
                        "order_id": order.order_id,
                        "driver_id": driver.driver_id,
                    },
                    # Webhook alternative to polling — uncomment when ready:
                    # "webhook_url": f"{settings.webhook_base_url}/webhook/modulate",
                },
            )
            response.raise_for_status()
            call_id = response.json()["call_id"]
            logger.info(f"Call initiated: call_id={call_id} for driver {driver.driver_id}")
            return await self._poll_outcome(call_id, driver.driver_id)

        except httpx.HTTPError as e:
            logger.error(f"Modulate API error for driver {driver.driver_id}: {e}")
            return DispatchOutcome(
                driver_id=driver.driver_id,
                outcome="error",
                decline_reason=str(e),
            )

    async def _poll_outcome(self, call_id: str, driver_id: str) -> DispatchOutcome:
        """
        Poll Modulate until the call reaches a terminal state.
        TODO: Replace with webhook handler for production.
        """
        elapsed = 0
        while elapsed < CALL_TIMEOUT_S:
            await asyncio.sleep(CALL_POLL_INTERVAL_S)
            elapsed += CALL_POLL_INTERVAL_S
            try:
                # TODO: Adapt to Modulate's actual call-status endpoint
                resp = await self.client.get(f"/calls/{call_id}")
                resp.raise_for_status()
                data = resp.json()

                if data["status"] in ("completed", "failed", "no_answer"):
                    return DispatchOutcome(
                        driver_id=driver_id,
                        # TODO: Map Modulate's response fields to these fields
                        outcome=data.get("driver_response", "no_answer"),
                        sentiment_score=data.get("sentiment", {}).get("score"),
                        decline_reason=data.get("decline_reason"),
                        call_duration_seconds=data.get("duration_seconds"),
                    )
            except httpx.HTTPError as e:
                logger.warning(f"Poll error for call {call_id}: {e}")

        logger.warning(f"Call {call_id} timed out after {CALL_TIMEOUT_S}s")
        return DispatchOutcome(driver_id=driver_id, outcome="no_answer")

    def _build_script(self, driver: RankedDriver, order: Order) -> str:
        pickup_label = order.pickup.address or f"{order.pickup.lat:.4f}, {order.pickup.lng:.4f}"
        dropoff_label = order.dropoff.address or f"{order.dropoff.lat:.4f}, {order.dropoff.lng:.4f}"

        return (
            f"You are a dispatch coordinator for Cheetah Express, a fast delivery service. "
            f"You are calling {driver.name} to offer them a delivery assignment. "
            f"Be professional, friendly, and brief.\n\n"
            f"Offer the following delivery:\n"
            f"- Pickup: {pickup_label}\n"
            f"- Dropoff: {dropoff_label}\n"
            f"- Pickup by: {order.time_window.pickup_by.strftime('%I:%M %p')}\n"
            f"- Deliver by: {order.time_window.deliver_by.strftime('%I:%M %p')}\n"
            f"- Your ETA to pickup: approximately {driver.eta_to_pickup_minutes:.0f} minutes\n\n"
            f"Ask clearly whether they accept or decline.\n"
            f"If accepted: confirm the pickup address and thank them.\n"
            f"If declined: acknowledge politely and briefly ask for the reason."
        )

    async def close(self):
        await self.client.aclose()
