from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import structlog
from config import settings
from models import OrderRequest, DispatchResult
from agents.orchestrator_agent import OrchestratorAgent
from database.neo4j_client import neo4j_client
import uvicorn

structlog.configure(
    processors=[
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.add_log_level,
        structlog.processors.JSONRenderer()
    ]
)

logger = structlog.get_logger()


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("🐆 Cheetah Express starting up...")
    neo4j_client.connect()
    yield
    logger.info("🐆 Cheetah Express shutting down...")
    neo4j_client.close()


app = FastAPI(
    title="Cheetah Express 🐆",
    description="AI-Powered Delivery Dispatch System with Multi-Agent Orchestration",
    version="1.0.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

orchestrator = OrchestratorAgent()


@app.get("/")
async def root():
    return {
        "service": "Cheetah Express 🐆",
        "status": "running",
        "version": "1.0.0",
        "description": "AI-Powered Delivery Dispatch System"
    }


@app.get("/health")
async def health_check():
    try:
        neo4j_client.driver.verify_connectivity()
        return {
            "status": "healthy",
            "database": "connected",
            "service": "operational"
        }
    except Exception as e:
        logger.error("Health check failed", error=str(e))
        raise HTTPException(status_code=503, detail="Service unhealthy")


@app.post("/api/v1/orders", response_model=DispatchResult)
async def create_order(order: OrderRequest):
    logger.info(
        "Received new order",
        order_id=order.order_id,
        pickup=order.pickup.address,
        dropoff=order.dropoff.address
    )
    
    try:
        result = await orchestrator.process_order(order)
        return result
    except Exception as e:
        logger.error("Order processing failed", order_id=order.order_id, error=str(e))
        raise HTTPException(
            status_code=500,
            detail=f"Failed to process order: {str(e)}"
        )


@app.post("/api/v1/orders/async", response_model=dict)
async def create_order_async(order: OrderRequest, background_tasks: BackgroundTasks):
    logger.info(
        "Received new order (async)",
        order_id=order.order_id
    )
    
    background_tasks.add_task(orchestrator.process_order, order)
    
    return {
        "order_id": order.order_id,
        "status": "processing",
        "message": "Order accepted and being processed in background"
    }


@app.get("/api/v1/orders/{order_id}")
async def get_order_status(order_id: str):
    try:
        with neo4j_client.driver.session() as session:
            result = session.run(
                "MATCH (o:Order {order_id: $order_id}) RETURN o",
                order_id=order_id
            )
            record = result.single()
            
            if not record:
                raise HTTPException(status_code=404, detail="Order not found")
            
            order = record["o"]
            return {
                "order_id": order["order_id"],
                "status": order.get("status", "unknown"),
                "assigned_driver_id": order.get("assigned_driver_id"),
                "created_at": order.get("created_at"),
                "updated_at": order.get("updated_at")
            }
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to fetch order status", order_id=order_id, error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v1/mock/orders")
async def get_mock_orders():
    from mock_data import get_all_mock_orders
    orders = get_all_mock_orders()
    return {
        "count": len(orders),
        "orders": orders
    }


@app.post("/api/v1/mock/orders/{order_id}")
async def submit_mock_order(order_id: str):
    from mock_data import get_mock_order
    mock_order_data = get_mock_order(order_id)
    
    if not mock_order_data:
        raise HTTPException(status_code=404, detail=f"Mock order {order_id} not found")
    
    order = OrderRequest(**mock_order_data)
    
    logger.info(
        "Processing mock order",
        order_id=order.order_id,
        pickup=order.pickup.address,
        dropoff=order.dropoff.address
    )
    
    try:
        result = await orchestrator.process_order(order)
        return result
    except Exception as e:
        logger.error("Mock order processing failed", order_id=order.order_id, error=str(e))
        raise HTTPException(
            status_code=500,
            detail=f"Failed to process mock order: {str(e)}"
        )


@app.get("/api/v1/orders/{order_id}/audit")
async def get_order_audit_trail(order_id: str):
    try:
        with neo4j_client.driver.session() as session:
            result = session.run("""
                MATCH (o:Order {order_id: $order_id})
                OPTIONAL MATCH (o)-[cc:COMPLIANCE_CHECK]->(d1:Driver)
                OPTIONAL MATCH (o)-[r:RANKED]->(d2:Driver)
                OPTIONAL MATCH (o)-[c:CALLED]->(d3:Driver)
                OPTIONAL MATCH (d4:Driver)-[a:ASSIGNED_TO]->(o)
                RETURN o,
                       collect(DISTINCT {driver_id: d1.driver_id, is_compliant: cc.is_compliant, reasons: cc.reasons}) as compliance_checks,
                       collect(DISTINCT {driver_id: d2.driver_id, rank: r.rank, score: r.score, reasoning: r.reasoning}) as rankings,
                       collect(DISTINCT {driver_id: d3.driver_id, outcome: c.outcome, sentiment: c.sentiment_score, decline_reason: c.decline_reason, transcript: c.transcript}) as calls,
                       collect(DISTINCT {driver_id: d4.driver_id, distance_km: a.distance_km, duration_hours: a.duration_hours}) as assignments
            """, order_id=order_id)
            
            record = result.single()
            
            if not record or not record["o"]:
                raise HTTPException(status_code=404, detail="Order not found")
            
            # Get assigned driver location from mock data for GPS tracking
            assigned_driver_location = None
            assignments = [a for a in record["assignments"] if a.get("driver_id")]
            if assignments:
                from agents.driver_context_agent import DriverContextAgent
                driver_agent = DriverContextAgent()
                driver = await driver_agent.get_driver_by_id(assignments[0]["driver_id"])
                if driver:
                    assigned_driver_location = {
                        "driver_id": driver.driver_id,
                        "name": driver.name,
                        "phone": driver.phone,
                        "vehicle_type": driver.vehicle_type.value,
                        "license_number": driver.license_number,
                        "license_expiry": driver.license_expiry.isoformat(),
                        "is_available": driver.is_available,
                        "latitude": driver.current_location.latitude,
                        "longitude": driver.current_location.longitude,
                        "address": driver.current_location.address
                    }
            
            return {
                "order_id": order_id,
                "order_details": dict(record["o"]),
                "compliance_checks": [c for c in record["compliance_checks"] if c.get("driver_id")],
                "rankings": [r for r in record["rankings"] if r.get("driver_id")],
                "voice_calls": [c for c in record["calls"] if c.get("driver_id")],
                "assignments": [a for a in record["assignments"] if a.get("driver_id")],
                "driver_location": assigned_driver_location
            }
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to fetch audit trail", order_id=order_id, error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v1/orders_graph")
async def get_all_orders_graph():
    try:
        with neo4j_client.driver.session() as session:
            result = session.run("""
                MATCH (o:Order)
                OPTIONAL MATCH (d:Driver)-[a:ASSIGNED_TO]->(o)
                RETURN o.order_id as order_id,
                       o.status as status,
                       d.driver_id as driver_id,
                       a.distance_km as distance_km,
                       a.duration_hours as duration_hours,
                       a.assigned_at as assigned_at
                ORDER BY o.created_at DESC
            """)
            rows = [dict(record) for record in result]

        from agents.driver_context_agent import DriverContextAgent

        driver_agent = DriverContextAgent()
        all_drivers = await driver_agent.get_active_drivers()
        driver_name_cache = {}

        for row in rows:
            driver_id = row.get("driver_id")
            if driver_id and driver_id not in driver_name_cache:
                driver = await driver_agent.get_driver_by_id(driver_id)
                driver_name_cache[driver_id] = driver.name if driver else driver_id

            if driver_id:
                row["driver_name"] = driver_name_cache.get(driver_id, driver_id)
            else:
                row["driver_name"] = None

            if row.get("assigned_at") is not None:
                row["assigned_at"] = str(row["assigned_at"])

        return {
            "count": len(rows),
            "orders": rows,
            "drivers": [
                {
                    "driver_id": driver.driver_id,
                    "driver_name": driver.name,
                }
                for driver in all_drivers
            ],
        }
    except Exception as e:
        logger.error("Failed to fetch all orders graph", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))




if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=settings.port,
        reload=True,
        log_level=settings.log_level.lower()
    )
