import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..database import get_db
from ..models.enums import SuggestionStatus
from ..models.pricing_suggestion import PricingSuggestion as PricingSuggestionModel
from ..models.product import Product as ProductModel
from ..models.reorder_suggestion import ReorderSuggestion as ReorderSuggestionModel
from ..schemas.suggestion import (
    PricingSuggestionResponse,
    ReorderSuggestionResponse,
    SuggestionResolve,
)

router = APIRouter(prefix="", tags=["suggestions"])


@router.patch(
    "/pricing-suggestions/{suggestion_id}",
    response_model=PricingSuggestionResponse,
)
async def update_pricing_suggestion(
    suggestion_id: str,
    update: SuggestionResolve,
    db: AsyncSession = Depends(get_db),
):
    """Update the status of a pricing suggestion."""
    stmt = select(PricingSuggestionModel).where(
        PricingSuggestionModel.id == suggestion_id
    )
    result = await db.execute(stmt)
    suggestion = result.scalar_one_or_none()

    if not suggestion:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Pricing suggestion not found",
        )

    # Update status and resolved_at timestamp
    suggestion.status = update.status
    suggestion.resolved_at = datetime.datetime.now(datetime.timezone.utc)

    # If approved, update product price in the same transaction context
    if update.status == SuggestionStatus.APPROVED:
        product_stmt = select(ProductModel).where(
            ProductModel.id == suggestion.product_id
        )
        product_result = await db.execute(product_stmt)
        product = product_result.scalar_one_or_none()
        if product:
            product.current_price = suggestion.recommended_price

    # Commit both suggestion and product updates atomically
    await db.commit()
    await db.refresh(suggestion)

    return suggestion


@router.patch(
    "/reorder-suggestions/{suggestion_id}",
    response_model=ReorderSuggestionResponse,
)
async def update_reorder_suggestion(
    suggestion_id: str,
    update: SuggestionResolve,
    db: AsyncSession = Depends(get_db),
):
    """Update the status of a reorder suggestion."""
    stmt = select(ReorderSuggestionModel).where(
        ReorderSuggestionModel.id == suggestion_id
    )
    result = await db.execute(stmt)
    suggestion = result.scalar_one_or_none()

    if not suggestion:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Reorder suggestion not found",
        )

    suggestion.status = update.status
    suggestion.resolved_at = datetime.datetime.now(datetime.timezone.utc)

    await db.commit()
    await db.refresh(suggestion)

    return suggestion


@router.get(
    "/pricing-suggestions",
    response_model=List[PricingSuggestionResponse],
)
async def list_pricing_suggestions(
    status_filter: Optional[SuggestionStatus] = None,
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db),
):
    """List pricing suggestions with optional filtering."""
    stmt = select(PricingSuggestionModel)

    if status_filter:
        stmt = stmt.where(PricingSuggestionModel.status == status_filter)

    stmt = (
        stmt.order_by(PricingSuggestionModel.created_at.desc())
        .offset(skip)
        .limit(limit)
    )

    result = await db.execute(stmt)
    return result.scalars().all()


@router.get(
    "/reorder-suggestions",
    response_model=List[ReorderSuggestionResponse],
)
async def list_reorder_suggestions(
    status_filter: Optional[SuggestionStatus] = None,
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db),
):
    """List reorder suggestions with optional filtering."""
    stmt = select(ReorderSuggestionModel)

    if status_filter:
        stmt = stmt.where(ReorderSuggestionModel.status == status_filter)

    stmt = (
        stmt.order_by(ReorderSuggestionModel.created_at.desc())
        .offset(skip)
        .limit(limit)
    )

    result = await db.execute(stmt)
    return result.scalars().all()