from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "openai_key_configured" in data

def test_submit_plan_and_hitl_flow():
    # 1. Submit a travel plan
    payload = {
        "destination": "Kyoto, Japan",
        "start_date": "2026-11-01",
        "end_date": "2026-11-05",
        "budget_range": "Moderate",
        "interests": ["Culture", "Temples", "Food"],
        "num_travelers": 2,
        "special_notes": "Prefers quiet tea houses"
    }
    response = client.post("/plan", json=payload)
    assert response.status_code == 202
    data = response.json()
    assert "plan_id" in data
    plan_id = data["plan_id"]

    # 2. Get Plan Status & Draft Itinerary
    status_res = client.get(f"/plan/{plan_id}")
    assert status_res.status_code == 200
    status_data = status_res.json()
    assert status_data["plan_id"] == plan_id
    assert status_data["stage"] == "AWAITING_APPROVAL"
    assert status_data["draft_itinerary"] is not None
    assert status_data["draft_itinerary"]["destination"] == "Kyoto, Japan"

    # 3. Test Modifying the Plan (HITL Modify Action)
    modify_payload = {
        "action": "modify",
        "comments": "Please add a tea ceremony on Day 2",
        "modifications": {"day_2": "Visit Fushimi Inari & Tea Ceremony"}
    }
    review_res = client.post(f"/plan/{plan_id}/review", json=modify_payload)
    assert review_res.status_code == 200
    review_data = review_res.json()
    assert review_data["action_taken"] == "modify"

    # Verify updated plan details
    updated_status = client.get(f"/plan/{plan_id}")
    assert updated_status.status_code == 200
    assert len(updated_status.json()["feedback_history"]) == 1

    # 4. Test Approving the Plan (HITL Approve Action)
    approve_payload = {"action": "approve"}
    approve_res = client.post(f"/plan/{plan_id}/review", json=approve_payload)
    assert approve_res.status_code == 200
    assert approve_res.json()["is_finalized"] is True

    # 5. Retrieve Final Plan
    final_res = client.get(f"/plan/{plan_id}/final")
    assert final_res.status_code == 200
    final_data = final_res.json()
    assert final_data["status"] == "FINALIZED"
    assert "final_plan_markdown" in final_data
    assert "Kyoto" in final_data["final_plan_markdown"]
