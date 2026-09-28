import asyncio
from typing import Optional
import logging

from .base import (
    CommerceAdvisorStrategy, 
    RecommendationContext, 
    RecommendationResult,
    PricingRecommendation,
    ReorderRecommendation,
    TriggerReason,
    PriceDirection
)
from ..models.enums import ProductCategory


logger = logging.getLogger(__name__)


class RuleBasedCommerceAdvisor(CommerceAdvisorStrategy):
    """
    Rule-based commerce advisor implementing deterministic formulas:
    - +10% price on low stock
    - +5% on velocity spike
    - Buffer reorder suggestions
    """
    
    # Configuration constants
    LOW_STOCK_PRICE_INCREASE = 1.10  # 10% increase
    VELOCITY_SPIKE_PRICE_INCREASE = 1.05  # 5% increase
    REORDER_BUFFER_MULTIPLIER = 2.0  # Order 2x expected usage
    VELOCITY_SPIKE_THRESHOLD = 2.0  # 2x normal velocity to trigger spike
    
    async def generate_recommendations(self, context: RecommendationContext) -> RecommendationResult:
        """
        Generate recommendations using deterministic rules.
        """
        result = RecommendationResult()
        
        # Check for pricing opportunities
        pricing_rec = await self._generate_pricing_recommendation(context)
        if pricing_rec:
            result.pricing = pricing_rec
            
        # Check for reorder needs
        reorder_rec = await self._generate_reorder_recommendation(context)
        if reorder_rec:
            result.reorder = reorder_rec
            
        return result
    
    async def _generate_pricing_recommendation(self, context: RecommendationContext) -> Optional[PricingRecommendation]:
        """Generate pricing recommendation based on stock levels and velocity."""
        # Check for low stock condition
        if context.current_stock <= context.reorder_threshold:
            new_price = context.current_price * self.LOW_STOCK_PRICE_INCREASE
            return PricingRecommendation(
                new_price=new_price,
                direction=PriceDirection.INCREASE,
                reason=TriggerReason.LOW_STOCK,
                confidence_score=0.9,
                notes=f"Low stock trigger: {context.current_stock} ≤ {context.reorder_threshold}"
            )
        
        # Check for velocity spike
        # We would normally compare against historical average, simplified here
        if context.recent_sales_velocity >= self.VELOCITY_SPIKE_THRESHOLD:
            new_price = context.current_price * self.VELOCITY_SPIKE_PRICE_INCREASE
            return PricingRecommendation(
                new_price=new_price,
                direction=PriceDirection.INCREASE,
                reason=TriggerReason.VELOCITY_SPIKE,
                confidence_score=0.8,
                notes=f"Velocity spike detected: {context.recent_sales_velocity} ≥ {self.VELOCITY_SPIKE_THRESHOLD}"
            )
            
        return None
    
    async def _generate_reorder_recommendation(self, context: RecommendationContext) -> Optional[ReorderRecommendation]:
        """Generate reorder recommendation based on stock levels and velocity."""
        # Simple reorder logic: if stock is below 2x reorder threshold, suggest reorder
        reorder_threshold = context.reorder_threshold * 2
        
        if context.current_stock <= reorder_threshold:
            # Calculate how much to order based on velocity and buffer
            days_of_supply = 30  # Target 30 days supply
            estimated_need = context.recent_sales_velocity * days_of_supply
            buffer_stock = estimated_need * self.REORDER_BUFFER_MULTIPLIER
            # Assuming a maximum stock level equivalent to reorder_threshold * 10 for calculation
            max_stock_level = context.reorder_threshold * 10
            current_buffer = max_stock_level - context.current_stock
            quantity_needed = max(1, int(buffer_stock - current_buffer))  # Ensure at least 1
            
            if quantity_needed > 0:
                return ReorderRecommendation(
                    quantity_to_order=quantity_needed,
                    reason=TriggerReason.LOW_STOCK,
                    confidence_score=0.9,
                    notes=f"Reorder triggered: {context.current_stock} ≤ {reorder_threshold}"
                )
                
        return None