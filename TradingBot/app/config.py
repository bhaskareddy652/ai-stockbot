import os
import redis
import sqlite3
from dotenv import load_dotenv

load_dotenv()


# API keys
COHERE_API_KEY = os.getenv("COHERE_API_KEY")
ALPHA_API_KEY = os.getenv("ALPHA_VANTAGE_API_KEY")
FINNHUB_API_KEY=os.getenv("FINNHUB_API_KEY")

# Redis setup
redis_client = redis.Redis(host='localhost', port=6379, decode_responses=True)

# DB path
DB_PATH = "conversations.db"

def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS conversations (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_input TEXT,
        bot_response TEXT,
        timestamp TEXT,
        symbol TEXT,
        exchange TEXT,
        chart_url TEXT,
        is_indian BOOLEAN
    )''')
    conn.commit()
    conn.close()
