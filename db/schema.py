"""
Neo4j schema initialisation — constraints and indexes.
Run once at application startup via init_schema().

Graph model:
  Nodes:   Order, Driver
  Edges:   COMPLIANCE_CHECKED, ROUTING_COMPUTED, RANKED,
           DISPATCH_ATTEMPTED, ASSIGNED_TO
"""

import logging

from db.client import get_driver

logger = logging.getLogger(__name__)

_SCHEMA_STATEMENTS = [
    # Uniqueness constraints (also create backing indexes)
    "CREATE CONSTRAINT order_id IF NOT EXISTS FOR (o:Order) REQUIRE o.order_id IS UNIQUE",
    "CREATE CONSTRAINT driver_id IF NOT EXISTS FOR (d:Driver) REQUIRE d.driver_id IS UNIQUE",
    # Additional indexes for common query patterns
    "CREATE INDEX order_status IF NOT EXISTS FOR (o:Order) ON (o.status)",
    "CREATE INDEX order_created IF NOT EXISTS FOR (o:Order) ON (o.created_at)",
]


async def init_schema() -> None:
    driver = await get_driver()
    async with driver.session() as session:
        for stmt in _SCHEMA_STATEMENTS:
            try:
                await session.run(stmt)
                logger.debug(f"Schema: {stmt[:70]}...")
            except Exception as e:
                # Constraint/index may already exist — safe to ignore
                logger.debug(f"Schema statement skipped (likely already exists): {e}")
    logger.info("Neo4j schema ready")
