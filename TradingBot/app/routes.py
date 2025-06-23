from fastapi import APIRouter, Request
from datetime import datetime
from app.models import Query
from app.analyzer import StockAnalyzer
from app.config import COHERE_API_KEY
import cohere

from app.utils import (
    get_indian_stock_data, get_international_stock_data,
    get_stock_sentiment, format_detailed_stock_info, generate_investment_advice
)
from app.intent_router import detect_intent

co = cohere.Client(COHERE_API_KEY)
router = APIRouter()
analyzer = StockAnalyzer()

@router.post("/ask")
async def ask(query: Query):
    try:
        user_input = query.question.strip()

        if query.voice_mode and not user_input:
            user_input = analyzer.listen_command()
            if not user_input:
                return {"response": "Sorry, I didn't catch that. Please try again."}

        # Step 1: Detect intent
        intent = detect_intent(user_input)

        # Step 2: If it's a general question, use Cohere to answer
        if intent in [
            "greeting", "how_to_invest", "portfolio_advice", "market_trend",
            "fundamental_analysis", "technical_analysis", "market_news",
            "investment_mistakes", "risk_tolerance","general"
            ]:

            prompt = f"""You are a helpful and friendly financial assistant.

User asked: "{user_input}"

Reply conversationally, introduce yourself, Respond with clear, practical, and accurate financial advice related to the question, in short form.
Avoid suggesting specific stocks unless asked directly."""
            result = co.generate(model="command-r-plus", prompt=prompt, max_tokens=350)
            return {
                "response": result.generations[0].text.strip(),
                "symbol": None,
                "exchange": None,
                "chart_url": None,
                "sentiment": None,
                "timestamp": datetime.now().isoformat()
            }

        # Step 3: Try to extract stock info
        stock_info = analyzer.extract_stock_info(user_input)
        if not stock_info:
            return {"response": "❌ Could not identify stock. Try asking like: 'TCS stock' or 'AAPL price'"}

        symbol = stock_info['symbol'].split(":")[-1]
        name = stock_info['name']
        exchange = stock_info['exchange']
        is_indian = stock_info['is_indian']

        # Step 4: Get stock data
        stock_data = get_indian_stock_data(symbol, exchange) if is_indian else get_international_stock_data(symbol, exchange)
        if not stock_data:
            return {"response": f"⚠️ Could not fetch data for {name}"}

        stock_data["is_indian"] = is_indian
        detailed = format_detailed_stock_info(stock_data)

        # Step 5: Generate investment advice if intent requires it
        if intent == "buy_advice":
            advice = generate_investment_advice(stock_data, name)
            response = f"{detailed}\n\n🧠 Investment Advice:\n{advice}"
        else:
            response = detailed

        chart_url = f"https://www.tradingview.com/chart/?symbol={stock_info['symbol']}"
        sentiment = get_stock_sentiment(name, exchange)

        analyzer.save_conversation(user_input, response, {
            "symbol": symbol,
            "exchange": exchange,
            "chart_url": chart_url,
            "is_indian": is_indian
        })

        if query.voice_mode:
            analyzer.speak_response(response)

        return {
            "response": response,
            "symbol": symbol,
            "exchange": exchange,
            "chart_url": chart_url,
            "sentiment": sentiment,
            "timestamp": datetime.now().isoformat()
        }

    except Exception as e:
        print(f"Ask route error: {e}")
        return {"response": "⚠️ An error occurred while processing your request.", "error": str(e)}
