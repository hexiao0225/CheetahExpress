from typing import List
import structlog
from models import DriverInfo

logger = structlog.get_logger()


class DriverContextAgent:
    """Agent for managing driver data - uses mock San Francisco drivers for GPS tracking"""
    
    def __init__(self):
        pass
    
    async def get_active_drivers(self) -> List[DriverInfo]:
        """Return mock drivers with San Francisco locations for GPS tracking"""
        from mock_data import get_mock_drivers
        drivers = get_mock_drivers()
        logger.info("Retrieved mock drivers with SF locations", count=len(drivers))
        return drivers
    
    async def get_driver_by_id(self, driver_id: str) -> DriverInfo | None:
        """Get a specific driver by ID from mock data"""
        from mock_data import get_mock_drivers
        drivers = get_mock_drivers()
        
        for driver in drivers:
            if driver.driver_id == driver_id:
                logger.info("Retrieved driver by ID", driver_id=driver_id)
                return driver
        
        logger.warning("Driver not found", driver_id=driver_id)
        return None
