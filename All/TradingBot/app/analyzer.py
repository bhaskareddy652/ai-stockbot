import re
import json
import cohere
import pyttsx3
import speech_recognition as sr
from datetime import datetime
import sqlite3
from app.config import COHERE_API_KEY, DB_PATH
from app.utils import INDIAN_STOCK_MAPPING, INTERNATIONAL_STOCK_MAPPING

class StockAnalyzer:
    def __init__(self):
        self.co = cohere.Client(COHERE_API_KEY)
        self.engine = pyttsx3.init()
        self.engine.setProperty('rate', 150)
        self.recognizer = sr.Recognizer()

        self.company_name_mapping = {
            **{v[1].upper(): k for k, v in INDIAN_STOCK_MAPPING.items()},
            **{v[1].upper(): k for k, v in INTERNATIONAL_STOCK_MAPPING.items()},
            "APPLE": "AAPL", "GOOGLE": "GOOG", "TESLA": "TSLA", "META": "META",
            "FACEBOOK": "META", "TCS": "TCS", "INFOSYS": "INFY", "RELIANCE": "RELIANCE"
        }

    def extract_stock_info(self, query: str):
        query = query.upper().strip()
        if query in INDIAN_STOCK_MAPPING:
            return self._prepare_stock_info(query, is_indian=True)
        if query in INTERNATIONAL_STOCK_MAPPING:
            return self._prepare_stock_info(query, is_indian=False)
        for name, symbol in self.company_name_mapping.items():
            if name in query:
                if symbol in INDIAN_STOCK_MAPPING:
                    return self._prepare_stock_info(symbol, True)
                elif symbol in INTERNATIONAL_STOCK_MAPPING:
                    return self._prepare_stock_info(symbol, False)
        return None

    def _prepare_stock_info(self, symbol: str, is_indian: bool):
        mapping = INDIAN_STOCK_MAPPING if is_indian else INTERNATIONAL_STOCK_MAPPING
        return {
            "symbol": mapping[symbol][0],
            "name": mapping[symbol][1],
            "exchange": mapping[symbol][2],
            "is_indian": is_indian
        }

    def speak_response(self, text: str):
        try:
            self.engine.say(text)
            self.engine.runAndWait()
        except Exception as e:
            print(f"TTS error: {e}")

    def listen_command(self):
        try:
            with sr.Microphone() as source:
                self.recognizer.adjust_for_ambient_noise(source, duration=1)
                audio = self.recognizer.listen(source, timeout=8)
                return self.recognizer.recognize_google(audio)
        except Exception:
            return ""

    def save_conversation(self, user_input, response, metadata):
        try:
            with sqlite3.connect(DB_PATH) as conn:
                c = conn.cursor()
                c.execute("""INSERT INTO conversations 
                             (user_input, bot_response, timestamp, symbol, exchange, chart_url, is_indian) 
                             VALUES (?, ?, ?, ?, ?, ?, ?)""",
                          (user_input, response, datetime.now().isoformat(),
                           metadata.get('symbol'), metadata.get('exchange'),
                           metadata.get('chart_url'), metadata.get('is_indian')))
                conn.commit()
        except Exception as e:
            print(f"DB save failed: {e}")
