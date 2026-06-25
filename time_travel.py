"""Wyllene Dynasty — Time Travel Scenarios."""
import random
from datetime import datetime

class TimeTravel:
    def __init__(self):
        self.scenarios = [
            {
                "name": "Great Depression",
                "year": 1929,
                "desc": "The stock market collapses. Banks fail. Unemployment soars to 25%.",
                "impact": -0.89,
                "duration": "4 years",
                "survivors": "Those who held cash and gold.",
                "lesson": "Diversification is survival.",
                "emoji": "📉",
                "color": "#FF4444"
            },
            {
                "name": "Post-War Boom",
                "year": 1950,
                "desc": "World War II ends. Industry explodes. Consumer spending skyrockets.",
                "impact": 2.00,
                "duration": "15 years",
                "survivors": "Industrialists and manufacturers.",
                "lesson": "Innovation drives wealth.",
                "emoji": "📈",
                "color": "#44FF44"
            },
            {
                "name": "Oil Crisis",
                "year": 1973,
                "desc": "OPEC embargo sends oil prices soaring. Gas lines form worldwide.",
                "impact": -0.48,
                "duration": "2 years",
                "survivors": "Energy sector investors.",
                "lesson": "Energy independence matters.",
                "emoji": "⛽",
                "color": "#FF8844"
            },
            {
                "name": "Black Monday",
                "year": 1987,
                "desc": "Stock markets crash 22% in a single day. Panic sweeps globally.",
                "impact": -0.22,
                "duration": "1 day",
                "survivors": "Long-term holders who didn't panic sell.",
                "lesson": "Never panic sell.",
                "emoji": "💀",
                "color": "#FF4444"
            },
            {
                "name": "Dot-Com Bubble",
                "year": 2000,
                "desc": "Tech stocks collapse. Pets.com becomes a punchline. Nasdaq falls 78%.",
                "impact": -0.78,
                "duration": "2 years",
                "survivors": "Companies with real revenue (Amazon survived).",
                "lesson": "Valuation matters.",
                "emoji": "💻",
                "color": "#FF4444"
            },
            {
                "name": "Housing Crisis",
                "year": 2008,
                "desc": "Subprime mortgages implode. Lehman Brothers collapses. Global recession.",
                "impact": -0.57,
                "duration": "3 years",
                "survivors": "Those who shorted the market (The Big Short).",
                "lesson": "When everyone is greedy, be fearful.",
                "emoji": "🏠",
                "color": "#FF4444"
            },
            {
                "name": "Crypto Winter",
                "year": 2022,
                "desc": "Bitcoin crashes 65%. FTX collapses. NFTs become worthless.",
                "impact": -0.65,
                "duration": "18 months",
                "survivors": "Long-term Bitcoin holders.",
                "lesson": "Not your keys, not your coins.",
                "emoji": "₿",
                "color": "#FF8844"
            },
            {
                "name": "AI Revolution",
                "year": 2024,
                "desc": "Artificial intelligence transforms every industry. Tech stocks explode.",
                "impact": 1.50,
                "duration": "Ongoing",
                "survivors": "Early AI investors and innovators.",
                "lesson": "Adapt or become obsolete.",
                "emoji": "🤖",
                "color": "#44FF44"
            },
        ]
    
    def get_all_scenarios(self):
        return self.scenarios
    
    def simulate_scenario(self, scenario_name, current_wealth):
        """Simulate a time travel scenario with current wealth."""
        scenario = next((s for s in self.scenarios if s["name"] == scenario_name), None)
        if not scenario:
            return None
        
        impact = scenario["impact"]
        
        # Add randomness
        variation = random.uniform(-0.15, 0.15)
        actual_impact = impact + variation
        
        new_wealth = current_wealth * (1 + actual_impact)
        change = new_wealth - current_wealth
        survived = new_wealth > 0
        
        return {
            "scenario": scenario,
            "starting_wealth": current_wealth,
            "ending_wealth": max(0, new_wealth),
            "change": change,
            "survived": survived,
            "rating": self._get_rating(actual_impact, survived),
            "message": self._get_message(scenario, survived, change)
        }
    
    def _get_rating(self, impact, survived):
        if not survived:
            return "💀 BANKRUPT"
        if impact > 1.0:
            return "🌟 LEGENDARY"
        if impact > 0.3:
            return "📈 THRIVED"
        if impact > 0:
            return "✅ SURVIVED"
        if impact > -0.3:
            return "😰 STRUGGLED"
        if impact > -0.6:
            return "💸 DEVASTATED"
        return "🏚️ RUINED"
    
    def _get_message(self, scenario, survived, change):
        if not survived:
            return f"Your dynasty was wiped out by the {scenario['name']}. {scenario['lesson']}"
        if change > 0:
            return f"Your dynasty THRIVED during the {scenario['name']}! Wealth grew by ${change:+,.0f}."
        else:
            return f"Your dynasty survived the {scenario['name']} but lost ${abs(change):,.0f}. {scenario['lesson']}"
    
    def get_historical_leaderboard(self, player_results):
        """Generate a leaderboard of how different dynasties would have performed."""
        return sorted(player_results, key=lambda x: x["change"], reverse=True)

time_travel = TimeTravel()
