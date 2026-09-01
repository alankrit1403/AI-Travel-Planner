from typing import TypedDict, List, Dict, Any, Optional

class TravelPlanState(TypedDict, total=False):
    plan_id: str
    request: Dict[str, Any]
    stage: str
    research_data: Optional[Dict[str, Any]]
    draft_itinerary: Optional[Dict[str, Any]]
    feedback_history: List[Dict[str, Any]]
    latest_review: Optional[Dict[str, Any]]
    final_plan: Optional[Dict[str, Any]]
    revision_count: int
    status_message: str
    error: Optional[str]
    created_at: str
    updated_at: str
