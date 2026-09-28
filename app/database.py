from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, DeclarativeBase
from sqlalchemy.pool import StaticPool
from sqlalchemy import text
import asyncio

from .config import settings


# Base class for all SQLAlchemy declarative models
class Base(DeclarativeBase):
    pass


# Create async engine with SQLite-specific configurations
engine = create_async_engine(
    settings.DATABASE_URL,
    echo=False,  # Set to True for SQL logging
    poolclass=StaticPool,  # For SQLite in single-process scenarios
    connect_args={
        "check_same_thread": False,  # Required for async SQLite
        "timeout": 30,  # Prevent "database is locked" errors
    },
)


# Create session factory
AsyncSessionLocal = sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


async def init_db():
    """Initialize the database and enable WAL mode."""
    async with engine.begin() as conn:
        # Enable WAL mode for better concurrency
        await conn.execute(text("PRAGMA journal_mode=WAL;"))
        # Other recommended SQLite settings
        await conn.execute(text("PRAGMA synchronous=NORMAL;"))
        await conn.execute(text("PRAGMA cache_size=1000000;"))
        await conn.execute(text("PRAGMA temp_store=memory;"))
        
        # Import models here to ensure they are registered with Base.metadata
        from .models.product import Product
        from .models.pricing_suggestion import PricingSuggestion
        from .models.reorder_suggestion import ReorderSuggestion
        
        # Create all tables
        await conn.run_sync(Base.metadata.create_all)


async def get_db():
    """Dependency for FastAPI to get DB session."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()