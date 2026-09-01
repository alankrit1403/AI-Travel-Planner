# AI Travel Planner (Multi-Agent System with Human-in-the-Loop Approval)

A state-of-the-art multi-agent travel planning system built with **Python**, **LangGraph**, and **FastAPI**, featuring Human-In-The-Loop (HITL) approval, checkpointer state persistence, real-time web search tools, and an interactive glassmorphic Web UI.

---

## 🌟 Architecture Overview

```mermaid
graph TD
    User([User / Web Client]) -->|1. POST /plan| API[FastAPI Web Server]
    API -->|Initialize Session State| LG[LangGraph Orchestrator]
    
    subgraph LangGraph StateGraph Workflow
        START((Start)) --> Validate[Validate Request Node]
        Validate --> Research[Agent 1: Research Agent]
        
        subgraph Research Tools
            Research <--> SearchTool[Tool 1: Web Search API - Serper / Exa / Tavily]
            Research <--> WeatherTool[Tool 2: Weather & Seasonal Forecast Tool]
        end
        
        Research --> Planner[Agent 2: Itinerary Planner Agent]
        
        subgraph Planner Tools
            Planner <--> CalcTool[Tool 1: Budget & Distance/Transit Calculator]
            Planner <--> DiningTool[Tool 2: Local Dining & Events Recommender]
        end
        
        Planner --> HITL{HITL Approval Interrupt}
        HITL -->|State Persisted in Checkpointer| Paused[Paused State - AWAITING_APPROVAL]
        
        Paused -->|2. POST /plan/{id}/review| ReviewNode[Process HITL Feedback]
        
        ReviewNode -->|Action: Approve| Finalize[Finalize Plan Node]
        ReviewNode -->|Action: Reject / Modify| Planner
        
        Finalize --> END((End - FINALIZED State))
    end
    
    Paused -->|GET /plan/{id}| API
    Finalize -->|3. GET /plan/{id}/final| API
```

---

## 🎯 Key Features & Agent System

1. **LangGraph Orchestrator:**
   - Manages state transitions using `StateGraph`.
   - Utilizes `MemorySaver` checkpointer for state persistence across API pause/resume boundaries.
   - Halts execution prior to finalization using `interrupt_before=["hitl_approval_node"]`.

2. **Agent 1: Research Agent**
   - **Tool 1 (Mandatory Web Search):** Supports **Serper API** (`serper.dev`), **Exa API** (`exa.ai`), Tavily, with automatic destination intelligence fallback if API keys are unconfigured.
   - **Tool 2 (Weather & Seasonal Intelligence):** Connects to Open-Meteo API for live temperature ranges, precipitation probabilities, and seasonal clothing advice.

3. **Agent 2: Itinerary Planner Agent**
   - **Tool 1 (Budget & Logistics Calculator):** Computes accommodation budget tiers, transit modes, daily spending limits, and inter-city transport times.
   - **Tool 2 (Local Dining & Events Recommender):** Recommends curated local restaurants, food markets, and cultural events tailored to user interests.

4. **Human-in-the-Loop (HITL) Workflow:**
   - **Approve:** Accepts the draft itinerary as-is and advances graph execution to generate the finalized plan.
   - **Reject:** Takes mandatory feedback comments and routes execution back to the planner agent for revision.
   - **Modify:** Allows itemized adjustments (e.g. changing hotel tier, swapping day activities) and updates itinerary state.

5. **Interactive Web UI:**
   - Single-page application built with dark glassmorphism styling, live step timeline, day-by-day itinerary cards, review modal, and Markdown exporter.

---

## 🛠️ Project Structure

```
├── app/
│   ├── __init__.py
│   ├── config.py                 # Pydantic Settings & environment vars
│   ├── main.py                   # FastAPI server & route handlers
│   ├── models/
│   │   ├── schema.py             # Pydantic API Request/Response schemas
│   │   └── state.py              # LangGraph TravelPlanState schema
│   ├── tools/
│   │   ├── search_tool.py        # Web Search Tool (Serper, Exa, Tavily, DDG)
│   │   ├── weather_tool.py       # Weather & Seasonal Forecast Tool
│   │   ├── budget_calc_tool.py   # Budget & Transit Logistics Tool
│   │   └── dining_events_tool.py # Dining & Events Recommender Tool
│   ├── agents/
│   │   ├── research_agent.py     # Research Agent logic
│   │   └── planner_agent.py      # Itinerary Planner Agent logic
│   ├── graph/
│   │   ├── nodes.py              # LangGraph node & routing functions
│   │   └── orchestrator.py       # StateGraph builder with HITL interrupt
│   └── static/
│       ├── index.html            # Web UI HTML template
│       ├── style.css             # Glassmorphic CSS styling
│       └── app.js                # Frontend state & API client logic
├── tests/
│   ├── test_api.py               # FastAPI integration tests
│   └── test_graph.py             # LangGraph state machine unit tests
├── .env.example                  # Environment configuration template
├── requirements.txt              # Dependency specifications
└── README.md                     # Documentation & architectural write-up
```

---

## 🚀 Setup & Installation Instructions

### Prerequisites
- **Python 3.10+** installed on your system.

### 1. Clone & Install Dependencies
```bash
# Install required Python packages
py -3.10 -m pip install -r requirements.txt
```

### 2. Configure Environment Variables (Optional)
Copy `.env.example` to `.env`:
```bash
cp .env.example .env
```
Edit `.env` to add your API keys:
```ini
OPENAI_API_KEY="your-openai-api-key"
SERPER_API_KEY="your-serper-api-key"   # Optional: Real-time Serper search
EXA_API_KEY="your-exa-api-key"         # Optional: Real-time Exa search
```
*(Note: If no API keys are provided, the system seamlessly operates using its built-in Smart Agent Synthesizer and Destination Intelligence engine for 100% functional testing out-of-the-box.)*

---

## 🏃 How to Run the Application

Start the FastAPI application using Uvicorn:

```bash
py -3.10 -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Once running:
- **Interactive Web Interface:** Open `http://localhost:8000` in your web browser.
- **Interactive Swagger OpenAPI Docs:** Open `http://localhost:8000/docs`.

---

## 🧪 Running Automated Tests

Run the test suite via pytest:

```bash
py -3.10 -m pytest
```

---

## 📡 API Endpoint Usage & Examples

### 1. Submit New Travel Request (`POST /plan`)
**Request:**
```bash
curl -X POST "http://localhost:8000/plan" \
  -H "Content-Type: application/json" \
  -d '{
    "destination": "Tokyo, Japan",
    "start_date": "2026-10-01",
    "end_date": "2026-10-05",
    "budget_range": "Moderate",
    "interests": ["Food", "Culture", "Anime"],
    "num_travelers": 2,
    "special_notes": "Vegetarian food preferences"
  }'
```
**Response (202 Accepted):**
```json
{
  "plan_id": "a1b2c3d4-e5f6-7890-abcd-1234567890ab",
  "status": "ACCEPTED",
  "stage": "AWAITING_APPROVAL",
  "message": "Travel request accepted. Workflow processed through research and itinerary planning.",
  "poll_url": "/plan/a1b2c3d4-e5f6-7890-abcd-1234567890ab"
}
```

---

### 2. Get Plan Status & Draft (`GET /plan/{id}`)
**Request:**
```bash
curl -X GET "http://localhost:8000/plan/a1b2c3d4-e5f6-7890-abcd-1234567890ab"
```
**Response (200 OK):**
```json
{
  "plan_id": "a1b2c3d4-e5f6-7890-abcd-1234567890ab",
  "stage": "AWAITING_APPROVAL",
  "status_message": "Draft itinerary created. Workflow paused awaiting user HITL review.",
  "request": { "destination": "Tokyo, Japan", "budget_range": "Moderate", "num_travelers": 2 },
  "draft_itinerary": {
    "title": "5-Day Trip to Tokyo, Japan",
    "accommodation_recommendation": "4-Star Hotel / Serviced Apartment in City Center",
    "daily_schedule": [ ... ]
  },
  "is_awaiting_approval": true
}
```

---

### 3. Submit HITL Feedback (`POST /plan/{id}/review`)
#### Option A: Approve As-Is
```bash
curl -X POST "http://localhost:8000/plan/a1b2c3d4-e5f6-7890-abcd-1234567890ab/review" \
  -H "Content-Type: application/json" \
  -d '{ "action": "approve" }'
```

#### Option B: Modify Specific Items
```bash
curl -X POST "http://localhost:8000/plan/a1b2c3d4-e5f6-7890-abcd-1234567890ab/review" \
  -H "Content-Type: application/json" \
  -d '{
    "action": "modify",
    "comments": "Please adjust hotel to 5-star luxury resort and add TeamLab Planets on day 2",
    "modifications": {
      "hotel": "5-Star Luxury Resort",
      "day_2": "Visit TeamLab Planets & Odaiba Waterfront"
    }
  }'
```

#### Option C: Reject with Feedback
```bash
curl -X POST "http://localhost:8000/plan/a1b2c3d4-e5f6-7890-abcd-1234567890ab/review" \
  -H "Content-Type: application/json" \
  -d '{
    "action": "reject",
    "comments": "The daily activity schedule is too packed for 2 travelers. Please lighten the pace."
  }'
```

---

### 4. Retrieve Finalized Plan (`GET /plan/{id}/final`)
**Request:**
```bash
curl -X GET "http://localhost:8000/plan/a1b2c3d4-e5f6-7890-abcd-1234567890ab/final"
```
**Response (200 OK):**
```json
{
  "plan_id": "a1b2c3d4-e5f6-7890-abcd-1234567890ab",
  "status": "FINALIZED",
  "total_estimated_cost": "$1450.0 USD",
  "final_plan_markdown": "# ✈️ Complete Travel Plan: Tokyo, Japan\n...",
  "packing_list": [ "Passport & travel documents", "Universal power adapter", "Comfortable walking shoes" ],
  "local_tips": [ "Transit advice: Public Transport Metro Pass" ]
}
```

---

## 📐 Design Decisions & Architectural Tradeoffs

1. **State Persistence & Interrupt Mechanics:**
   - Used LangGraph's native checkpointer (`MemorySaver`) combined with `interrupt_before=["hitl_approval_node"]`. This guarantees that execution pauses cleanly after draft itinerary generation without holding HTTP connections open. State is saved by `thread_id` (`plan_id`).
2. **Decoupled Specialized Agents:**
   - Separated destination research (Research Agent) from itinerary construction (Planner Agent). This ensures clean separation of concerns and allows caching destination intelligence independently of user schedule preferences.
3. **Graceful Fallbacks & Resilience:**
   - Integrated primary web search APIs (Serper / Exa / Tavily) alongside an offline Destination Intelligence Fallback. This ensures tests pass deterministically without depending on external API rate limits or missing credentials.

---

## 🔮 Production Considerations & Future Improvements

With more development time, the following enhancements would be added for production scale:

1. **Persistent Relational Checkpointer:**
   - Upgrade from `MemorySaver` to `SqliteSaver` or `PostgresSaver` (via `langgraph-checkpoint-postgres`) so plan state survives server restarts across horizontally scaled API workers.
2. **Real-time Server-Sent Events (SSE) / WebSockets:**
   - Stream intermediate agent thoughts and tool calls in real time to the frontend UI as research and planning progress.
3. **Live Booking API Integrations:**
   - Connect Tool 1 & 2 to live flight/hotel pricing APIs (e.g. Amadeus API, Skyscanner, Booking.com) for real-time room availability and flight ticket booking links.
4. **User Authentication & Multi-Tenant Access:**
   - Implement JWT / OAuth2 authentication so users can view saved past trips, bookmark favorite itineraries, and share plan URLs with fellow travelers.
