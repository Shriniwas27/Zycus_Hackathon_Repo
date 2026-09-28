from sqlalchemy import Column, String, Integer, DateTime, Enum, ForeignKey, UniqueConstraint, Numeric
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
import uuid

from .enums import SuggestionStatus, TriggerReason
from ..database import Base


class ReorderSuggestion(Base):
    __tablename__ = "reorder_suggestions"
    
    # UUID primary key
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    product_id = Column(String(36), ForeignKey("products.id"), nullable=False)
    current_stock = Column(Integer, nullable=False)
    recommended_quantity = Column(Integer, nullable=False)
    suggested_lead_time_days = Column(Integer, nullable=True)
    confidence = Column(Numeric(5, 2), nullable=True)  # Confidence score 0.00-1.00
    reasoning = Column(String(500), nullable=True)
    status = Column(Enum(SuggestionStatus), nullable=False, default=SuggestionStatus.PENDING)
    trigger_reason = Column(Enum(TriggerReason), nullable=False)
    strategy_used = Column(String(50), nullable=True, default="RULE_BASED")
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    resolved_at = Column(DateTime(timezone=True), nullable=True)
    
    # Compound uniqueness constraint to prevent duplicate suggestions
    __table_args__ = (
        UniqueConstraint('product_id', 'trigger_reason', 'status',
                        name='uq_reorder_product_trigger_status'),
    )
    
    # Relationship
    product = relationship("Product", back_populates="reorder_suggestions")


# Add relationship to Product model
from .product import Product
Product.reorder_suggestions = relationship("ReorderSuggestion", back_populates="product")