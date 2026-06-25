"""Wyllene Dynasty — Early Adopter Elite Sector."""
import random
from datetime import datetime

class EarlyAdopter:
    def __init__(self):
        self.founding_members = [
            "Lunga Titus Malebadi — Founder & CEO",
            "The Malebadi Dynasty",
        ]
        
        self.exclusive_perks = [
            {"name": "Lifetime Diamond Tier", "icon": "💎", "desc": "Permanent top-tier status, never downgraded"},
            {"name": "Revenue Sharing", "icon": "💰", "desc": "5% of platform revenue shared among Early Adopters"},
            {"name": "Governance Rights", "icon": "🗳️", "desc": "Vote on new features and platform direction"},
            {"name": "Private API Access", "icon": "🔌", "desc": "Direct API access before public release"},
            {"name": "White-Glove Onboarding", "icon": "🤝", "desc": "Personal setup by the Wyllene team"},
            {"name": "Early Feature Access", "icon": "🚀", "desc": "Test new features 30 days before everyone else"},
            {"name": "Dedicated Slack/Telegram", "icon": "💬", "desc": "Direct line to the development team"},
            {"name": "Custom Integrations", "icon": "🔧", "desc": "We build integrations specifically for you"},
            {"name": "Annual Summit Invite", "icon": "🏔️", "desc": "Exclusive yearly gathering of Early Adopters"},
            {"name": "Legacy Recognition", "icon": "🏆", "desc": "Your name permanently displayed in the platform"},
        ]
        
        self.badges = [
            {"name": "Founding Member", "icon": "👑", "color": "#D4AF37", "desc": "First 10 members"},
            {"name": "Early Adopter", "icon": "🥇", "color": "#C0C0C0", "desc": "First 100 members"},
            {"name": "Beta Tester", "icon": "🧪", "color": "#00FF00", "desc": "Helped test the platform"},
            {"name": "Investor", "icon": "💼", "color": "#2196F3", "desc": "Financial backers"},
        ]
        
        self.roadmap = [
            {"feature": "Native Mobile App", "eta": "Q3 2026", "status": "In Development", "early_access": True},
            {"feature": "Cloud Deployment", "eta": "Q3 2026", "status": "Planning", "early_access": True},
            {"feature": "AI Financial Advisor 2.0", "eta": "Q4 2026", "status": "Research", "early_access": False},
            {"feature": "Blockchain Integration", "eta": "Q4 2026", "status": "Research", "early_access": False},
            {"feature": "Global Stock Exchange", "eta": "Q1 2027", "status": "Concept", "early_access": False},
        ]
    
    def get_perks(self):
        return self.exclusive_perks
    
    def get_badges(self):
        return self.badges
    
    def get_roadmap(self):
        return self.roadmap
    
    def get_founding_members(self):
        return self.founding_members
    
    def generate_early_adopter_card(self, member_name, join_date=None):
        if not join_date:
            join_date = datetime.now().strftime("%B %Y")
        
        badge = random.choice(self.badges)
        
        return {
            "name": member_name,
            "join_date": join_date,
            "badge": badge,
            "member_number": random.randint(1, 100),
            "revenue_share": round(random.uniform(0.1, 1.0), 2),
            "features_tested": random.randint(3, 12),
            "votes_cast": random.randint(5, 50),
        }

early_adopter = EarlyAdopter()
