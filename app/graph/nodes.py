import json
from datetime import datetime
from typing import Dict, Any
from app.models.state import TravelPlanState
from app.agents.research_agent import research_agent
from app.agents.planner_agent import planner_agent

def validate_request_node(state: TravelPlanState) -> Dict[str, Any]:
    """
    Validates travel request inputs and initializes state variables.
    """
    req = state.get("request", {})
    now_str = datetime.now().isoformat()
    
    if not req.get("destination"):
        return {
            "stage": "ERROR",
            "error": "Destination is required.",
            "status_message": "Validation failed: missing destination."
        }
        
    return {
        "stage": "RESEARCHING",
        "status_message": f"Validating request for {req.get('destination')}. Initiating destination research.",
        "created_at": state.get("created_at") or now_str,
        "updated_at": now_str,
        "revision_count": state.get("revision_count", 0),
        "feedback_history": state.get("feedback_history") or []
    }

def research_node(state: TravelPlanState) -> Dict[str, Any]:
    """
    Executes Research Agent to gather destination intelligence.
    """
    req = state.get("request", {})
    res_data = research_agent.run_research(req)
    now_str = datetime.now().isoformat()

    return {
        "research_data": res_data,
        "stage": "PLANNING",
        "status_message": f"Research complete for {req.get('destination')}. Constructing initial day-by-day itinerary.",
        "updated_at": now_str
    }

def planner_node(state: TravelPlanState) -> Dict[str, Any]:
    """
    Executes Itinerary Planner Agent to construct day-by-day trip plan.
    """
    req = state.get("request", {})
    res_data = state.get("research_data", {})
    feedback_hist = state.get("feedback_history", [])
    latest_rev = state.get("latest_review")
    now_str = datetime.now().isoformat()

    draft_plan = planner_agent.create_itinerary(
        request=req,
        research_data=res_data,
        feedback_history=feedback_hist,
        latest_review=latest_rev
    )

    return {
        "draft_itinerary": draft_plan,
        "stage": "AWAITING_APPROVAL",
        "status_message": "Draft itinerary created. Workflow paused awaiting user HITL review (approve, reject, modify).",
        "updated_at": now_str
    }

def hitl_approval_node(state: TravelPlanState) -> Dict[str, Any]:
    """
    Pause point for Human-In-The-Loop review.
    Execution is interrupted prior to or at this node.
    """
    now_str = datetime.now().isoformat()
    return {
        "stage": "AWAITING_APPROVAL",
        "status_message": "Awaiting human review.",
        "updated_at": now_str
    }

def process_feedback_node(state: TravelPlanState) -> Dict[str, Any]:
    """
    Processes human review feedback submitted via API.
    """
    latest = state.get("latest_review", {})
    action = latest.get("action", "approve")
    history = list(state.get("feedback_history", []))
    history.append({
        "timestamp": datetime.now().isoformat(),
        "action": action,
        "comments": latest.get("comments"),
        "modifications": latest.get("modifications")
    })

    rev_count = state.get("revision_count", 0) + 1
    now_str = datetime.now().isoformat()

    if action == "approve":
        return {
            "stage": "FINALIZING",
            "feedback_history": history,
            "revision_count": rev_count,
            "status_message": "Plan approved by user! Finalizing detailed itinerary.",
            "updated_at": now_str
        }
    elif action == "reject":
        return {
            "stage": "REVISING",
            "feedback_history": history,
            "revision_count": rev_count,
            "status_message": f"Plan rejected with feedback: '{latest.get('comments')}'. Routing back to planner for revision.",
            "updated_at": now_str
        }
    else:  # modify
        return {
            "stage": "REVISING",
            "feedback_history": history,
            "revision_count": rev_count,
            "status_message": f"Plan modifications requested: {latest.get('modifications') or latest.get('comments')}. Updating itinerary.",
            "updated_at": now_str
        }

def finalize_plan_node(state: TravelPlanState) -> Dict[str, Any]:
    """
    Finalizes the trip plan and formats markdown output.
    """
    draft = state.get("draft_itinerary", {})
    req = state.get("request", {})
    now_str = datetime.now().isoformat()

    # Generate Markdown Final Output
    markdown_output = generate_final_markdown(req, draft, state.get("research_data", {}))

    final_plan_data = {
        "plan_id": state.get("plan_id"),
        "status": "FINALIZED",
        "request": req,
        "final_plan_markdown": markdown_output,
        "structured_itinerary": draft,
        "total_estimated_cost": f"${draft.get('budget_summary', {}).get('breakdown_usd', {}).get('estimated_grand_total', 'N/A')} USD",
        "packing_list": draft.get("packing_list", []),
        "local_tips": draft.get("local_tips", []),
        "finalized_at": now_str
    }

    return {
        "final_plan": final_plan_data,
        "stage": "FINALIZED",
        "status_message": "Trip plan successfully finalized and approved!",
        "updated_at": now_str
    }

def route_after_feedback(state: TravelPlanState) -> str:
    """
    Conditional edge function routing based on stage after processing feedback.
    """
    stage = state.get("stage")
    if stage == "FINALIZING":
        return "finalize_plan_node"
    return "planner_node"

def generate_final_markdown(request: dict, draft: dict, research: dict) -> str:
    dest = request.get("destination")
    dates = draft.get("dates")
    budget = draft.get("budget_summary", {})
    schedule = draft.get("daily_schedule", [])

    lines = [
        f"# ✈️ Complete Travel Plan: {dest}",
        f"**Dates:** {dates}  ",
        f"**Travelers:** {request.get('num_travelers')} traveler(s)  ",
        f"**Budget Tier:** {request.get('budget_range')}  ",
        f"**Estimated Grand Total:** ${budget.get('breakdown_usd', {}).get('estimated_grand_total', 'N/A')} USD  \n",
        "---",
        "## 🏨 Recommended Accommodation & Transit",
        f"- **Hotel Category:** {draft.get('accommodation_recommendation')}",
        f"- **Local Transportation:** {budget.get('recommended_transit_mode')}  \n",
        "---",
        "## 📅 Day-by-Day Itinerary"
    ]

    for day in schedule:
        lines.extend([
            f"### {day.get('date')} - Day {day.get('day')}",
            f"- **Morning:** {day.get('morning')}",
            f"- **Lunch:** {day.get('lunch')}",
            f"- **Afternoon:** {day.get('afternoon')}",
            f"- **Evening:** {day.get('evening')}\n"
        ])

    lines.extend([
        "---",
        "## 🍽️ Recommended Dining Spots"
    ])

    for restaurant in draft.get("recommended_dining", []):
        lines.append(f"- **{restaurant.get('name')}** ({restaurant.get('type')}, {restaurant.get('price')}): {restaurant.get('highlight')}")

    lines.extend([
        "\n---",
        "## 🧳 Packing Essentials"
    ])
    for item in draft.get("packing_list", []):
        lines.append(f"- [ ] {item}")

    lines.extend([
        "\n---",
        "## 💡 Local Intelligence & Tips"
    ])
    for tip in draft.get("local_tips", []):
        lines.append(f"- {tip}")

    return "\n".join(lines)
