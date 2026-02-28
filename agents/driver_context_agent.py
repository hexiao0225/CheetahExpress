from typing import List, Optional, Dict, Any
import httpx
import structlog
from config import settings
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

    async def search_yutori_drivers(
        self,
        query: str,
        limit: int = 10,
        latitude: Optional[float] = None,
        longitude: Optional[float] = None,
        vehicle_type: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Read-only driver search against Yutori."""
        if not settings.enable_yutori_search:
            return {
                "enabled": False,
                "source": "yutori",
                "count": 0,
                "results": [],
                "message": "Yutori search is disabled. Set ENABLE_YUTORI_SEARCH=true.",
            }

        if not settings.yutori_api_key:
            return {
                "enabled": False,
                "source": "yutori",
                "count": 0,
                "results": [],
                "message": "Yutori API key is missing. Set YUTORI_API_KEY.",
            }

        location_hint = ""
        if latitude is not None and longitude is not None:
            location_hint = f" Current pickup coordinates: ({latitude}, {longitude})."
        vehicle_hint = f" Required vehicle type: {vehicle_type}." if vehicle_type else ""

        browsing_task = (
            f"Find up to {limit} delivery drivers that match this request: {query}."
            f"{vehicle_hint}{location_hint} "
            "Return concise candidate entries with fields: driver_name, driver_id, vehicle_type, "
            "location, reason, source_url."
        )

        payload: Dict[str, Any] = {
            "task": browsing_task,
            "start_url": "https://www.google.com",
            "max_steps": 20,
            "output_schema": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "driver_name": {"type": "string"},
                        "driver_id": {"type": "string"},
                        "vehicle_type": {"type": "string"},
                        "location": {"type": "string"},
                        "reason": {"type": "string"},
                        "source_url": {"type": "string"},
                    },
                },
            },
        }

        create_task_endpoint = f"{settings.yutori_base_url.rstrip('/')}/browsing/tasks"

        try:
            async with httpx.AsyncClient(timeout=20.0) as client:
                auth_header_options = [
                    {"X-API-Key": settings.yutori_api_key, "Content-Type": "application/json"},
                    {"X-Api-Key": settings.yutori_api_key, "Content-Type": "application/json"},
                    {"Authorization": f"Bearer {settings.yutori_api_key}", "Content-Type": "application/json"},
                ]

                create_data: Dict[str, Any] = {}
                last_error: Optional[str] = None
                selected_headers: Optional[Dict[str, str]] = None

                for headers in auth_header_options:
                    try:
                        response = await client.post(
                            create_task_endpoint,
                            headers=headers,
                            json=payload,
                        )
                        response.raise_for_status()
                        create_data = response.json()
                        selected_headers = headers
                        last_error = None
                        break
                    except httpx.HTTPStatusError as http_err:
                        error_body = http_err.response.text
                        last_error = (
                            f"HTTP {http_err.response.status_code} from Yutori: {error_body}"
                        )
                        if http_err.response.status_code not in (401, 403):
                            break

                if last_error is not None:
                    raise RuntimeError(last_error)

                task_id = create_data.get("task_id")
                view_url = create_data.get("view_url")
                status = create_data.get("status", "queued")

                status_data = create_data
                if task_id and selected_headers:
                    status_endpoint = f"{create_task_endpoint}/{task_id}"
                    try:
                        status_response = await client.get(status_endpoint, headers=selected_headers)
                        status_response.raise_for_status()
                        status_data = status_response.json()
                        status = status_data.get("status", status)
                        view_url = status_data.get("view_url", view_url)
                    except Exception:
                        pass

            results = status_data.get("structured_result") if isinstance(status_data, dict) else []
            if isinstance(results, dict):
                results = [results]
            elif not isinstance(results, list):
                results = []

            raw_result = status_data.get("result") if isinstance(status_data, dict) else None
            if not results and isinstance(raw_result, str) and raw_result.strip():
                results = [{"result": raw_result}]

            if not results and view_url:
                results = [
                    {
                        "task_id": task_id,
                        "status": status,
                        "view_url": view_url,
                    }
                ]

            if not isinstance(results, list):
                results = []

            return {
                "enabled": True,
                "source": "yutori_browsing_tasks",
                "count": len(results),
                "results": results,
                "message": (
                    "Browsing task queued. Open view_url for live progress and rerun search shortly."
                    if status in {"queued", "running"}
                    else None
                ),
            }
        except Exception as e:
            logger.error("Yutori driver search failed", error=str(e))
            return {
                "enabled": True,
                "source": "yutori_browsing_tasks",
                "count": 0,
                "results": [],
                "message": f"Yutori search failed: {str(e)}",
            }
