from sqlalchemy import Column, String, Integer, Numeric, DateTime, Enum, ForeignKey, UniqueConstraint
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
import uuid

from .enums import SuggestionStatus, TriggerReason, PriceDirection
from ..database import Base


class PricingSuggestion(Base):
    __tablename__ = "pricing_suggestions"
    
    # UUID primary key
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    product_id = Column(String(36), ForeignKey("products.id"), nullable=False)
    current_price = Column(Numeric(10, 2), nullable=False)
    recommended_price = Column(Numeric(10, 2), nullable=False)
    change_direction = Column(Enum(PriceDirection), nullable=False)
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
                        name='uq_product_trigger_status'),
    )
    
    # Relationship
    product = relationship("Product", back_populates="pricing_suggestions")


# Add relationship to Product model
from .product import Product
Product.pricing_suggestions = relationship("PricingSuggestion", back_populates="product")