"""Wyllene AI Assistant - Offline banking chatbot."""
import subprocess
import json
import sqlite3
from datetime import datetime

class WylleneAI:
    def __init__(self, model="llama3.2:1b"):
        self.model = model
        self.context = []
        self.max_history = 20
        
        # Banking knowledge base
        self.system_prompt = """You are Wyllene AI, an enterprise banking assistant for Wyllene ATM.
You help with:
- Checking balances and transactions
- Explaining banking features (deposits, withdrawals, transfers, payroll, CEO links)
- Answering questions about account roles (CEO, Manager, Employee)
- Providing financial tips and security advice
- Processing natural language commands like "show my balance" or "deposit 100 dollars"

Keep responses professional, concise, and helpful. If you don't know something, say so politely.
Current date: """ + datetime.now().strftime("%Y-%m-%d %H:%M")
    
    def ask(self, question, username=None):
        """Ask the AI a question and get a response."""
        try:
            # Build the prompt
            prompt = f"{self.system_prompt}\n\n"
            
            # Add user context if available
            if username:
                prompt += f"Current user: {username}\n"
            
            # Add conversation history
            for msg in self.context[-self.max_history:]:
                prompt += f"{msg['role']}: {msg['content']}\n"
            
            # Add the new question
            prompt += f"\nUser: {question}\nAssistant:"
            
            # Call Ollama
            result = subprocess.run(
                ["ollama", "run", self.model, prompt],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            response = result.stdout.strip()
            
            # Store in context
            self.context.append({"role": "user", "content": question})
            self.context.append({"role": "assistant", "content": response})
            
            return response
        
        except subprocess.TimeoutExpired:
            return "I'm taking too long to think. Please try again."
        except Exception as e:
            return f"AI service unavailable: {str(e)}"
    
    def detect_command(self, text):
        """Try to extract banking commands from natural language."""
        text_lower = text.lower()
        
        commands = {
            "balance": ["balance", "how much", "my money", "account"],
            "deposit": ["deposit", "add money", "put in"],
            "withdraw": ["withdraw", "take out", "get cash"],
            "transfer": ["transfer", "send to", "pay"],
            "history": ["history", "transactions", "recent", "statement"],
            "payroll": ["payroll", "salary", "pay employees"],
            "employees": ["employees", "staff", "team", "workers"],
        }
        
        detected = []
        for cmd, keywords in commands.items():
            if any(kw in text_lower for kw in keywords):
                detected.append(cmd)
        
        # Try to extract amounts
        import re
        amounts = re.findall(r'\$?(\d+(?:,\d{3})*(?:\.\d{2})?)', text)
        if amounts:
            detected.append(f"amount:{amounts[0].replace(',','')}")
        
        # Try to extract usernames (words after "to" or "for")
        names = re.findall(r'(?:to|for)\s+(\w+)', text_lower)
        if names:
            detected.append(f"recipient:{names[0]}")
        
        return detected
    
    def save_chat(self, username, question, response):
        """Save chat to database."""
        try:
            conn = sqlite3.connect("atm.db")
            c = conn.cursor()
            c.execute('''CREATE TABLE IF NOT EXISTS ai_chats
                (id INTEGER PRIMARY KEY AUTOINCREMENT,
                 username TEXT, question TEXT, response TEXT,
                 timestamp TEXT DEFAULT CURRENT_TIMESTAMP)''')
            c.execute("INSERT INTO ai_chats (username, question, response) VALUES (?,?,?)",
                      (username, question, response))
            conn.commit()
            conn.close()
        except:
            pass
    
    def get_chat_history(self, username, limit=10):
        """Get chat history for a user."""
        try:
            conn = sqlite3.connect("atm.db")
            conn.row_factory = sqlite3.Row
            c = conn.cursor()
            c.execute("SELECT * FROM ai_chats WHERE username=? ORDER BY id DESC LIMIT ?",
                      (username, limit))
            rows = [dict(row) for row in c.fetchall()]
            conn.close()
            return rows
        except:
            return []
    
    def clear_context(self):
        """Clear conversation history."""
        self.context = []
        return "Conversation cleared."

# Create global AI instance
ai = WylleneAI()
