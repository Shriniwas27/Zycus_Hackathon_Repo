from enum import Enum


class ProductCategory(str, Enum):
    ELECTRONICS = "electronics"
    CLOTHING = "clothing"
    HOME_GOODS = "home_goods"
    BEAUTY = "beauty"
    BOOKS = "books"
    TOYS = "toys"
    SPORTS = "sports"
    OTHER = "other"


class ProductStatus(str, Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    DISCONTINUED = "discontinued"


class SuggestionStatus(str, Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    IMPLEMENTED = "implemented"


class TriggerReason(str, Enum):
    LOW_STOCK = "low_stock"
    VELOCITY_SPIKE = "velocity_spike"
    SEASONAL_TREND = "seasonal_trend"
    COMPETITOR_PRICE_CHANGE = "competitor_price_change"


class PriceDirection(str, Enum):
    INCREASE = "increase"
    DECREASE = "decrease"
    MAINTAIN = "maintain"