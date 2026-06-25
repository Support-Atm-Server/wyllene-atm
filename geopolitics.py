"""Wyllene Dynasty — Geopolitical Influence System."""
import random
from datetime import datetime

class Geopolitics:
    def __init__(self):
        self.world_events = [
            {"name": "Global Trade War", "desc": "Tariffs escalate between superpowers.", "market": -0.25, "regions": ["All"]},
            {"name": "Peace Treaty Signed", "desc": "A major conflict ends peacefully.", "market": 0.30, "regions": ["Middle East"]},
            {"name": "Tech Cold War", "desc": "Chip sanctions cripple supply chains.", "market": -0.18, "regions": ["Asia"]},
            {"name": "Green Energy Revolution", "desc": "Global shift to renewable energy.", "market": 0.40, "regions": ["Europe"]},
            {"name": "Pandemic Outbreak", "desc": "New virus threatens global health.", "market": -0.35, "regions": ["All"]},
            {"name": "Space Race 2.0", "desc": "Nations compete for orbital dominance.", "market": 0.25, "regions": ["All"]},
            {"name": "Currency Crisis", "desc": "Major fiat currency collapses.", "market": -0.50, "regions": ["South America"]},
            {"name": "AI Arms Race", "desc": "Military AI development accelerates.", "market": 0.15, "regions": ["All"]},
        ]
        
        self.political_actions = [
            {"action": "Lobby Government", "cost": 5000000, "influence": 10, "desc": "Push favorable legislation"},
            {"action": "Fund Political Campaign", "cost": 25000000, "influence": 30, "desc": "Back a presidential candidate"},
            {"action": "Media Takeover", "cost": 100000000, "influence": 50, "desc": "Acquire major news network"},
            {"action": "Trade Deal Negotiation", "cost": 15000000, "influence": 25, "desc": "Secure favorable trade terms"},
            {"action": "Military Contract", "cost": 50000000, "influence": 35, "desc": "Supply armed forces"},
            {"action": "Diplomatic Summit", "cost": 10000000, "influence": 20, "desc": "Host peace negotiations"},
            {"action": "Sanction Rival", "cost": 30000000, "influence": 40, "desc": "Push sanctions against competitor"},
            {"action": "Intelligence Operation", "cost": 20000000, "influence": 30, "desc": "Gather competitor secrets"},
        ]
        
        self.diplomatic_statuses = ["Allied 🤝", "Friendly 😊", "Neutral 😐", "Tense 😤", "Hostile ⚔️", "War 💀"]
    
    def generate_world_event(self):
        """Generate a random world event."""
        event = random.choice(self.world_events)
        event["timestamp"] = datetime.now().strftime("%Y-%m-%d")
        return event
    
    def perform_political_action(self, dynasty_name, action_name, current_wealth):
        """Perform a political action."""
        action = next((a for a in self.political_actions if a["action"] == action_name), None)
        if not action:
            return None
        
        if current_wealth < action["cost"]:
            return {"status": "error", "message": f"Insufficient funds. Need ${action['cost']:,}."}
        
        success = random.random() < 0.7
        influence_gained = action["influence"] if success else action["influence"] // 3
        
        return {
            "status": "ok",
            "action": action["action"],
            "cost": action["cost"],
            "influence_gained": influence_gained,
            "success": success,
            "message": f"{'✅' if success else '❌'} {action['desc']}: {'Success!' if success else 'Partial success.'} +{influence_gained} influence."
        }
    
    def get_diplomatic_relation(self, dynasty1, dynasty2):
        """Get or generate a diplomatic relation between two dynasties."""
        return {
            "status": random.choice(self.diplomatic_statuses),
            "trade_volume": random.randint(0, 100000000),
            "alliance_strength": random.randint(0, 100),
            "conflict_risk": random.randint(0, 100)
        }
    
    def calculate_global_influence(self, dynasty_name, total_wealth, political_actions_count):
        """Calculate a dynasty's global influence score."""
        base = min(100, total_wealth / 10000000)
        political = min(50, political_actions_count * 2)
        return min(100, base + political)

geopolitics = Geopolitics()
