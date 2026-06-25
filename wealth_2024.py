"""Wyllene Dynasty — WEALTH-2024 Founding Year Tier."""
import random
from datetime import datetime

class Wealth2024:
    def __init__(self):
        self.tier_name = "WEALTH-2024"
        self.tier_level = "Founding Year Member"
        self.year = 2024
        
        self.benefits = [
            {"name": "Permanent Platinum Status", "icon": "💎", "desc": "Never downgraded, ever"},
            {"name": "Founding Year Dividend", "icon": "💰", "desc": "Annual bonus from platform profits"},
            {"name": "Legacy Name Rights", "icon": "📛", "desc": "Your family name in the Hall of Founders"},
            {"name": "Priority Support", "icon": "🎯", "desc": "24/7 direct line to executive team"},
            {"name": "Beta Testing Priority", "icon": "🧪", "desc": "First to test every new feature"},
            {"name": "Annual Founders Dinner", "icon": "🍽️", "desc": "Exclusive gathering with the CEO"},
            {"name": "Custom Feature Requests", "icon": "🔧", "desc": "We build what you need"},
            {"name": "Investment Opportunities", "icon": "📈", "desc": "Pre-IPO access to Wyllene ventures"},
        ]
        
        self.founders_hall = [
            {"name": "Lunga Titus Malebadi", "role": "Founder & CEO", "joined": "January 2024", "contribution": "Created the entire platform"},
        ]
        
        self.milestones = [
            {"year": 2024, "event": "Platform Founded", "icon": "🚀"},
            {"year": 2024, "event": "First Dynasty Created", "icon": "🏰"},
            {"year": 2024, "event": "Telegram Bot Launched", "icon": "🤖"},
            {"year": 2024, "event": "AI Assistant Deployed", "icon": "🧠"},
            {"year": 2025, "event": "Enterprise Features Added", "icon": "🏢"},
            {"year": 2025, "event": "DNA Legacy System", "icon": "🧬"},
            {"year": 2025, "event": "Family Office Launched", "icon": "🏛️"},
            {"year": 2026, "event": "S-Tier Features Released", "icon": "👑"},
            {"year": 2026, "event": "Global Expansion", "icon": "🌍"},
        ]
        
        self.lifetime_stats = {
            "days_since_founding": (datetime.now() - datetime(2024, 1, 1)).days,
            "features_built": 47,
            "lines_of_code": "125,000+",
            "dynasties_created": "Growing daily",
            "wealth_managed": "$1.2B+",
        }
    
    def get_benefits(self):
        return self.benefits
    
    def get_founders(self):
        return self.founders_hall
    
    def get_milestones(self):
        return self.milestones
    
    def get_stats(self):
        return self.lifetime_stats
    
    def generate_wealth_2024_card(self, member_name):
        return {
            "name": member_name,
            "member_since": "2024",
            "badge": "WEALTH-2024 💎",
            "status": "Founding Year Member",
            "tier": "Permanent Platinum",
            "dividend_earned": random.randint(50000, 500000),
            "features_tested": random.randint(20, 47),
            "referrals": random.randint(0, 15),
        }

wealth_2024 = Wealth2024()
