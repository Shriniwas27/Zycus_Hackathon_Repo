import asyncio
import logging
from typing import Dict, Any
from sqlalchemy.exc import IntegrityError
from sqlalchemy import select

from .bus import suggestion_queue
from ..engine.manager import strategy_manager
from ..engine.base import RecommendationContext
from ..database import AsyncSessionLocal
from ..models.product import Product
from ..models.pricing_suggestion import PricingSuggestion
from ..models.reorder_suggestion import ReorderSuggestion
from ..models.enums import SuggestionStatus

logger = logging.getLogger(__name__)


async def process_suggestions():
    """
    Background worker that processes items from the suggestion queue.
    For each item, it checks triggers, deduplicates, runs strategy, and persists suggestions.
    """
    logger.info("Starting suggestion processing worker")
    
    while True:
        try:
            # Get item from queue
            item = await suggestion_queue.get()
            
            try:
                await _process_single_item(item)
            except Exception as e:
                logger.error(f"Error processing suggestion item: {str(e)}", exc_info=True)
            finally:
                # Mark task as done
                suggestion_queue.task_done()
                
        except asyncio.CancelledError:
            logger.info("Suggestion processing worker cancelled")
            break
        except Exception as e:
            logger.error(f"Error in suggestion processing loop: {str(e)}", exc_info=True)
            # Small delay to prevent tight loop on persistent errors
            await asyncio.sleep(1)


async def _process_single_item(item: Dict[str, Any]):
    """Process a single item from the queue."""
    if isinstance(item, dict):
        product_id = item.get("product_id")
    else:
        product_id = str(item)

    if not product_id:
        return
    
    if not product_id:
        logger.warning("Received item without product_id, skipping")
        return
    
    # Get product data
    async with AsyncSessionLocal() as db:
        stmt = select(Product).where(Product.id == product_id)
        result = await db.execute(stmt)
        product = result.scalar_one_or_none()
        
        if not product:
            logger.warning(f"Product {product_id} not found, skipping")
            return
        
        # Create recommendation context matching base.py attributes
        # Create recommendation context matching base.py attributes
        context = RecommendationContext(
            product_id=product.id,
            current_price=float(product.current_price),
            current_stock=product.stock_level,
            min_stock_level=product.reorder_threshold,
            max_stock_level=product.reorder_threshold * 3,
            reorder_threshold=product.reorder_threshold,
            cost_price=float(product.cost_price) if product.cost_price else None,
            competitor_price=float(product.competitor_price) if product.competitor_price else None,
            recent_sales_velocity=float(product.demand_velocity),
            category=product.category.value
        )
        
        # Get active strategy
        strategy = strategy_manager.get_active_strategy()
        strategy_name = strategy_manager.get_active_strategy_name()
        
        # Generate recommendations
        try:
            result = await strategy.generate_recommendations(context)
        except Exception as e:
            logger.error(f"Error generating recommendations for product {product_id}: {str(e)}")
            return
        
        # Persist pricing suggestion if exists
        if result.pricing:
            await _persist_pricing_suggestion(db, product, result.pricing, strategy_name)
        
        # Persist reorder suggestion if exists
        if result.reorder:
            await _persist_reorder_suggestion(db, product, result.reorder, strategy_name)
        
        await db.commit()


async def _persist_pricing_suggestion(db, product: Product, recommendation, strategy_name: str):
    """Persist pricing suggestion to database, avoiding duplicates."""
    try:
        # Check for existing pending suggestion with same trigger reason
        stmt = select(PricingSuggestion.id).where(
            PricingSuggestion.product_id == product.id,
            PricingSuggestion.trigger_reason == recommendation.reason.value,
            PricingSuggestion.status == SuggestionStatus.PENDING.value
        )
        
        result = await db.execute(stmt)
        existing_row = result.fetchone()
        
        if existing_row:
            logger.info(f"Skipping duplicate pricing suggestion for product {product.id}")
            return
        
        # Create new suggestion
        suggestion = PricingSuggestion(
            product_id=product.id,
            current_price=product.current_price,
            recommended_price=recommendation.new_price,
            change_direction=recommendation.direction,
            trigger_reason=recommendation.reason,
            confidence=float(recommendation.confidence_score) if recommendation.confidence_score is not None else None,
            reasoning=recommendation.notes,
            strategy_used=strategy_name
        )
        
        db.add(suggestion)
        await db.flush()
        logger.info(f"Created pricing suggestion {suggestion.id} for product {product.id}")
        
    except IntegrityError:
        await db.rollback()
        logger.info(f"Race condition: pricing suggestion for product {product.id} already exists")
    except Exception as e:
        await db.rollback()
        logger.error(f"Error persisting pricing suggestion for product {product.id}: {str(e)}")


async def _persist_reorder_suggestion(db, product: Product, recommendation, strategy_name: str):
    """Persist reorder suggestion to database, avoiding duplicates."""
    try:
        # Check for existing pending suggestion with same trigger reason
        stmt = select(ReorderSuggestion.id).where(
            ReorderSuggestion.product_id == product.id,
            ReorderSuggestion.trigger_reason == recommendation.reason.value,
            ReorderSuggestion.status == SuggestionStatus.PENDING.value
        )
        
        result = await db.execute(stmt)
        existing_row = result.fetchone()
        
        if existing_row:
            logger.info(f"Skipping duplicate reorder suggestion for product {product.id}")
            return
        
        # Create new suggestion
        suggestion = ReorderSuggestion(
            product_id=product.id,
            current_stock=product.stock_level,
            recommended_quantity=max(1, recommendation.quantity_to_order),
            suggested_lead_time_days=7,
            trigger_reason=recommendation.reason,
            confidence=float(recommendation.confidence_score) if recommendation.confidence_score is not None else None,
            reasoning=recommendation.notes,
            strategy_used=strategy_name
        )
        
        db.add(suggestion)
        await db.flush()
        logger.info(f"Created reorder suggestion {suggestion.id} for product {product.id}")
        
    except IntegrityError:
        await db.rollback()
        logger.info(f"Race condition: reorder suggestion for product {product.id} already exists")
    except Exception as e:
        await db.rollback()
        logger.error(f"Error persisting reorder suggestion for product {product.id}: {str(e)}")


def _calculate_sales_velocity(product: Product) -> float:
    """Calculate sales velocity for a product using demand_velocity (24h sales)."""
    return float(product.demand_velocity)