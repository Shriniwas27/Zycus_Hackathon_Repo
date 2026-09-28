from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..database import get_db
from ..models.enums import ProductStatus, TriggerReason
from ..models.product import Product 
from ..schemas.product import (
    ProductCreate,
    ProductOrderSimulate,
    ProductResponse,
    ProductStockUpdate,
    ProductUpdate,
)
from ..task_queue.bus import suggestion_queue

router = APIRouter(
    prefix="/products",
    tags=["products"],
)


async def _check_triggers(product: ProductModel) -> None:
    """Check if product changes trigger any recommendations."""
    # Check for low stock trigger
    if getattr(product, "is_low_stock", False):
        await suggestion_queue.put(
            {
                "product_id": product.id,
                "trigger_reason": TriggerReason.LOW_STOCK.value,
            }
        )

    # Check for high demand velocity trigger
    reorder_threshold = getattr(product, "reorder_threshold", 0)
    demand_velocity = getattr(product, "demand_velocity", 0)
    if reorder_threshold > 0 and demand_velocity > (2 * reorder_threshold):
        await suggestion_queue.put(
            {
                "product_id": product.id,
                "trigger_reason": TriggerReason.VELOCITY_SPIKE.value,
            }
        )


@router.post("/", response_model=ProductResponse, status_code=status.HTTP_201_CREATED)
async def create_product(product_in: ProductCreate, db: AsyncSession = Depends(get_db)):
    product = Product(**product_in.model_dump())
    db.add(product)
    await db.commit()
    await db.refresh(product)

    # Trigger background recommendation processing
    # In app/routers/products.py inside create_product:
    await suggestion_queue.put({"product_id": str(product.id)})
    # (If your worker uses a helper: await enqueue_product_suggestion(product.id))

    return product


@router.get("/", response_model=List[ProductResponse])
async def list_products(
    skip: int = 0,
    limit: int = 100,
    status_filter: Optional[ProductStatus] = None,
    category: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
):
    """List all products with optional filtering."""
    stmt = select(ProductModel)

    if status_filter:
        stmt = stmt.where(ProductModel.status == status_filter)

    if category:
        stmt = stmt.where(ProductModel.category == category)

    stmt = stmt.offset(skip).limit(limit)

    result = await db.execute(stmt)
    products = result.scalars().all()

    return products


@router.get("/{product_id}", response_model=ProductResponse)
async def get_product(product_id: str, db: AsyncSession = Depends(get_db)):
    """Get a specific product by ID."""
    stmt = select(ProductModel).where(ProductModel.id == product_id)
    result = await db.execute(stmt)
    product = result.scalar_one_or_none()

    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found",
        )

    return product


@router.patch("/{product_id}", response_model=ProductResponse)
async def update_product(
    product_id: str,
    product_update: ProductUpdate,
    db: AsyncSession = Depends(get_db),
):
    """Update a product."""
    stmt = select(ProductModel).where(ProductModel.id == product_id)
    result = await db.execute(stmt)
    db_product = result.scalar_one_or_none()

    if not db_product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found",
        )

    update_data = product_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_product, field, value)

    await db.commit()
    await db.refresh(db_product)

    await _check_triggers(db_product)

    return db_product


@router.patch("/{product_id}/stock", response_model=ProductResponse)
async def update_product_stock(
    product_id: str,
    stock_update: ProductStockUpdate,
    db: AsyncSession = Depends(get_db),
):
    """Update product stock level."""
    stmt = select(ProductModel).where(ProductModel.id == product_id)
    result = await db.execute(stmt)
    db_product = result.scalar_one_or_none()

    if not db_product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found",
        )

    if stock_update.stock_level < 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Stock level cannot be negative",
        )

    db_product.stock_level = stock_update.stock_level

    if db_product.stock_level == 0:
        db_product.status = ProductStatus.INACTIVE

    await db.commit()
    await db.refresh(db_product)

    await _check_triggers(db_product)

    return db_product


@router.post("/{product_id}/orders", response_model=ProductResponse)
async def record_order(
    product_id: str,
    order: ProductOrderSimulate,
    db: AsyncSession = Depends(get_db),
):
    """Record an order/sale for a product."""
    stmt = select(ProductModel).where(ProductModel.id == product_id)
    result = await db.execute(stmt)
    db_product = result.scalar_one_or_none()

    if not db_product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found",
        )

    if db_product.stock_level < order.quantity:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Insufficient stock for this order",
        )

    db_product.stock_level -= order.quantity
    db_product.demand_velocity += order.quantity

    if db_product.stock_level == 0:
        db_product.status = ProductStatus.INACTIVE

    await db.commit()
    await db.refresh(db_product)

    await _check_triggers(db_product)

    return db_product