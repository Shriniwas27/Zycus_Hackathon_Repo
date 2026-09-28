from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field, field_validator

from ..models.enums import PriceDirection, SuggestionStatus, TriggerReason


class PricingSuggestionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    product_id: str
    current_price: float
    recommended_price: float
    change_direction: PriceDirection
    confidence: float = Field(
        ..., ge=0.0, le=1.0, description="Confidence score bounded between 0.0 and 1.0"
    )
    reasoning: str = Field(..., description="Plain-English merchandising rationale")
    status: SuggestionStatus
    trigger_reason: TriggerReason
    strategy_used: Optional[str] = "RULE_BASED"
    created_at: datetime
    resolved_at: Optional[datetime] = None


class ReorderSuggestionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    product_id: str
    current_stock: int
    recommended_quantity: int = Field(
        ..., gt=0, description="Must be a positive integer >= 1"
    )
    suggested_lead_time_days: int = Field(
        default=7, gt=0, description="Estimated lead time in days"
    )
    confidence: float = Field(
        ..., ge=0.0, le=1.0, description="Confidence score bounded between 0.0 and 1.0"
    )
    reasoning: str = Field(..., description="Plain-English replenishment rationale")
    status: SuggestionStatus
    trigger_reason: TriggerReason
    strategy_used: Optional[str] = "RULE_BASED"
    created_at: datetime
    resolved_at: Optional[datetime] = None


class SuggestionResolve(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    status: SuggestionStatus

    @field_validator("status")
    @classmethod
    def validate_resolution_status(cls, value: SuggestionStatus) -> SuggestionStatus:
        allowed = (SuggestionStatus.APPROVED, SuggestionStatus.REJECTED)
        if value not in allowed:
            raise ValueError(
                f"Resolution status must be either '{SuggestionStatus.APPROVED.value}' or '{SuggestionStatus.REJECTED.value}'"
            )
        return value