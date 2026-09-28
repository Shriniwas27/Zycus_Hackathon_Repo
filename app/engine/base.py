from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, List, Optional
from enum import Enum

from ..models.enums import TriggerReason, PriceDirection


@dataclass
class RecommendationContext:
    product_id: Any
    current_price: float
    current_stock: int
    min_stock_level: int
    max_stock_level: int
    cost_price: Optional[float]
    competitor_price: Optional[float]
    recent_sales_velocity: float  # Units sold per day
    category: str
    reorder_threshold: Optional[int] = None

    def __post_init__(self):
        if self.reorder_threshold is None:
            self.reorder_threshold = self.min_stock_level


@dataclass
class PricingRecommendation:
    new_price: float
    direction: PriceDirection
    reason: TriggerReason
    confidence_score: Optional[float] = None
    notes: Optional[str] = None


@dataclass
class ReorderRecommendation:
    quantity_to_order: int
    reason: TriggerReason
    confidence_score: Optional[float] = None
    notes: Optional[str] = None


@dataclass
class RecommendationResult:
    pricing: Optional[PricingRecommendation] = None
    reorder: Optional[ReorderRecommendation] = None


class CommerceAdvisorStrategy(ABC):
    @abstractmethod
    async def generate_recommendations(self, context: RecommendationContext) -> RecommendationResult:
        """
        Generate pricing and reorder recommendations based on the product context.
        
        Args:
            context: RecommendationContext containing product data
            
        Returns:
            RecommendationResult with pricing and/or reorder recommendations
        """
        pass