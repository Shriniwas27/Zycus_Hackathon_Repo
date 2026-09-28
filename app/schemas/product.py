from pydantic import BaseModel, Field, ConfigDict
from typing import Optional
from datetime import datetime

from ..models.enums import ProductCategory, ProductStatus


class ProductBase(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    sku: str = Field(max_length=64)
    name: str = Field(max_length=255)
    category: ProductCategory
    current_price: float = Field(gt=0)
    stock_level: int = Field(ge=0, default=0)
    reorder_threshold: int = Field(ge=0, default=10)
    demand_velocity: int = Field(ge=0, default=0)
    status: ProductStatus = ProductStatus.ACTIVE
    cost_price: Optional[float] = Field(default=None, gt=0)
    supplier_id: Optional[str] = Field(default=None, max_length=64)
    competitor_price: Optional[float] = Field(default=None, gt=0)


class ProductCreate(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    sku: str = Field(max_length=64)
    name: str = Field(max_length=255)
    category: ProductCategory
    current_price: float = Field(gt=0)
    stock_level: int = Field(ge=0, default=0)
    reorder_threshold: int = Field(ge=0, default=10)
    cost_price: Optional[float] = Field(default=None, gt=0)
    supplier_id: Optional[str] = Field(default=None, max_length=64)
    competitor_price: Optional[float] = Field(default=None, gt=0)


class ProductUpdate(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    sku: Optional[str] = Field(default=None, max_length=64)
    name: Optional[str] = Field(default=None, max_length=255)
    category: Optional[ProductCategory] = None
    current_price: Optional[float] = Field(default=None, gt=0)
    stock_level: Optional[int] = Field(default=None, ge=0)
    reorder_threshold: Optional[int] = Field(default=None, ge=0)
    demand_velocity: Optional[int] = Field(default=None, ge=0)
    status: Optional[ProductStatus] = None
    cost_price: Optional[float] = Field(default=None, gt=0)
    supplier_id: Optional[str] = Field(default=None, max_length=64)
    competitor_price: Optional[float] = Field(default=None, gt=0)


class ProductStockUpdate(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    stock_level: int = Field(ge=0)


class ProductOrderSimulate(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    quantity: int = Field(default=1, gt=0)


class ProductResponse(ProductBase):
    model_config = ConfigDict(from_attributes=True)
    
    id: str
    created_at: datetime
    updated_at: datetime