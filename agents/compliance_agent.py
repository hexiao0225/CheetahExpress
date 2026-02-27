from typing import List, Dict, Any
import structlog
from models import DriverInfo, ComplianceResult, VehicleType, OrderRequest
from database.neo4j_client import neo4j_client
from datetime import datetime

logger = structlog.get_logger()


class ComplianceAgent:
    
    def __init__(self):
        self.neo4j = neo4j_client
        self.max_km_per_day = 300
        self.max_hours_per_day = 10
        self.min_license_buffer_days = 14
        self.min_km_remaining = 20
        self.min_hours_remaining = 1
    
    async def check_compliance(
        self, 
        drivers: List[DriverInfo], 
        order: OrderRequest
    ) -> List[ComplianceResult]:
        compliance_results = []
        
        for driver in drivers:
            compliance_data = self._check_driver_compliance_in_memory(
                driver=driver,
                vehicle_type=order.vehicle_type.value,
                delivery_time=order.time_window.start
            )
            
            result = ComplianceResult(
                driver_id=driver.driver_id,
                is_compliant=compliance_data["is_compliant"],
                reasons=compliance_data["reasons"],
                checks=compliance_data["checks"]
            )
            
            compliance_results.append(result)
            
            self.neo4j.log_compliance_decision(
                order_id=order.order_id,
                driver_id=driver.driver_id,
                compliance_result=compliance_data
            )
            
            logger.info(
                "Compliance check completed",
                driver_id=driver.driver_id,
                is_compliant=result.is_compliant,
                reasons=result.reasons
            )
        
        compliant_count = sum(1 for r in compliance_results if r.is_compliant)
        logger.info(
            "Compliance checks completed for all drivers",
            total_drivers=len(drivers),
            compliant_drivers=compliant_count
        )
        
        return compliance_results
    
    def _check_driver_compliance_in_memory(
        self, 
        driver: DriverInfo, 
        vehicle_type: str, 
        delivery_time: datetime
    ) -> Dict[str, Any]:
        checks = {}
        reasons = []
        
        days_until_expiry = (driver.license_expiry - datetime.now()).days
        checks["license_valid"] = days_until_expiry > self.min_license_buffer_days
        if not checks["license_valid"]:
            reasons.append(f"License expires in {days_until_expiry} days (< {self.min_license_buffer_days} day buffer)")
        
        checks["vehicle_type_match"] = driver.vehicle_type.value == vehicle_type
        if not checks["vehicle_type_match"]:
            reasons.append(f"Vehicle type mismatch: need {vehicle_type}, driver has {driver.vehicle_type.value}")
        
        workload = self.neo4j.get_driver_workload_today(driver.driver_id)
        remaining_km = self.max_km_per_day - workload["km_today"]
        checks["km_budget_available"] = remaining_km > self.min_km_remaining
        if not checks["km_budget_available"]:
            reasons.append(f"Insufficient km budget: {remaining_km:.1f} km remaining (need > {self.min_km_remaining} km)")
        
        remaining_hours = self.max_hours_per_day - workload["hours_today"]
        checks["hours_budget_available"] = remaining_hours > self.min_hours_remaining
        if not checks["hours_budget_available"]:
            reasons.append(f"Insufficient hours budget: {remaining_hours:.1f} hours remaining (need > {self.min_hours_remaining} hr)")
        
        delivery_hour = delivery_time.hour
        shift_start = 6
        shift_end = 18
        checks["shift_window_covers_delivery"] = shift_start <= delivery_hour < shift_end
        if not checks["shift_window_covers_delivery"]:
            reasons.append(f"Delivery at {delivery_hour}:00 outside default shift {shift_start}:00-{shift_end}:00")
        
        is_compliant = all(checks.values())
        
        return {
            "is_compliant": is_compliant,
            "reasons": reasons if not is_compliant else ["All compliance checks passed"],
            "checks": checks,
            "remaining_km": remaining_km,
            "remaining_hours": remaining_hours
        }
    
    def filter_compliant_drivers(
        self, 
        drivers: List[DriverInfo], 
        compliance_results: List[ComplianceResult]
    ) -> List[DriverInfo]:
        compliant_driver_ids = {
            r.driver_id for r in compliance_results if r.is_compliant
        }
        
        compliant_drivers = [
            d for d in drivers if d.driver_id in compliant_driver_ids
        ]
        
        logger.info(
            "Filtered compliant drivers",
            total=len(drivers),
            compliant=len(compliant_drivers)
        )
        
        return compliant_drivers
