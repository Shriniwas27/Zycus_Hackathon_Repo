from sqlalchemy import Column, String, Integer, Numeric, DateTime, Enum
from sqlalchemy.sql import func
import uuid

from ..database import Base
from .enums import ProductCategory, ProductStatus


class Product(Base):
    __tablename__ = "products"
    
    # UUID primary key
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    sku = Column(String(64), unique=True, index=True, nullable=False)
    name = Column(String(255), nullable=False)
    category = Column(Enum(ProductCategory), index=True, nullable=False)
    current_price = Column(Numeric(10, 2), nullable=False)
    cost_price = Column(Numeric(10, 2), nullable=True)  # Nullable for Sprint 2
    supplier_id = Column(String(64), nullable=True)  # Nullable for Sprint 2
    competitor_price = Column(Numeric(10, 2), nullable=True)  # Nullable for Sprint 2
    stock_level = Column(Integer, nullable=False, default=0)
    reorder_threshold = Column(Integer, nullable=False, default=10)
    demand_velocity = Column(Integer, nullable=False, default=0)  # 24h sales
    status = Column(Enum(ProductStatus), nullable=False, default=ProductStatus.ACTIVE, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    @property
    def available_stock(self) -> int:
        return self.stock_level
    
    @property
    def is_low_stock(self) -> bool:
        return self.stock_level <= self.reorder_threshold
    
    @property
    def stock_status_ratio(self) -> float:
        """Return stock level as ratio of reorder threshold."""
        if self.reorder_threshold == 0:
            return 0.0
        return self.stock_level / self.reorder_threshold