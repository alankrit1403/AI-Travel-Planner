from typing import Dict, Any, List
from datetime import datetime

class BudgetAndDistanceCalculatorTool:
    """
    Tool for calculating budget allocations, flight/hotel price ranges, and transit logistics.
    """

    def calculate_budget_and_logistics(
        self,
        destination: str,
        start_date: str,
        end_date: str,
        budget_range: str,
        num_travelers: int
    ) -> Dict[str, Any]:
        """
        Calculates trip duration, hotel tier recommendations, daily spending limit, and estimated transit times.
        """
        # Calculate trip duration
        days = 3
        try:
            d1 = datetime.strptime(start_date, "%Y-%m-%d")
            d2 = datetime.strptime(end_date, "%Y-%m-%d")
            delta = (d2 - d1).days + 1
            if delta > 0:
                days = delta
        except Exception:
            days = 5

        budget_lower = budget_range.lower()
        if "budget" in budget_lower or "economy" in budget_lower:
            daily_hotel_per_night = 60.0
            daily_food_per_person = 35.0
            daily_activity_per_person = 25.0
            daily_transit_per_person = 15.0
            hotel_category = "3-Star Boutique Hotel or Hostels (Central & Clean)"
            transit_recommendation = "Public Transport (Metro Pass / City Bus / Walking)"
        elif "luxury" in budget_lower or "premium" in budget_lower or "high" in budget_lower:
            daily_hotel_per_night = 350.0
            daily_food_per_person = 150.0
            daily_activity_per_person = 100.0
            daily_transit_per_person = 60.0
            hotel_category = "5-Star Luxury Resort / Executive Suite"
            transit_recommendation = "Private Airport Transfers & Taxi / Private Driver"
        else: # Moderate / Default
            daily_hotel_per_night = 150.0
            daily_food_per_person = 70.0
            daily_activity_per_person = 50.0
            daily_transit_per_person = 25.0
            hotel_category = "4-Star Hotel / Serviced Apartment in City Center"
            transit_recommendation = "Combination of Express Train / Metro & Rideshare"

        total_hotel = daily_hotel_per_night * max(1, days - 1)
        total_food = daily_food_per_person * days * num_travelers
        total_activities = daily_activity_per_person * days * num_travelers
        total_transit = daily_transit_per_person * days * num_travelers
        grand_total = total_hotel + total_food + total_activities + total_transit

        return {
            "num_days": days,
            "num_travelers": num_travelers,
            "budget_tier": budget_range,
            "recommended_hotel_category": hotel_category,
            "recommended_transit_mode": transit_recommendation,
            "breakdown_usd": {
                "accommodation_total": round(total_hotel, 2),
                "food_and_dining_total": round(total_food, 2),
                "activities_and_entry_fees": round(total_activities, 2),
                "local_transportation": round(total_transit, 2),
                "estimated_grand_total": round(grand_total, 2)
            },
            "per_person_estimated_cost_usd": round(grand_total / max(1, num_travelers), 2),
            "typical_transit_times": {
                "airport_to_city_center": "35 - 50 mins",
                "inter_city_attractions": "15 - 30 mins between major spots"
            }
        }

budget_calculator_tool = BudgetAndDistanceCalculatorTool()
