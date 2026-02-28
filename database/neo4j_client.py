from neo4j import GraphDatabase, Driver
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import structlog
from config import settings

logger = structlog.get_logger()


class Neo4jClient:
    def __init__(self):
        self.driver: Optional[Driver] = None
        
    def connect(self):
        try:
            self.driver = GraphDatabase.driver(
                settings.neo4j_uri,
                auth=(settings.neo4j_user, settings.neo4j_password)
            )
            self.driver.verify_connectivity()
            logger.info("Connected to Neo4j", uri=settings.neo4j_uri)
            self._initialize_schema()
        except Exception as e:
            logger.error("Failed to connect to Neo4j — running without audit graph", error=str(e))
            self.driver = None
    
    def close(self):
        if self.driver:
            self.driver.close()
            logger.info("Neo4j connection closed")
    
    def _initialize_schema(self):
        with self.driver.session() as session:
            session.run("""
                CREATE CONSTRAINT order_id IF NOT EXISTS
                FOR (o:Order) REQUIRE o.order_id IS UNIQUE
            """)
            logger.info("Neo4j schema initialized")
    
    def _db_unavailable(self) -> bool:
        if not self.driver:
            logger.warning("Neo4j unavailable — skipping audit log")
            return True
        return False

    def get_driver_workload_today(self, driver_id: str) -> Dict[str, float]:
        if self._db_unavailable():
            return {"km_today": 0.0, "hours_today": 0.0}
        query = """
        MATCH (d:Driver {driver_id: $driver_id})-[a:ASSIGNED_TO]->(o:Order)
        WHERE date(o.created_at) = date()
        RETURN 
            COALESCE(SUM(a.distance_km), 0) as km_today,
            COALESCE(SUM(a.duration_hours), 0) as hours_today
        """
        with self.driver.session() as session:
            result = session.run(query, driver_id=driver_id)
            record = result.single()
            if record:
                return {
                    "km_today": record["km_today"],
                    "hours_today": record["hours_today"]
                }
            return {"km_today": 0.0, "hours_today": 0.0}
    
    def create_order_audit_graph(self, order_id: str, order_data: Dict[str, Any]) -> str:
        if self._db_unavailable():
            return order_id
        query = """
        MERGE (o:Order {order_id: $order_id})
        ON CREATE SET o.created_at = datetime()
        SET o.pickup_address = $pickup_address,
            o.pickup_latitude = $pickup_latitude,
            o.pickup_longitude = $pickup_longitude,
            o.dropoff_address = $dropoff_address,
            o.dropoff_latitude = $dropoff_latitude,
            o.dropoff_longitude = $dropoff_longitude,
            o.vehicle_type = $vehicle_type,
            o.time_window_start = datetime($time_window_start),
            o.time_window_end = datetime($time_window_end),
            o.status = 'processing',
            o.status_message = '',
            o.assigned_driver_id = null,
            o.updated_at = datetime()
        WITH o
        OPTIONAL MATCH (o)-[r1:COMPLIANCE_CHECK|RANKED|CALLED]->(:Driver)
        DELETE r1
        WITH o
        OPTIONAL MATCH (:Driver)-[r2:ASSIGNED_TO]->(o)
        DELETE r2
        RETURN o.order_id as order_id
        """
        with self.driver.session() as session:
            result = session.run(query, **order_data)
            record = result.single()
            logger.info("Order audit graph created", order_id=order_id)
            return record["order_id"]
    
    def log_compliance_decision(self, order_id: str, driver_id: str,
                               compliance_result: Dict[str, Any]) -> None:
        if self._db_unavailable():
            return
        query = """
        MATCH (o:Order {order_id: $order_id})
        MERGE (d:Driver {driver_id: $driver_id})
        CREATE (o)-[r:COMPLIANCE_CHECK]->(d)
        SET r.is_compliant = $is_compliant,
            r.reasons = $reasons,
            r.checks = $checks,
            r.timestamp = datetime()
        """
        with self.driver.session() as session:
            session.run(
                query,
                order_id=order_id,
                driver_id=driver_id,
                is_compliant=compliance_result["is_compliant"],
                reasons=compliance_result["reasons"],
                checks=str(compliance_result["checks"])
            )
    
    def log_ranking_decision(self, order_id: str, rankings: List[Dict[str, Any]]) -> None:
        for idx, ranking in enumerate(rankings):
            query = """
            MATCH (o:Order {order_id: $order_id})
            MATCH (d:Driver {driver_id: $driver_id})
            CREATE (o)-[r:RANKED]->(d)
            SET r.rank = $rank,
                r.score = $score,
                r.eta_minutes = $eta_minutes,
                r.reasoning = $reasoning,
                r.timestamp = datetime()
            """
            with self.driver.session() as session:
                session.run(
                    query,
                    order_id=order_id,
                    driver_id=ranking["driver_id"],
                    rank=idx + 1,
                    score=ranking["score"],
                    eta_minutes=ranking.get("eta_to_pickup_minutes", 0),
                    reasoning=ranking.get("reasoning", "")
                )
    
    def log_voice_call_outcome(self, order_id: str, driver_id: str, 
                              call_result: Dict[str, Any]) -> None:
        query = """
        MATCH (o:Order {order_id: $order_id})
        MATCH (d:Driver {driver_id: $driver_id})
        CREATE (o)-[r:CALLED]->(d)
        SET r.outcome = $outcome,
            r.sentiment_score = $sentiment_score,
            r.decline_reason = $decline_reason,
            r.transcript = $transcript,
            r.call_duration_seconds = $call_duration_seconds,
            r.timestamp = datetime()
        """
        with self.driver.session() as session:
            session.run(
                query,
                order_id=order_id,
                driver_id=driver_id,
                outcome=call_result["outcome"],
                sentiment_score=call_result.get("sentiment_score"),
                decline_reason=call_result.get("decline_reason"),
                transcript=call_result.get("transcript"),
                call_duration_seconds=call_result.get("call_duration_seconds")
            )
    
    def log_assignment(self, order_id: str, driver_id: str, 
                      distance_km: float, duration_hours: float) -> None:
        query = """
        MATCH (o:Order {order_id: $order_id})
        MATCH (d:Driver {driver_id: $driver_id})
        CREATE (d)-[r:ASSIGNED_TO]->(o)
        SET r.distance_km = $distance_km,
            r.duration_hours = $duration_hours,
            r.assigned_at = datetime(),
            o.status = 'driver_assigned',
            o.assigned_driver_id = $driver_id
        """
        with self.driver.session() as session:
            session.run(
                query,
                order_id=order_id,
                driver_id=driver_id,
                distance_km=distance_km,
                duration_hours=duration_hours
            )
            logger.info("Assignment logged", order_id=order_id, driver_id=driver_id)
    
    def update_order_status(self, order_id: str, status: str, message: str = "") -> None:
        query = """
        MATCH (o:Order {order_id: $order_id})
        SET o.status = $status,
            o.status_message = $message,
            o.updated_at = datetime()
        """
        with self.driver.session() as session:
            session.run(query, order_id=order_id, status=status, message=message)


neo4j_client = Neo4jClient()
