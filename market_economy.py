"""Wyllene Dynasty — Market Economy."""
import random

class MarketEconomy:
    def __init__(self):
        pass
    
    def generate_market_year(self, year=None):
        types = ["Boom 🚀", "Growth 📈", "Normal 📊"]
        market = random.choice(types)
        rates = {"Boom 🚀": 0.20, "Growth 📈": 0.12, "Normal 📊": 0.06}
        vols = {"Boom 🚀": "High", "Growth 📈": "Medium", "Normal 📊": "Low"}
        return {"market": market, "growth": rates.get(market, 0.05), "volatility": vols.get(market, "Medium")}
    
    def get_market_state(self):
        return self.generate_market_year()
    
    def get_stock_prices(self):
        return [
            {"ticker": "WYLL", "name": "Wyllene Corp", "sector": "Tech", "price": random.randint(100, 500)},
            {"ticker": "DYNA", "name": "Dynasty Holdings", "sector": "Finance", "price": random.randint(200, 600)},
            {"ticker": "LEGC", "name": "Legacy Industries", "sector": "Energy", "price": random.randint(50, 300)},
            {"ticker": "WLTH", "name": "Wealth Capital", "sector": "Finance", "price": random.randint(150, 450)},
        ]
    
    def update_leaderboard(self):
        return [
            {"dynasty": "Malebadi", "wealth": 1250000000, "members": 8, "score": 125000},
            {"dynasty": "Vanderbilt", "wealth": 850000000, "members": 6, "score": 85000},
            {"dynasty": "Rothschild", "wealth": 950000000, "members": 5, "score": 95000},
        ]
    
    def ipo_company(self, founder, business, ticker, sector, price, shares):
        return {"status": "ok", "message": f"🎉 {business} (${ticker}) IPO'd! Raised ${price * shares:,}."}

economy = MarketEconomy()
