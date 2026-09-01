from typing import List, Optional, Dict, Any, Literal
from pydantic import BaseModel, Field, field_validator
from datetime import datetime

class TravelRequest(BaseModel):
    destination: str = Field(..., description="Destination city or region", json_schema_extra={"example": "Tokyo, Japan"})
    start_date: str = Field(..., description="Start date (YYYY-MM-DD)", json_schema_extra={"example": "2026-10-01"})
    end_date: str = Field(..., description="End date (YYYY-MM-DD)", json_schema_extra={"example": "2026-10-07"})
    budget_range: str = Field(..., description="Budget tier: Budget, Moderate, Luxury, or custom limit", json_schema_extra={"example": "Moderate"})
    interests: List[str] = Field(default_factory=list, description="List of interests or preferred activities", json_schema_extra={"example": ["Food", "Culture", "Shopping"]})
    num_travelers: int = Field(default=1, ge=1, description="Number of travelers", json_schema_extra={"example": 2})
    special_notes: Optional[str] = Field(default=None, description="Additional preferences or constraints", json_schema_extra={"example": "Vegetarian food preferences, prefers public transit"})

    @field_validator('destination')
    def destination_must_not_be_empty(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError('Destination cannot be empty')
        return v.strip()

class ReviewRequest(BaseModel):
    action: Literal["approve", "reject", "modify"] = Field(..., description="Action to take: approve, reject (requires comments), or modify (with specific details)")
    comments: Optional[str] = Field(default=None, description="Feedback or reasons if rejecting or modifying")
    modifications: Optional[Dict[str, Any]] = Field(default=None, description="Specific itemized modifications (e.g. {'hotel': 'Luxury resort', 'day_3_activity': 'Visit Mount Fuji'})")

    @field_validator('comments')
    def validate_comments_for_reject(cls, v: Optional[str], info) -> Optional[str]:
        if info.data.get('action') == 'reject' and (not v or not v.strip()):
            raise ValueError('Feedback comments are required when rejecting a plan.')
        return v

class PlanStatusResponse(BaseModel):
    plan_id: str
    stage: str
    status_message: str
    request: TravelRequest
    research_summary: Optional[Dict[str, Any]] = None
    draft_itinerary: Optional[Dict[str, Any]] = None
    feedback_history: List[Dict[str, Any]] = Field(default_factory=list)
    created_at: str
    updated_at: str

class FinalPlanResponse(BaseModel):
    plan_id: str
    status: str = "FINALIZED"
    request: TravelRequest
    final_plan_markdown: str
    structured_itinerary: Dict[str, Any]
    total_estimated_cost: str
    packing_list: List[str]
    local_tips: List[str]
    finalized_at: str
