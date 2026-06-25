"""Wyllene Dynasty — S-Tier Exclusive Features."""
import random
from datetime import datetime

class AdvancedFeatures:
    def __init__(self):
        self.black_swans = [
            {"name": "Global Pandemic", "impact": -0.40, "desc": "A worldwide health crisis freezes economies."},
            {"name": "Quantum Computing Breakthrough", "impact": 0.50, "desc": "Tech revolution reshapes all industries."},
            {"name": "Asteroid Mining Rush", "impact": 0.80, "desc": "Space resources flood global markets."},
            {"name": "Global Climate Treaty", "impact": -0.25, "desc": "Carbon taxes reshape energy sector."},
            {"name": "AI Singularity Warning", "impact": 0.35, "desc": "AGI emerges — markets panic then boom."},
            {"name": "Mars Colony Established", "impact": 1.00, "desc": "First permanent settlement on Mars."},
            {"name": "Global Currency Reset", "impact": -0.60, "desc": "Fiat systems collapse — crypto surges."},
        ]
        
        self.political_offices = [
            "City Council", "Mayor", "State Senator", "Governor", 
            "Congressperson", "Senator", "Vice President", "President",
            "UN Ambassador", "World Bank Director"
        ]
        
        self.space_investments = [
            {"name": "Orbital Hotels", "cost": 500000000, "return": 0.30},
            {"name": "Asteroid Mining Co", "cost": 2000000000, "return": 0.80},
            {"name": "Mars Real Estate", "cost": 100000000, "return": 1.50},
            {"name": "Space Tourism Inc", "cost": 300000000, "return": 0.45},
            {"name": "Lunar Factory", "cost": 800000000, "return": 0.55},
        ]
        
        self.art_patronage = [
            {"name": "Renaissance Revival", "cost": 50000000, "prestige": 5000},
            {"name": "Modern Art Museum", "cost": 100000000, "prestige": 8000},
            {"name": "Symphony Orchestra", "cost": 25000000, "prestige": 3000},
            {"name": "Cultural Foundation", "cost": 200000000, "prestige": 15000},
            {"name": "National Monument", "cost": 500000000, "prestige": 25000},
        ]
    
    def trigger_black_swan(self):
        event = random.choice(self.black_swans)
        return {
            "type": "black_swan",
            "name": event["name"],
            "desc": event["desc"],
            "market_impact": event["impact"]
        }
    
    def run_for_office(self, current_office=None):
        if not current_office:
            target = "City Council"
        else:
            idx = self.political_offices.index(current_office) if current_office in self.political_offices else 0
            target = self.political_offices[min(idx + 1, len(self.political_offices) - 1)]
        
        cost = random.randint(1000000, 50000000)
        won = random.random() < 0.4
        
        return {
            "office": target,
            "cost": cost,
            "won": won,
            "message": f"{'🏛️ Elected' if won else '❌ Lost'} {target}! {'Can now influence policy.' if won else 'Campaign cost: $' + f'{cost:,}'}"
        }
    
    def invest_space(self):
        inv = random.choice(self.space_investments)
        return {
            "name": inv["name"],
            "cost": inv["cost"],
            "projected_return": f"{inv['return']*100:.0f}%",
            "message": f"🚀 Invested in {inv['name']}: ${inv['cost']:,}"
        }
    
    def patron_art(self):
        art = random.choice(self.art_patronage)
        return {
            "name": art["name"],
            "cost": art["cost"],
            "prestige": art["prestige"],
            "message": f"🎨 Commissioned {art['name']} — +{art['prestige']:,} prestige"
        }
    
    def succession_war(self, heirs):
        if len(heirs) < 2:
            return {"message": "Not enough heirs for a succession war."}
        
        winner = random.choice(heirs)
        loser = [h for h in heirs if h != winner][0]
        
        return {
            "winner": winner,
            "loser": loser,
            "message": f"⚔️ Succession War! {winner} defeated {loser} for control of the dynasty!",
            "drama": random.choice([
                "A bitter courtroom battle",
                "A hostile takeover",
                "A secret alliance revealed",
                "Public scandal and redemption"
            ])
        }

advanced = AdvancedFeatures()
