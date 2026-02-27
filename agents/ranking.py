"""
Ranking Engine — scores and sorts the eligible, SLA-feasible driver pool.

Score formula (0–100):
  score = 0.50 × eta_score          (lower pickup ETA → higher score)
        + 0.25 × km_budget_score     (more km remaining → higher score)
        + 0.25 × license_buffer_score (farther from expiry → higher score)

Each factor is normalised to [0, 1] before weighting.
Tie-breaking is implicit in the floating-point score.
"""

import logging
from datetime import date
from typing import List

from models.driver import ComplianceResult, Driver, RankedDriver, RoutingResult

logger = logging.getLogger(__name__)

# Score weights — must sum to 1.0
WEIGHT_ETA = 0.50
WEIGHT_KM_BUDGET = 0.25
WEIGHT_LICENSE_BUFFER = 0.25

# Normalisation caps
MAX_ETA_MINUTES = 120.0
MAX_KM_BUDGET = 300.0
MAX_LICENSE_BUFFER_DAYS = 365.0


class RankingEngine:
    def rank(
        self,
        drivers: List[Driver],
        compliance_results: List[ComplianceResult],
        routing_results: List[RoutingResult],
    ) -> List[RankedDriver]:
        """
        Returns drivers sorted descending by score.
        Only includes drivers who are both eligible (compliance) and fits_sla (routing).
        """
        compliance_map = {r.driver_id: r for r in compliance_results}
        routing_map = {r.driver_id: r for r in routing_results}

        candidates: List[RankedDriver] = []
        for driver in drivers:
            compliance = compliance_map.get(driver.driver_id)
            routing = routing_map.get(driver.driver_id)

            if not compliance or not compliance.eligible:
                continue
            if not routing or not routing.fits_sla:
                continue

            score = self._score(driver, routing)
            candidates.append(
                RankedDriver(
                    driver_id=driver.driver_id,
                    name=driver.name,
                    phone=driver.phone,
                    score=score,
                    rank=0,  # assigned below after sort
                    eta_to_pickup_minutes=routing.eta_to_pickup_minutes,
                    eta_total_trip_minutes=routing.eta_total_trip_minutes,
                    compliance=compliance,
                    routing=routing,
                )
            )

        candidates.sort(key=lambda d: d.score, reverse=True)
        for i, d in enumerate(candidates):
            d.rank = i + 1

        logger.info(f"Ranked {len(candidates)} eligible + SLA-feasible drivers")
        if candidates:
            top = candidates[0]
            logger.info(
                f"Top driver: {top.driver_id} — score={top.score:.1f}, "
                f"ETA={top.eta_to_pickup_minutes:.1f}min"
            )
        return candidates

    def _score(self, driver: Driver, routing: RoutingResult) -> float:
        today = date.today()
        days_until_expiry = (driver.license_expiry - today).days

        eta_norm = 1.0 - min(routing.eta_to_pickup_minutes, MAX_ETA_MINUTES) / MAX_ETA_MINUTES
        km_norm = min(driver.km_budget_remaining_today, MAX_KM_BUDGET) / MAX_KM_BUDGET
        license_norm = min(days_until_expiry, MAX_LICENSE_BUFFER_DAYS) / MAX_LICENSE_BUFFER_DAYS

        return round(
            (WEIGHT_ETA * eta_norm + WEIGHT_KM_BUDGET * km_norm + WEIGHT_LICENSE_BUFFER * license_norm)
            * 100,
            2,
        )
