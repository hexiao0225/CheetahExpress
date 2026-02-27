"""
Compliance Check Agent — validates drivers against business rules.

Rules (matching the architecture spec):
  2.1  License valid and not expiring within 14 days
  2.2  Driver's vehicle type matches the order requirement
  2.3  Sufficient km budget remaining today (>= MIN_KM_BUDGET_REMAINING)
  2.4  Driver's shift window covers the full delivery time window

All compliance decisions are logged to Neo4j by the AuditLogger after this agent runs.
"""

import logging
from datetime import date
from typing import List

from models.driver import ComplianceResult, Driver
from models.order import Order

logger = logging.getLogger(__name__)

LICENSE_EXPIRY_BUFFER_DAYS = 14
MIN_KM_BUDGET_REMAINING = 20.0  # km


class ComplianceAgent:
    async def check_all(self, drivers: List[Driver], order: Order) -> List[ComplianceResult]:
        """
        Run all four compliance rules for every driver in the active pool.
        Returns one ComplianceResult per driver (eligible=True or eligible=False with reasons).
        """
        results = [self._check_driver(d, order) for d in drivers]

        eligible_count = sum(1 for r in results if r.eligible)
        logger.info(f"Compliance: {eligible_count}/{len(drivers)} drivers passed all rules")

        for r in results:
            if not r.eligible:
                logger.debug(f"Driver {r.driver_id} FAILED: {r.failure_reasons}")

        return results

    def _check_driver(self, driver: Driver, order: Order) -> ComplianceResult:
        failures: List[str] = []
        today = date.today()

        # Rule 2.1 — License validity
        days_remaining = (driver.license_expiry - today).days
        license_ok = days_remaining >= LICENSE_EXPIRY_BUFFER_DAYS
        if not license_ok:
            failures.append(
                f"License expires in {days_remaining}d (minimum {LICENSE_EXPIRY_BUFFER_DAYS}d buffer required)"
            )

        # Rule 2.2 — Vehicle type match
        vehicle_match = driver.vehicle_type.lower() == order.vehicle_type.value.lower()
        if not vehicle_match:
            failures.append(
                f"Vehicle mismatch: driver has '{driver.vehicle_type}', order requires '{order.vehicle_type.value}'"
            )

        # Rule 2.3 — km budget
        km_budget_ok = driver.km_budget_remaining_today >= MIN_KM_BUDGET_REMAINING
        if not km_budget_ok:
            failures.append(
                f"Insufficient km budget: {driver.km_budget_remaining_today:.1f}km remaining "
                f"(minimum {MIN_KM_BUDGET_REMAINING}km)"
            )

        # Rule 2.4 — Shift window covers delivery SLA
        shift_window_ok = (
            driver.shift_start <= order.time_window.pickup_by
            and driver.shift_end >= order.time_window.deliver_by
        )
        if not shift_window_ok:
            failures.append(
                f"Shift {driver.shift_start.strftime('%H:%M')}–{driver.shift_end.strftime('%H:%M')} "
                f"doesn't cover delivery window "
                f"({order.time_window.pickup_by.strftime('%H:%M')}–{order.time_window.deliver_by.strftime('%H:%M')})"
            )

        return ComplianceResult(
            driver_id=driver.driver_id,
            eligible=len(failures) == 0,
            failure_reasons=failures,
            license_days_remaining=days_remaining,
            vehicle_match=vehicle_match,
            km_budget_ok=km_budget_ok,
            shift_window_ok=shift_window_ok,
        )
