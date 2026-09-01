from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from app.config import settings
from app.tools.budget_calc_tool import budget_calculator_tool
from app.tools.dining_events_tool import dining_events_tool

class PlannerAgent:
    """
    Itinerary Planner Agent: Constructs structured day-by-day trip plans, budget breakdowns, and packing lists.
    Has access to Budget & Distance Calculator Tool and Dining & Events Tool.
    """

    def create_itinerary(
        self,
        request: Dict[str, Any],
        research_data: Dict[str, Any],
        feedback_history: Optional[List[Dict[str, Any]]] = None,
        latest_review: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        destination = request.get("destination", "")
        start_date = request.get("start_date", "")
        end_date = request.get("end_date", "")
        budget_range = request.get("budget_range", "Moderate")
        interests = request.get("interests", [])
        num_travelers = request.get("num_travelers", 1)
        special_notes = request.get("special_notes", "")

        # Apply modifications if present in latest review
        if latest_review and latest_review.get("modifications"):
            mods = latest_review.get("modifications", {})
            if "budget_range" in mods:
                budget_range = mods["budget_range"]
            if "hotel" in mods:
                special_notes = f"{special_notes} | Preferred hotel: {mods['hotel']}"

        # 1. Execute Budget & Distance Calculator Tool
        budget_logistics = budget_calculator_tool.calculate_budget_and_logistics(
            destination, start_date, end_date, budget_range, num_travelers
        )

        # 2. Execute Dining & Events Recommender Tool
        dining_events = dining_events_tool.get_recommendations(destination, interests, budget_range)

        # 3. Build Day-by-Day Structure
        num_days = budget_logistics.get("num_days", 3)
        attractions = research_data.get("key_attractions", [])
        days_schedule = self._build_daily_schedule(
            destination, num_days, start_date, attractions, dining_events, latest_review
        )

        # 4. Generate Packing List based on Weather & Destination
        weather_info = research_data.get("weather_info", {})
        packing_list = self._generate_packing_list(weather_info, interests)

        # 5. LLM Synthesis for Final Polishing (if LLM key present)
        llm_enhanced_notes = self._enhance_with_llm(destination, request, latest_review)

        draft_itinerary = {
            "title": f"{num_days}-Day Trip to {destination}",
            "destination": destination,
            "dates": f"{start_date} to {end_date}",
            "travelers": num_travelers,
            "budget_summary": budget_logistics,
            "accommodation_recommendation": budget_logistics.get("recommended_hotel_category"),
            "daily_schedule": days_schedule,
            "recommended_dining": dining_events.get("recommended_dining", []),
            "special_events": dining_events.get("recommended_events", []),
            "packing_list": packing_list,
            "local_tips": [
                research_data.get("safety_and_tips", ""),
                weather_info.get("clothing_recommendation", ""),
                f"Transit advice: {budget_logistics.get('recommended_transit_mode')}"
            ],
            "planner_notes": llm_enhanced_notes or "Itinerary generated with optimized spatial flow and travel-time buffering."
        }

        return draft_itinerary

    def _build_daily_schedule(
        self,
        destination: str,
        num_days: int,
        start_date_str: str,
        attractions: list,
        dining_events: dict,
        latest_review: Optional[dict] = None
    ) -> list:
        schedule = []
        start_dt = None
        try:
            start_dt = datetime.strptime(start_date_str, "%Y-%m-%d")
        except Exception:
            start_dt = datetime.now()

        dining_list = dining_events.get("recommended_dining", [])
        mods = latest_review.get("modifications", {}) if latest_review else {}

        for i in range(num_days):
            current_dt = start_dt + timedelta(days=i)
            day_num = i + 1
            day_key = f"day_{day_num}"
            date_formatted = current_dt.strftime("%A, %b %d")

            # Check if specific modification exists for this day
            custom_mod = mods.get(day_key) or mods.get(f"day_{day_num}_activity")

            att1 = attractions[i % len(attractions)] if attractions else f"Explore Central {destination}"
            att2 = attractions[(i + 1) % len(attractions)] if attractions else f"Local Market Walk in {destination}"
            lunch_spot = dining_list[i % len(dining_list)]["name"] if dining_list else "Local Bistro"
            dinner_spot = dining_list[(i + 1) % len(dining_list)]["name"] if dining_list else "Traditional Restaurant"

            if i == 0:
                morn = "Arrival, hotel check-in, and orientation walk around neighborhood"
                aft = att1 if not custom_mod else custom_mod
                eve = f"Welcome dinner at {dinner_spot} & scenic evening stroll"
            elif i == num_days - 1:
                morn = att1 if not custom_mod else custom_mod
                aft = "Souvenir shopping & final sightseeing spots"
                eve = f"Farewell dinner at {dinner_spot} & departure prep"
            else:
                morn = att1 if not custom_mod else custom_mod
                aft = f"Visit {att2} and leisure exploration"
                eve = f"Dinner at {dinner_spot} & local nightlife/cultural event"

            schedule.append({
                "day": day_num,
                "date": date_formatted,
                "title": f"Day {day_num}: {morn.split(',')[0]}",
                "morning": morn,
                "lunch": f"Lunch at {lunch_spot}",
                "afternoon": aft,
                "evening": eve,
                "estimated_daily_budget_usd": 120.0
            })

        return schedule

    def _generate_packing_list(self, weather_info: dict, interests: list) -> list:
        base_items = [
            "Passport & travel documents",
            "Universal power adapter & power bank",
            "Comfortable walking shoes / sneakers",
            "Personal toiletries & travel medicine kit",
            "Reusable water bottle & light daypack"
        ]

        clothing_tip = weather_info.get("clothing_recommendation", "")
        if "rain" in clothing_tip.lower() or "umbrella" in clothing_tip.lower():
            base_items.append("Compact umbrella or light rain jacket")
        if "sun" in clothing_tip.lower() or "hot" in clothing_tip.lower():
            base_items.append("Sunglasses, high SPF sunscreen, and brimmed hat")
        if "warm" in clothing_tip.lower() or "winter" in clothing_tip.lower():
            base_items.append("Thermal layers, warm coat, and beanie")

        if any("hiking" in i.lower() or "nature" in i.lower() for i in interests):
            base_items.append("Trail walking shoes & bug repellent spray")

        return base_items

    def _enhance_with_llm(self, destination: str, request: dict, latest_review: Optional[dict]) -> str:
        if settings.OPENAI_API_KEY or settings.GROQ_API_KEY:
            try:
                from langchain_openai import ChatOpenAI
                from langchain_core.messages import HumanMessage
                llm = ChatOpenAI(
                    model=settings.LLM_MODEL if settings.OPENAI_API_KEY else "llama-3.1-70b-versatile",
                    api_key=settings.OPENAI_API_KEY or settings.GROQ_API_KEY,
                    temperature=0.7
                )
                review_context = f"User Review Comments: {latest_review.get('comments')}" if latest_review else "Initial Draft Creation"
                prompt = (
                    f"You are an expert Travel Planner AI. Generate a friendly 2-sentence note to the user about their itinerary for {destination}.\n"
                    f"Context: {review_context}"
                )
                res = llm.invoke([HumanMessage(content=prompt)])
                return res.content
            except Exception as e:
                print(f"[PlannerAgent] LLM notice: {e}")

        if latest_review and latest_review.get("comments"):
            return f"Itinerary updated based on user feedback: '{latest_review.get('comments')}'."
        return "Itinerary crafted with optimal scheduling, local dining highlights, and travel time buffers."

planner_agent = PlannerAgent()
