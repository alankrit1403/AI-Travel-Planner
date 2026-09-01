import uuid
from app.graph import build_travel_planner_graph
from langgraph.checkpoint.memory import MemorySaver

def test_langgraph_workflow_execution():
    checkpointer = MemorySaver()
    app = build_travel_planner_graph(checkpointer)
    
    plan_id = str(uuid.uuid4())
    thread_config = {"configurable": {"thread_id": plan_id}}

    initial_state = {
        "plan_id": plan_id,
        "request": {
            "destination": "Paris, France",
            "start_date": "2026-12-01",
            "end_date": "2026-12-05",
            "budget_range": "Luxury",
            "interests": ["Art", "Fine Dining"],
            "num_travelers": 2
        },
        "stage": "VALIDATING",
        "feedback_history": [],
        "revision_count": 0
    }

    # Step 1: Execute graph until interrupt (interrupt_before hitl_approval_node)
    for event in app.stream(initial_state, thread_config):
        pass

    state_snapshot = app.get_state(thread_config)
    assert state_snapshot.values["stage"] == "AWAITING_APPROVAL"
    assert "draft_itinerary" in state_snapshot.values
    assert state_snapshot.values["draft_itinerary"]["destination"] == "Paris, France"

    # Step 2: Resume with Approval
    app.update_state(thread_config, {"latest_review": {"action": "approve"}})
    for event in app.stream(None, thread_config):
        pass

    final_snapshot = app.get_state(thread_config)
    assert final_snapshot.values["stage"] == "FINALIZED"
    assert "final_plan" in final_snapshot.values
