from typing import Dict, Any, List

class LocalDiningAndEventsRecommenderTool:
    """
    Tool to recommend restaurants, food experiences, and seasonal events matching user interests.
    """

    def get_recommendations(
        self,
        destination: str,
        interests: List[str],
        budget_range: str
    ) -> Dict[str, Any]:
        """
        Returns structured dining and cultural event recommendations.
        """
        dest_lower = destination.lower()
        interests_lower = [i.lower() for i in interests]
        
        dining = []
        events = []

        if "tokyo" in dest_lower or "japan" in dest_lower:
            dining = [
                {"name": "Tsuta Japanese Soba Noodles", "type": "Michelin Ramen", "price": "$$", "highlight": "Truffle oil shoyu ramen"},
                {"name": "Sukiyabashi Jiro / Ginza Sushi", "type": "Traditional Edomae Sushi", "price": "$$$$", "highlight": "Chef's omakase selection"},
                {"name": "Memory Lane (Omoide Yokocho)", "type": "Yakitori & Izakaya", "price": "$$", "highlight": "Atmospheric alleyway dining in Shinjuku"},
                {"name": "Harajuku Street Food", "type": "Crepes & Dessert", "price": "$", "highlight": "Takeshita street crepes & giant cotton candy"}
            ]
            events = [
                {"event": "TeamLab Planets Immersive Digital Art", "type": "Museum & Experience", "season": "Year-round"},
                {"event": "Asakusa Senso-ji Evening Stroll", "type": "Cultural Heritage", "season": "Year-round"},
                {"event": "Shibuya Sky Sunset View", "type": "Observation Deck", "season": "Year-round"}
            ]
        elif "paris" in dest_lower or "france" in dest_lower:
            dining = [
                {"name": "Le Relais de l'Entrecôte", "type": "Classic Bistro", "price": "$$", "highlight": "Steak frites with secret green sauce"},
                {"name": "Du Pain et des Idées", "type": "Artisanal Bakery", "price": "$", "highlight": "Famous Escargot Pistache pastry"},
                {"name": "Le Jules Verne", "type": "Fine Dining", "price": "$$$$", "highlight": "Eiffel Tower panoramic dining"}
            ]
            events = [
                {"event": "Seine River Evening Cruise", "type": "Sightseeing", "season": "Year-round"},
                {"event": "Montmartre Artist Square Walk", "type": "Art & History", "season": "Year-round"}
            ]
        else:
            dining = [
                {"name": f"Central Market Hall in {destination}", "type": "Local Food Hall", "price": "$", "highlight": "Authentic street food and local produce"},
                {"name": f"The Grand Bistro {destination}", "type": "Regional Cuisine", "price": "$$", "highlight": "Traditional recipes with local ingredients"},
                {"name": f"Rooftop Panorama Restaurant", "type": "Fine Dining & Cocktails", "price": "$$$", "highlight": "Sunset skyline views"}
            ]
            events = [
                {"event": f"Old Town Walking Tour in {destination}", "type": "Historical Exploration", "season": "Daily"},
                {"event": f"Local Crafts & Farmers Market", "type": "Cultural Market", "season": "Weekends"}
            ]

        # Customize based on interests
        if any("food" in i or "culinary" in i or "dining" in i for i in interests_lower):
            events.append({"event": f"Guided Food & Tasting Tour", "type": "Gastronomy", "season": "Daily"})

        if any("anime" in i or "pop" in i or "shopping" in i for i in interests_lower):
            events.append({"event": "Akihabara Pop Culture & Electronics District", "type": "Shopping", "season": "Daily"})

        return {
            "destination": destination,
            "recommended_dining": dining,
            "recommended_events": events,
            "dietary_notes": "Vegetarian and vegan options available upon request at selected venues."
        }

dining_events_tool = LocalDiningAndEventsRecommenderTool()
