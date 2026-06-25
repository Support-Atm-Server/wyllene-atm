"""Wyllene Dynasty — Elite Private Wealth Management."""
import random
from datetime import datetime

class PrivateWealth:
    def __init__(self):
        self.bankers = ["Victoria Sterling", "Alexander Blackwood", "Sebastian Goldcrest", 
                       "Isabella Ashford", "Maximilian Windsor", "Arabella Kensington"]
        
        self.exclusive_services = [
            {"name": "Private Jet Charter", "icon": "🛩️", "min_tier": "silver", "desc": "Gulfstream G650 at your command"},
            {"name": "Yacht Acquisition", "icon": "🛥️", "min_tier": "gold", "desc": "Bespoke yacht sourcing"},
            {"name": "Art Advisory", "icon": "🎨", "min_tier": "gold", "desc": "Curate your personal gallery"},
            {"name": "Wine Cellar Management", "icon": "🍷", "min_tier": "platinum", "desc": "Rare vintage procurement"},
            {"name": "Family Office Setup", "icon": "🏛️", "min_tier": "diamond", "desc": "Multi-generational structure"},
            {"name": "Island Acquisition", "icon": "🏝️", "min_tier": "diamond", "desc": "Private island sourcing"},
            {"name": "Space Tourism", "icon": "🚀", "min_tier": "diamond", "desc": "Orbital flight booking"},
        ]
        
        self.tiers = {
            "silver": {"name": "Silver", "icon": "🥈", "min_assets": 100000, "color": "#C0C0C0", "benefits": 3},
            "gold": {"name": "Gold", "icon": "🥇", "min_assets": 500000, "color": "#D4AF37", "benefits": 5},
            "platinum": {"name": "Platinum", "icon": "💎", "min_assets": 1000000, "color": "#E5E4E2", "benefits": 7},
            "diamond": {"name": "Diamond", "icon": "👑", "min_assets": 5000000, "color": "#B9F2FF", "benefits": 10},
        }
        
        self.invite_codes = {
            "WYLLENE-ALPHA": "Founding Member",
            "WEALTH-2024": "Early Adopter",
            "FAMILY-OFFICE": "Family Office",
            "DYNASTY-ELITE": "Dynasty Elite",
            "CHAIRMAN-CIRCLE": "Chairman's Circle",
            "DYNASTY-ELITE": "Dynasty Member",
            "CHAIRMAN-CIRCLE": "Chairman's Circle",
        }
    
    def get_tier(self, net_worth):
        """Determine client tier based on net worth."""
        current = "silver"
        for tier, info in sorted(self.tiers.items(), key=lambda x: x[1]["min_assets"], reverse=True):
            if net_worth >= info["min_assets"]:
                current = tier
                break
        return current
    
    def assign_banker(self):
        """Assign a personal banker."""
        return random.choice(self.bankers)
    
    def get_services(self, tier):
        """Get available services based on tier."""
        tier_order = ["silver", "gold", "platinum", "diamond"]
        available_up_to = tier_order.index(tier) if tier in tier_order else 0
        return [s for s in self.exclusive_services 
                if tier_order.index(s["min_tier"]) <= available_up_to]
    
    def get_portfolio_recommendation(self, net_worth, risk_tolerance=50):
        """Generate a personalized portfolio recommendation."""
        if risk_tolerance > 70:
            return {
                "stocks": 50, "real_estate": 15, "bonds": 5, 
                "crypto": 15, "private_equity": 10, "cash": 5,
                "strategy": "Aggressive Growth 🚀"
            }
        elif risk_tolerance > 40:
            return {
                "stocks": 35, "real_estate": 25, "bonds": 15,
                "crypto": 5, "private_equity": 10, "cash": 10,
                "strategy": "Balanced Growth 📊"
            }
        else:
            return {
                "stocks": 20, "real_estate": 30, "bonds": 25,
                "crypto": 2, "private_equity": 8, "cash": 15,
                "strategy": "Wealth Preservation 🛡️"
            }

wealth = PrivateWealth()
