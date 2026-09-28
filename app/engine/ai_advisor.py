import asyncio
import json
import logging
from typing import Optional, Dict, Any

from .base import (
    CommerceAdvisorStrategy, 
    RecommendationContext, 
    RecommendationResult,
    PricingRecommendation,
    ReorderRecommendation,
    TriggerReason,
    PriceDirection
)
from .llm_gateway import call_llm
from ..config import settings
from .rule_based import RuleBasedCommerceAdvisor


logger = logging.getLogger(__name__)


class AIAdvisorCommerceAdvisor(CommerceAdvisorStrategy):
    """
    AI-powered commerce advisor using LLM to generate structured recommendations.
    Falls back to rule-based strategy if LLM fails or times out.
    """
    
    def __init__(self):
        self.fallback_strategy = RuleBasedCommerceAdvisor()
        
    async def generate_recommendations(self, context: RecommendationContext) -> RecommendationResult:
        """
        Generate recommendations using AI with fallback to rules.
        """
        try:
            # Try AI recommendation with timeout
            ai_result = await asyncio.wait_for(
                self._generate_ai_recommendations(context),
                timeout=15  # 4.5s timeout as specified
            )
            return ai_result
        except asyncio.TimeoutError:
            logger.warning(f"AI advisor timeout for product {context.product_id}, falling back to rules")
            return await self.fallback_strategy.generate_recommendations(context)
        except Exception as e:
            logger.error(f"AI advisor error for product {context.product_id}: {str(e)}, falling back to rules")
            return await self.fallback_strategy.generate_recommendations(context)
    
    async def _generate_ai_recommendations(self, context: RecommendationContext) -> RecommendationResult:
        """Generate recommendations using AI/LLM."""
        # Prepare structured prompt for LLM
        prompt = self._create_structured_prompt(context)
        
        # Call LLM
        response_text = await call_llm(prompt)
        
        # Parse and validate response
        parsed_response = self._parse_and_validate_response(response_text)
        
        return parsed_response
    
    def _create_structured_prompt(self, context: RecommendationContext) -> str:
        """Create structured prompt for LLM."""
        prompt = f"""
You are a commerce advisor expert. Analyze the product data and provide pricing and reorder recommendations.

PRODUCT DATA:
- Product ID: {context.product_id}
- Current Price: ${context.current_price:.2f}
- Current Stock: {context.current_stock} units
- Reorder Threshold: {context.reorder_threshold} units
- Cost Price: ${context.cost_price or 0:.2f}
- Competitor Price: ${context.competitor_price or 0:.2f}
- Recent Sales Velocity: {context.recent_sales_velocity} units/day
- Category: {context.category}

ANALYSIS CRITERIA:
1. Pricing Recommendations:
   - Increase prices by up to 15% for low stock items (< reorder threshold)
   - Increase prices by up to 10% for high-velocity items (> 2x normal)
   - Decrease prices by up to 5% for overstock items (> 80% of max level)
   - Maintain prices otherwise
   - Consider competitor pricing when making decisions

2. Reorder Recommendations:
   - Recommend reordering when stock falls below 2x reorder threshold
   - Calculate order quantities to maintain 30 days of inventory plus 50% buffer
   - Consider sales velocity in calculations

RESPONSE FORMAT:
Provide your response as a valid JSON object with the following structure:
{{
  "pricing": {{
    "new_price": number,
    "direction": "increase|decrease|maintain",
    "reason": "low_stock|velocity_spike|seasonal_trend|competitor_price_change",
    "confidence_score": number between 0.0-1.0,
    "notes": "brief explanation"
  }} | null,
  "reorder": {{
    "quantity_to_order": integer,
    "reason": "low_stock|velocity_spike|seasonal_trend|competitor_price_change",
    "confidence_score": number between 0.0-1.0,
    "notes": "brief explanation"
  }} | null
}}

Guidelines:
- Only include sections that apply (use null for unused sections)
- Ensure numerical values are within reasonable bounds
- Confidence scores must be between 0.0 and 1.0
- Direction must be one of: "increase", "decrease", "maintain"
- Reason must be one of: "low_stock", "velocity_spike", "seasonal_trend", "competitor_price_change"
- quantity_to_order must be a positive integer (≥ 1)

Provide only the JSON object, no additional text.
"""
        return prompt
    
    def _parse_and_validate_response(self, response_text: str) -> RecommendationResult:
        """Parse and validate LLM response."""
        try:
            # Parse JSON response
            data = json.loads(response_text)
            
            result = RecommendationResult()
            
            # Process pricing recommendation
            if data.get("pricing"):
                pricing_data = data["pricing"]
                # Validate and constrain values
                new_price = max(0.01, pricing_data["new_price"])  # Minimum $0.01
                
                # Determine price direction
                direction_map = {
                    "increase": PriceDirection.INCREASE,
                    "decrease": PriceDirection.DECREASE,
                    "maintain": PriceDirection.MAINTAIN
                }
                direction = direction_map.get(pricing_data["direction"], PriceDirection.MAINTAIN)
                
                # Validate reason
                reason_map = {
                    "low_stock": TriggerReason.LOW_STOCK,
                    "velocity_spike": TriggerReason.VELOCITY_SPIKE,
                    "seasonal_trend": TriggerReason.SEASONAL_TREND,
                    "competitor_price_change": TriggerReason.COMPETITOR_PRICE_CHANGE
                }
                reason = reason_map.get(pricing_data["reason"], TriggerReason.LOW_STOCK)
                
                # Constrain confidence score
                confidence = pricing_data.get("confidence_score")
                if confidence is not None:
                    confidence = max(0.0, min(1.0, confidence))
                
                result.pricing = PricingRecommendation(
                    new_price=new_price,
                    direction=direction,
                    reason=reason,
                    confidence_score=confidence,
                    notes=pricing_data.get("notes")
                )
            
            # Process reorder recommendation
            if data.get("reorder"):
                reorder_data = data["reorder"]
                # Validate and constrain values
                quantity = max(1, reorder_data["quantity_to_order"])  # Ensure positive integer ≥ 1
                
                # Validate reason
                reason_map = {
                    "low_stock": TriggerReason.LOW_STOCK,
                    "velocity_spike": TriggerReason.VELOCITY_SPIKE,
                    "seasonal_trend": TriggerReason.SEASONAL_TREND,
                    "competitor_price_change": TriggerReason.COMPETITOR_PRICE_CHANGE
                }
                reason = reason_map.get(reorder_data["reason"], TriggerReason.LOW_STOCK)
                
                # Constrain confidence score
                confidence = reorder_data.get("confidence_score")
                if confidence is not None:
                    confidence = max(0.0, min(1.0, confidence))
                
                result.reorder = ReorderRecommendation(
                    quantity_to_order=quantity,
                    reason=reason,
                    confidence_score=confidence,
                    notes=reorder_data.get("notes")
                )
            
            return result
        except (json.JSONDecodeError, KeyError, TypeError) as e:
            logger.error(f"Failed to parse AI response: {str(e)}")
            raise ValueError(f"Invalid AI response format: {str(e)}")