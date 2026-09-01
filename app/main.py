import uuid
from datetime import datetime
from typing import Dict, Any, List, Optional
from fastapi import FastAPI, HTTPException, Path, status
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
import os

from app.config import settings
from app.models import TravelRequest, ReviewRequest, PlanStatusResponse, FinalPlanResponse
from app.graph import travel_planner_app, memory_checkpointer

app = FastAPI(
    title=settings.APP_NAME,
    description="Multi-Agent Travel Planning System with Human-in-the-Loop Approval using LangGraph & FastAPI",
    version="1.0.0"
)

# Enable CORS for frontend integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve Static UI files
static_dir = os.path.join(os.path.dirname(__file__), "static")
if os.path.exists(static_dir):
    app.mount("/static", StaticFiles(directory=static_dir), name="static")

# In-memory store for fast plan lookup mapping plan_id to thread config
PLAN_STORES: Dict[str, Dict[str, Any]] = {}

@app.get("/health", tags=["System"])
def health_check():
    """System health check and feature flag status."""
    return {
        "status": "healthy",
        "app_name": settings.APP_NAME,
        "openai_key_configured": bool(settings.OPENAI_API_KEY),
        "serper_key_configured": bool(settings.SERPER_API_KEY),
        "exa_key_configured": bool(settings.EXA_API_KEY),
        "timestamp": datetime.now().isoformat()
    }

@app.post("/plan", response_model=Dict[str, Any], status_code=status.HTTP_202_ACCEPTED, tags=["Travel Plan"])
def submit_travel_plan(request: TravelRequest):
    """
    Submit a new travel request.
    Initializes the LangGraph workflow and runs until the HITL interrupt stage.
    Returns plan_id (session ID).
    """
    plan_id = str(uuid.uuid4())
    thread_config = {"configurable": {"thread_id": plan_id}}
    
    initial_state = {
        "plan_id": plan_id,
        "request": request.model_dump(),
        "stage": "VALIDATING",
        "feedback_history": [],
        "revision_count": 0,
        "created_at": datetime.now().isoformat(),
        "updated_at": datetime.now().isoformat(),
        "status_message": "Travel request received and initialized."
    }

    try:
        # Run graph until interrupt (interrupt_before hitl_approval_node)
        for event in travel_planner_app.stream(initial_state, thread_config):
            pass
    except Exception as e:
        print(f"[POST /plan] Stream notice: {e}")

    # Fetch current graph snapshot state
    snapshot = travel_planner_app.get_state(thread_config)
    current_values = snapshot.values if snapshot else initial_state

    PLAN_STORES[plan_id] = {
        "thread_config": thread_config,
        "created_at": initial_state["created_at"]
    }

    return {
        "plan_id": plan_id,
        "status": "ACCEPTED",
        "stage": current_values.get("stage", "AWAITING_APPROVAL"),
        "message": "Travel request accepted. Workflow processed through research and itinerary planning.",
        "poll_url": f"/plan/{plan_id}"
    }

@app.get("/plan/{plan_id}", tags=["Travel Plan"])
def get_plan_status(plan_id: str = Path(..., description="The unique session/plan ID")):
    """
    Retrieve current plan status, draft itinerary, research summary, and feedback history.
    """
    thread_config = {"configurable": {"thread_id": plan_id}}
    snapshot = travel_planner_app.get_state(thread_config)

    if not snapshot or not snapshot.values:
        if plan_id not in PLAN_STORES:
            raise HTTPException(status_code=404, detail=f"Travel plan ID '{plan_id}' not found.")
        state = {}
    else:
        state = snapshot.values

    return {
        "plan_id": plan_id,
        "stage": state.get("stage", "UNKNOWN"),
        "status_message": state.get("status_message", "Processing plan"),
        "request": state.get("request"),
        "research_summary": state.get("research_data"),
        "draft_itinerary": state.get("draft_itinerary"),
        "feedback_history": state.get("feedback_history", []),
        "revision_count": state.get("revision_count", 0),
        "is_awaiting_approval": state.get("stage") == "AWAITING_APPROVAL",
        "is_finalized": state.get("stage") == "FINALIZED",
        "created_at": state.get("created_at"),
        "updated_at": state.get("updated_at")
    }

@app.post("/plan/{plan_id}/review", tags=["Travel Plan"])
def review_travel_plan(
    review: ReviewRequest,
    plan_id: str = Path(..., description="The unique session/plan ID")
):
    """
    Submit HITL feedback (approve, reject with comments, or modify specific items).
    Resumes the stateful LangGraph workflow based on human input.
    """
    thread_config = {"configurable": {"thread_id": plan_id}}
    snapshot = travel_planner_app.get_state(thread_config)

    if not snapshot or not snapshot.values:
        raise HTTPException(status_code=404, detail=f"Travel plan ID '{plan_id}' not found.")

    current_state = snapshot.values
    if current_state.get("stage") == "FINALIZED":
        raise HTTPException(status_code=400, detail="Plan is already finalized. No further reviews permitted.")

    # Update state with latest review feedback
    review_payload = {
        "latest_review": review.model_dump()
    }
    
    travel_planner_app.update_state(thread_config, review_payload)

    # Resume graph execution (None resumes from current checkpoint)
    try:
        for event in travel_planner_app.stream(None, thread_config):
            pass
    except Exception as e:
        print(f"[POST /plan/review] Resume stream notice: {e}")

    updated_snapshot = travel_planner_app.get_state(thread_config)
    updated_state = updated_snapshot.values if updated_snapshot else {}

    return {
        "plan_id": plan_id,
        "action_taken": review.action,
        "stage": updated_state.get("stage"),
        "status_message": updated_state.get("status_message"),
        "is_finalized": updated_state.get("stage") == "FINALIZED"
    }

@app.get("/plan/{plan_id}/final", tags=["Travel Plan"])
def get_finalized_plan(plan_id: str = Path(..., description="The unique session/plan ID")):
    """
    Retrieve the finalized trip plan. Only available after approval.
    """
    thread_config = {"configurable": {"thread_id": plan_id}}
    snapshot = travel_planner_app.get_state(thread_config)

    if not snapshot or not snapshot.values:
        raise HTTPException(status_code=404, detail=f"Travel plan ID '{plan_id}' not found.")

    state = snapshot.values
    if state.get("stage") != "FINALIZED" or not state.get("final_plan"):
        raise HTTPException(
            status_code=400,
            detail=f"Plan '{plan_id}' is currently in stage '{state.get('stage')}'. Final plan is only available after approval."
        )

    return state.get("final_plan")

@app.get("/", response_class=HTMLResponse, tags=["UI"])
def serve_ui():
    """Serves the main Web UI application."""
    index_path = os.path.join(static_dir, "index.html")
    if os.path.exists(index_path):
        return FileResponse(index_path)
    return "<h1>AI Travel Planner API Running</h1><p>Visit <a href='/docs'>/docs</a> for API documentation.</p>"
