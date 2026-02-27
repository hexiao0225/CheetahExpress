"""
Cheetah Express — FastAPI application entry point.

Start locally:
  uvicorn main:app --reload --port 8000

Or via Python:
  python main.py
"""

import logging
from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI

from api.webhooks import router
from config import settings
from db.client import close_driver
from db.schema import init_schema

logging.basicConfig(
    level=getattr(logging, settings.log_level.upper()),
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("🐆 Cheetah Express starting up...")
    await init_schema()
    logger.info("Ready — waiting for orders.")
    yield
    logger.info("Shutting down...")
    await close_driver()


app = FastAPI(
    title="Cheetah Express",
    description="AI-powered last-mile logistics dispatch",
    version="0.1.0",
    lifespan=lifespan,
)

app.include_router(router)


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=settings.port, reload=True)
