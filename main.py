from fastapi import FastAPI, HTTPException, BackgroundTasks, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import asyncio
import io
import os
import tempfile
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


def _get_demo_call_context():
    """Shared demo driver/order/ranking for demo endpoints."""
    from mock_data import get_mock_order, MOCK_DRIVERS
    from models import RankingScore

    driver = next((d for d in MOCK_DRIVERS if d.driver_id == "DRV001"), MOCK_DRIVERS[0])
    order = OrderRequest(**get_mock_order("ORD002"))
    ranking = RankingScore(
        driver_id=driver.driver_id,
        score=95.0,
        eta_to_pickup_minutes=8.0,
        total_trip_time_minutes=25.0,
        vehicle_match=True,
        license_expiry_buffer_days=365,
        remaining_km_budget=280.0,
        reasoning="Demo call",
    )
    return driver, order, ranking


@app.get("/api/v1/demo/call/script")
async def get_demo_call_script():
    """Return the call script and driver/order info for the live demo (browser TTS + mic)."""
    from agents.voice_dispatch_agent import VoiceDispatchAgent

    driver, order, ranking = _get_demo_call_context()
    agent = VoiceDispatchAgent()
    script = agent._generate_call_script(driver, order, ranking)
    return {
        "script": script,
        "driver_name": driver.name,
        "driver_id": driver.driver_id,
        "order_id": order.order_id,
    }


@app.post("/api/v1/demo/call/transcribe")
async def transcribe_demo_call_audio(audio: UploadFile = File(...)):
    """Accept recorded audio from the browser (WAV or WebM), transcribe via Velma-2, return outcome + response message."""
    from agents.voice_dispatch_agent import VoiceDispatchAgent
    from concurrent.futures import ThreadPoolExecutor

    driver, _order, _ranking = _get_demo_call_context()
    content = await audio.read()
    if not content:
        raise HTTPException(status_code=400, detail="No audio data received")

    filename = (audio.filename or "").lower()
    content_type = (audio.content_type or "").lower()
    is_webm = "webm" in filename or "webm" in content_type
    is_ogg = "ogg" in filename or "ogg" in content_type

    wav_path = None
    try:
        if is_webm or is_ogg:
            try:
                from pydub import AudioSegment
                fmt = "webm" if is_webm else "ogg"
                seg = AudioSegment.from_file(io.BytesIO(content), format=fmt)
                with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
                    seg.export(f.name, format="wav")
                    wav_path = f.name
            except Exception as e:
                logger.warning("Could not convert to WAV (install ffmpeg for WebM/OGG)", error=str(e))
                raise HTTPException(
                    status_code=400,
                    detail="WebM/OGG conversion failed. Install ffmpeg or record in WAV.",
                ) from e
        else:
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
                f.write(content)
                wav_path = f.name

        agent = VoiceDispatchAgent()
        loop = asyncio.get_event_loop()
        with ThreadPoolExecutor(max_workers=1) as executor:
            result = await loop.run_in_executor(
                executor,
                agent.process_user_audio,
                wav_path,
                driver.name,
            )
        return {
            "order_id": _order.order_id,
            "driver_id": driver.driver_id,
            "driver_name": driver.name,
            "transcript": result["transcript"],
            "outcome": result["outcome"],
            "decline_reason": result.get("decline_reason"),
            "sentiment_score": result["sentiment_score"],
            "response_message": result["response_message"],
        }
    finally:
        if wav_path:
            try:
                os.unlink(wav_path)
            except Exception:
                pass


@app.post("/api/v1/demo/call")
async def trigger_demo_call():
    """Place a real Modulate voice call to DRV001 for ORD002 — no orchestration, no DB (server mic)."""
    from agents.voice_dispatch_agent import VoiceDispatchAgent

    driver, order, ranking = _get_demo_call_context()
    logger.info("Demo call triggered", driver_id=driver.driver_id, phone=driver.phone)

    try:
        result = await VoiceDispatchAgent()._call_driver(driver, order, ranking)
        return {
            "order_id": order.order_id,
            "driver_id": result.driver_id,
            "driver_name": driver.name,
            "phone": driver.phone,
            "outcome": result.outcome.value,
            "sentiment_score": result.sentiment_score,
            "decline_reason": result.decline_reason,
            "transcript": result.transcript,
            "call_duration_seconds": result.call_duration_seconds,
        }
    except Exception as e:
        logger.error("Demo call failed", error=str(e))
        raise HTTPException(status_code=500, detail=f"Demo call failed: {str(e)}")


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
                       collect(DISTINCT {driver_id: d3.driver_id, outcome: c.outcome, sentiment: c.sentiment_score, decline_reason: c.decline_reason}) as calls,
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




if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=settings.port,
        reload=True,
        log_level=settings.log_level.lower()
    )
