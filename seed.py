#!/usr/bin/env python3
"""
Seed script to populate the database with initial products.
"""

import asyncio
import sys
import os

# Add the app directory to the path so we can import from it
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

from app.database import init_db, AsyncSessionLocal
from app.models.product import Product
from app.models.enums import ProductCategory, ProductStatus


async def seed_database():
    """Seed the database with initial products."""
    # Initialize the database
    await init_db()
    
    async with AsyncSessionLocal() as db:
        # Check if we already have products
        from sqlalchemy import text
        result = await db.execute(text("SELECT COUNT(*) FROM products"))
        count = result.scalar()
        
        if count > 0:
            print(f"Database already contains {count} products. Skipping seed.")
            return
        
        # Create initial products
        products_data = [
            {
                "name": "Wireless Bluetooth Headphones",
                "sku": "WBH-001",
                "category": ProductCategory.ELECTRONICS,
                "current_price": 89.99,
                "cost_price": 45.00,
                "supplier_id": "SUP-ELC-001",
                "competitor_price": 95.00,
                "stock_level": 50,
                "reorder_threshold": 10,
                "demand_velocity": 2,
                "status": ProductStatus.ACTIVE
            },
            {
                "name": "Smartphone Case - Clear",
                "sku": "SCC-002",
                "category": ProductCategory.ELECTRONICS,
                "current_price": 19.99,
                "cost_price": 5.50,
                "supplier_id": "SUP-ELC-002",
                "competitor_price": 18.99,
                "stock_level": 200,
                "reorder_threshold": 50,
                "demand_velocity": 5,
                "status": ProductStatus.ACTIVE
            },
            {
                "name": "Cotton T-Shirt - Medium",
                "sku": "CTS-M-003",
                "category": ProductCategory.CLOTHING,
                "current_price": 24.99,
                "cost_price": 8.75,
                "supplier_id": "SUP-CLT-001",
                "competitor_price": 26.99,
                "stock_level": 150,
                "reorder_threshold": 30,
                "demand_velocity": 3,
                "status": ProductStatus.ACTIVE
            },
            {
                "name": "Stainless Steel Water Bottle",
                "sku": "SSWB-004",
                "category": ProductCategory.HOME_GOODS,
                "current_price": 29.99,
                "cost_price": 12.00,
                "supplier_id": "SUP-HOM-001",
                "competitor_price": 32.99,
                "stock_level": 75,
                "reorder_threshold": 15,
                "demand_velocity": 1,
                "status": ProductStatus.ACTIVE
            },
            {
                "name": "Facial Moisturizer SPF 30",
                "sku": "FMS-005",
                "category": ProductCategory.BEAUTY,
                "current_price": 34.99,
                "cost_price": 15.25,
                "supplier_id": "SUP-BTY-001",
                "competitor_price": 36.50,
                "stock_level": 40,
                "reorder_threshold": 10,
                "demand_velocity": 2,
                "status": ProductStatus.ACTIVE
            },
            {
                "name": "Bestselling Novel",
                "sku": "BN-006",
                "category": ProductCategory.BOOKS,
                "current_price": 14.99,
                "cost_price": 7.50,
                "supplier_id": "SUP-BOK-001",
                "competitor_price": 13.99,
                "stock_level": 80,
                "reorder_threshold": 20,
                "demand_velocity": 4,
                "status": ProductStatus.ACTIVE
            },
            {
                "name": "Board Game for Families",
                "sku": "BGF-007",
                "category": ProductCategory.TOYS,
                "current_price": 39.99,
                "cost_price": 20.00,
                "supplier_id": "SUP-TOY-001",
                "competitor_price": 42.99,
                "stock_level": 25,
                "reorder_threshold": 5,
                "demand_velocity": 1,
                "status": ProductStatus.ACTIVE
            },
            {
                "name": "Yoga Mat - Premium",
                "sku": "YMP-008",
                "category": ProductCategory.SPORTS,
                "current_price": 49.99,
                "cost_price": 25.00,
                "supplier_id": "SUP-SPR-001",
                "competitor_price": 45.99,
                "stock_level": 12,  # Near low-stock threshold
                "reorder_threshold": 10,
                "demand_velocity": 2,
                "status": ProductStatus.ACTIVE
            }
        ]
        
        # Insert products
        for product_data in products_data:
            product = Product(**product_data)
            db.add(product)
        
        await db.commit()
        print(f"Successfully seeded database with {len(products_data)} products.")


if __name__ == "__main__":
    asyncio.run(seed_database())