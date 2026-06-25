"""Wyllene Private Wealth — Configuration."""

# Invitation tokens
VALID_INVITE_CODES = ["WYLLENE-ALPHA", "WEALTH-2024", "FAMILY-OFFICE"]

# Elite tiers
TIERS = {
    "silver": {"min_balance": 100000, "benefits": ["Basic concierge", "Monthly reports"]},
    "gold": {"min_balance": 500000, "benefits": ["Priority support", "Weekly reports", "Crypto access"]},
    "platinum": {"min_balance": 1000000, "benefits": ["Personal banker", "Daily reports", "All assets"]},
    "diamond": {"min_balance": 5000000, "benefits": ["Dedicated team", "Real-time analytics", "Family office"]},
}

# Asset classes
ASSET_CLASSES = ["Cash", "Stocks", "Bonds", "Crypto", "Real Estate", "Commodities", "Private Equity"]

# Personal banker names
BANKER_NAMES = ["Victoria", "Alexander", "Sebastian", "Isabella", "Maximilian", "Arabella"]

# Concierge services
SERVICES = [
    "Private Jet Booking",
    "Luxury Car Rental",
    "Five-Star Hotel Reservation",
    "Personal Shopper",
    "Event Tickets",
    "Yacht Charter",
    "Wine Acquisition",
    "Art Advisory",
]

# Color scheme
COLORS = {
    "bg": "#0a0a0a",
    "card": "#1a1a1a",
    "gold": "#D4AF37",
    "gold_light": "#F4D03F",
    "text": "#FFFFFF",
    "text_dim": "#AAAAAA",
    "accent": "#1a1a3a",
}
