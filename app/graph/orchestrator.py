from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import MemorySaver
from app.models.state import TravelPlanState
from app.graph.nodes import (
    validate_request_node,
    research_node,
    planner_node,
    hitl_approval_node,
    process_feedback_node,
    finalize_plan_node,
    route_after_feedback
)

def build_travel_planner_graph(checkpointer=None):
    """
    Builds the LangGraph StateGraph workflow for travel planning with HITL approval.
    """
    builder = StateGraph(TravelPlanState)

    # 1. Add Nodes
    builder.add_node("validate_request_node", validate_request_node)
    builder.add_node("research_node", research_node)
    builder.add_node("planner_node", planner_node)
    builder.add_node("hitl_approval_node", hitl_approval_node)
    builder.add_node("process_feedback_node", process_feedback_node)
    builder.add_node("finalize_plan_node", finalize_plan_node)

    # 2. Add Edges
    builder.add_edge(START, "validate_request_node")
    builder.add_edge("validate_request_node", "research_node")
    builder.add_edge("research_node", "planner_node")
    builder.add_edge("planner_node", "hitl_approval_node")
    builder.add_edge("hitl_approval_node", "process_feedback_node")

    builder.add_conditional_edges(
        "process_feedback_node",
        route_after_feedback,
        {
            "finalize_plan_node": "finalize_plan_node",
            "planner_node": "planner_node"
        }
    )

    builder.add_edge("finalize_plan_node", END)

    # Use MemorySaver checkpointer if none provided
    cp = checkpointer if checkpointer is not None else MemorySaver()

    # Compile with interrupt BEFORE hitl_approval_node
    # Execution will pause right after planner_node generates the draft itinerary!
    compiled_app = builder.compile(
        checkpointer=cp,
        interrupt_before=["hitl_approval_node"]
    )

    return compiled_app

# Global shared graph instance and checkpointer
memory_checkpointer = MemorySaver()
travel_planner_app = build_travel_planner_graph(memory_checkpointer)
