import asyncio
import logging
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .config import settings
from .database import init_db
from .routers import products, suggestions
from .task_queue.worker import process_suggestions

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    # 1. Initialize database & tables
    logger.info("Initializing database...")
    await init_db()

    # 2. Start reactive loop worker in background
    logger.info("Starting background suggestion worker...")
    worker_task = asyncio.create_task(process_suggestions())

    yield

    # 3. Clean graceful shutdown
    logger.info("Shutting down background suggestion worker...")
    worker_task.cancel()
    try:
        await worker_task
    except asyncio.CancelledError:
        logger.info("Background suggestion worker stopped successfully.")
    except Exception as e:
        logger.error(f"Error shutting down worker task: {e}")


def create_app() -> FastAPI:
    app = FastAPI(
        title="ShopStream Reactive Commerce Advisor",
        description=(
            "Reactive commerce advisor observing inventory signals, "
            "running Gemini/rule-based strategies, and managing merchandising approval queues."
        ),
        version="1.0.0",
        lifespan=lifespan,
    )

    # Enable CORS for the Merchandising Console
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.ALLOWED_ORIGINS if hasattr(settings, "ALLOWED_ORIGINS") else ["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Core routes registered at root level to match task specifications
    app.include_router(products.router)
    app.include_router(suggestions.router)

    @app.get("/health", tags=["system"])
    async def health_check():
        return {
            "status": "healthy",
            "service": "ShopStream Commerce Advisor",
            "strategy": getattr(settings, "DEFAULT_STRATEGY", "UNKNOWN"),
        }

    @app.get("/")
    async def root():
        return {
            "message": "Welcome to ShopStream Reactive Commerce Advisor API",
            "docs": "/docs",
        }

    return app


app = create_app()