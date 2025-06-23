import re
import json
import requests
import yfinance as yf
from datetime import datetime
from textblob import TextBlob
from app.config import redis_client, ALPHA_API_KEY
from app.config import FINNHUB_API_KEY
# === Constants ===
INDIAN_EXCHANGES = ["NSE", "BSE", "NSI", "BOM"]
US_EXCHANGES = ["NYSE", "NASDAQ", "NYSE ARCA", "NYSE MKT"]
INTERNATIONAL_EXCHANGES = US_EXCHANGES + ["LSE", "TSE", "FRA", "SIX"]

# === Mappings ===
INDIAN_STOCK_MAPPING = {
    # Format: "NSE_SYMBOL": ("NSE:SYMBOL", "Company Name", "Exchange")
    "RELIANCE": ("NSE:RELIANCE", "Reliance Industries", "NSE"),
    "TCS": ("NSE:TCS", "Tata Consultancy Services", "NSE"),
    "HDFCBANK": ("NSE:HDFCBANK", "HDFC Bank", "NSE"),
    "INFY": ("NSE:INFY", "Infosys", "NSE"),
    "BHARTIARTL": ("NSE:BHARTIARTL", "Bharti Airtel", "NSE"),
    "ITC": ("NSE:ITC", "ITC Limited", "NSE"),
    "SBIN": ("NSE:SBIN", "State Bank of India", "NSE"),
    "LT": ("NSE:LT", "Larsen & Toubro", "NSE"),
    "HINDUNILVR": ("NSE:HINDUNILVR", "Hindustan Unilever", "NSE"),
    "ICICIBANK": ("NSE:ICICIBANK", "ICICI Bank", "NSE"),
    "KOTAKBANK": ("NSE:KOTAKBANK", "Kotak Mahindra Bank", "NSE"),
    "AXISBANK": ("NSE:AXISBANK", "Axis Bank", "NSE"),
    "ASIANPAINT": ("NSE:ASIANPAINT", "Asian Paints", "NSE"),
    "MARUTI": ("NSE:MARUTI", "Maruti Suzuki India", "NSE"),
    "BAJFINANCE": ("NSE:BAJFINANCE", "Bajaj Finance", "NSE"),
    "M&M": ("NSE:M&M", "Mahindra & Mahindra", "NSE"),
    "TATAMOTORS": ("NSE:TATAMOTORS", "Tata Motors", "NSE"),
    "ULTRACEMCO": ("NSE:ULTRACEMCO", "UltraTech Cement", "NSE"),
    "ADANIENT": ("NSE:ADANIENT", "Adani Enterprises", "NSE"),
    "NTPC": ("NSE:NTPC", "NTPC Ltd", "NSE"),
    "WIPRO": ("NSE:WIPRO", "Wipro Limited", "NSE"),
    "SUNPHARMA": ("NSE:SUNPHARMA", "Sun Pharmaceutical Industries", "NSE"),
    "DRREDDY": ("NSE:DRREDDY", "Dr. Reddy's Laboratories", "NSE"),
    "NESTLEIND": ("NSE:NESTLEIND", "Nestle India", "NSE")
}
INTERNATIONAL_STOCK_MAPPING = {
    "APPLE": ("NASDAQ:AAPL", "Apple Inc", "NASDAQ"),
    "AAPL": ("NASDAQ:AAPL", "Apple Inc", "NASDAQ"),
    "GOOGLE": ("NASDAQ:GOOG", "Alphabet Inc", "NASDAQ"),
    "GOOG": ("NASDAQ:GOOG", "Alphabet Inc", "NASDAQ"),
    "AMZN": ("NASDAQ:AMZN", "Amazon.com", "NASDAQ"),
    "MSFT": ("NASDAQ:MSFT", "Microsoft", "NASDAQ"),
    "MICROSOFT": ("NASDAQ:MSFT", "Microsoft", "NASDAQ"),
    "TSLA": ("NASDAQ:TSLA", "Tesla", "NASDAQ"),
    "META": ("NASDAQ:META", "Meta Platforms", "NASDAQ"),
    "NVDA": ("NASDAQ:NVDA", "NVIDIA", "NASDAQ"),
    "JPM": ("NYSE:JPM", "JPMorgan Chase", "NYSE"),
    "VISA": ("NYSE:V", "Visa Inc", "NYSE"),
    "WALMART": ("NYSE:WMT", "Walmart", "NYSE")
}


# === Utilities ===
def clean_stock_input(input_str: str):
    input_str = input_str.upper().strip()
    removals = ["STOCK", "SHARE", "PRICE", "QUOTE"]
    for word in removals:
        input_str = re.sub(rf'\b{word}\b', '', input_str)
    return re.sub(r'[^A-Z0-9]', '', input_str)


def get_tradingview_symbol(symbol: str, exchange: str) -> str:
    base_symbol = symbol.split('.')[0].upper().strip()
    exchange = exchange.upper().strip()
    if exchange in INDIAN_EXCHANGES:
        return f"NSE:{base_symbol}"
    return f"{exchange}:{base_symbol}"


def get_return(hist, days):
    if len(hist) >= days:
        close_today = hist["Close"].iloc[-1]
        close_then = hist["Close"].iloc[-days]
        change = ((close_today - close_then) / close_then) * 100
        return f"{change:+.2f}%"
    return "N/A"


def format_percent(val):
    return f"{val:.2f}%" if val else "N/A"


def format_market_cap(market_cap):
    if not market_cap:
        return "N/A"
    trillion = 1_000_000_000_000
    billion = 1_000_000_000
    million = 1_000_000
    if market_cap >= trillion:
        return f"${market_cap / trillion:.2f} Trillion"
    elif market_cap >= billion:
        return f"${market_cap / billion:.2f} Billion"
    elif market_cap >= million:
        return f"${market_cap / million:.2f} Million"
    return f"${market_cap}"

def evaluate_trend(data: dict) -> str:
    try:
        returns = []
        for key in ["1d_return", "1w_return", "1m_return", "1y_return"]:
            val = data.get(key, "0").replace("%", "").replace("+", "").strip()
            returns.append(float(val) if val != "N/A" else 0)

        score = sum(returns)

        if score > 5:
            return "positive"
        elif score < -5:
            return "negative"
        else:
            return "neutral"
    except:
        return "neutral"


def format_detailed_stock_info(data: dict) -> str:
    currency = "₹" if data.get("is_indian") else "$"

    return f"""
📈 Stock Information

- 🏷️ Stock Name:         {data.get('stock_name', 'N/A')}
- 💰 Current Price:      {currency}{data.get('current_price', 'N/A')}
- 📉 Day's Range:        {currency}{data.get('day_low', 'N/A')} - {currency}{data.get('day_high', 'N/A')}
- 📆 52-Week Range:      {currency}{data.get('week52_low', 'N/A')} - {currency}{data.get('week52_high', 'N/A')}
- 🏦 Market Cap:         {format_market_cap(data.get('market_cap'))}
- 📊 P/E Ratio:          {data.get('pe_ratio', 'N/A')}
- 💸 Dividend Yield:     {format_percent(data.get('dividend_yield'))}

📉 Recent Performance:
  - 1-Day Return:        {data.get('1d_return', 'N/A')}
  - 1-Week Return:       {data.get('1w_return', 'N/A')}
  - 1-Month Return:      {data.get('1m_return', 'N/A')}
  - 1-Year Return:       {data.get('1y_return', 'N/A')}

🔍 Analyst Recommendations:
  - Buy/Sell Ratings:    {data.get('buy_sell_ratings', 'N/A')}
  - 🎯 Target Price:     {currency}{data.get('target_price', 'N/A')}
"""
def get_finnhub_analyst_rating(symbol: str) -> str:
    try:
        url = f"https://finnhub.io/api/v1/stock/recommendation?symbol={symbol}&token={FINNHUB_API_KEY}"
        response = requests.get(url)
        data = response.json()
        print(f"Finnhub data for {symbol}:", data)  # 🔍 DEBUG LINE

        if isinstance(data, list) and data:
            latest = data[0]
            buy = latest.get("buy", 0)
            hold = latest.get("hold", 0)
            sell = latest.get("sell", 0)
            strong_buy = latest.get("strongBuy", 0)
            strong_sell = latest.get("strongSell", 0)

            return f"{strong_buy + buy} Buy / {hold} Hold / {strong_sell + sell} Sell"
    except Exception as e:
        print(f"Finnhub API error: {e}")
    return "Not available"


# === Stock Data Fetchers ===
def get_indian_stock_data(symbol: str, exchange: str) -> dict:
    try:
        yf_symbol = f"{symbol}.{'NS' if exchange == 'NSE' else 'BO'}"
        ticker = yf.Ticker(yf_symbol)
        hist = ticker.history(period="1y")
        info = ticker.info

        if hist.empty:
            return None

        # Try to extract real analyst ratings (if available)
        try:
            recs = ticker.recommendations
            if recs is not None and not recs.empty:
                latest = recs.tail(30)['To Grade'].value_counts().to_dict()
                buy = latest.get("Buy", 0)
                hold = latest.get("Hold", 0)
                sell = latest.get("Sell", 0)
                rating_str = f"{buy} Buy / {hold} Hold / {sell} Sell"
            else:
                rating_str = "Not available"
        except:
            rating_str = "Not available"

        return {
            "stock_name": info.get("shortName", symbol),
            "current_price": info.get("currentPrice"),
            "day_low": info.get("dayLow"),
            "day_high": info.get("dayHigh"),
            "week52_low": info.get("fiftyTwoWeekLow"),
            "week52_high": info.get("fiftyTwoWeekHigh"),
            "market_cap": info.get("marketCap"),
            "pe_ratio": info.get("trailingPE"),
            "dividend_yield": info.get("dividendYield"),
            "1d_return": get_return(hist, 1),
            "1w_return": get_return(hist, 5),
            "1m_return": get_return(hist, 21),
            "1y_return": get_return(hist, 252),
            "buy_sell_ratings": get_finnhub_analyst_rating(f"{symbol}.NS"),
            "target_price": info.get("targetMeanPrice", "N/A"),
            "symbol": symbol,
            "exchange": exchange,
            "is_indian": True
        }
    except Exception as e:
        print(f"Indian stock error: {e}")
        return None

def get_international_stock_data(symbol: str, exchange: str) -> dict:
    try:
        yf_symbol = symbol if "." not in symbol else symbol.split(".")[0]
        ticker = yf.Ticker(yf_symbol)
        hist = ticker.history(period="1y")
        info = ticker.info

        if hist.empty:
            return None

        return {
            "stock_name": info.get("shortName", symbol),
            "current_price": info.get("currentPrice"),
            "day_low": info.get("dayLow"),
            "day_high": info.get("dayHigh"),
            "week52_low": info.get("fiftyTwoWeekLow"),
            "week52_high": info.get("fiftyTwoWeekHigh"),
            "market_cap": info.get("marketCap"),
            "pe_ratio": info.get("trailingPE"),
            "dividend_yield": info.get("dividendYield"),
            "1d_return": get_return(hist, 1),
            "1w_return": get_return(hist, 5),
            "1m_return": get_return(hist, 21),
            "1y_return": get_return(hist, 252),
            "buy_sell_ratings": get_finnhub_analyst_rating(symbol),
            "target_price": info.get("targetMeanPrice", "N/A"),
            "symbol": symbol,
            "exchange": exchange,
            "is_indian": False
        }
    except Exception as e:
        print(f"International stock error: {e}")
        return None

def generate_investment_advice(data: dict, stock_name: str) -> str:
    currency = "₹" if data.get("is_indian") else "$"
    price = data.get("current_price", "N/A")
    pe = data.get("pe_ratio", "N/A")
    yield_ = format_percent(data.get("dividend_yield"))
    market_cap = format_market_cap(data.get("market_cap"))
    target = data.get("target_price", "N/A")
    rating = data.get("buy_sell_ratings", "N/A")

    ret_1d = data.get("1d_return", "N/A")
    ret_1w = data.get("1w_return", "N/A")
    ret_1m = data.get("1m_return", "N/A")
    ret_1y = data.get("1y_return", "N/A")

    trend_sentiment = evaluate_trend(data)

    advice = f"""To help you decide whether to buy {stock_name} stock, let's look at some key metrics and recent performance:

- 💰 Current Price: {currency}{price}
- 📈 Recent Performance:
    - 1-Day Return: {ret_1d}
    - 1-Week Return: {ret_1w}
    - 1-Month Return: {ret_1m}
    - 1-Year Return: {ret_1y}
- 📊 Analyst Recommendations:
    - Buy/Sell Ratings: {rating}
    - Target Price: {currency}{target}
- 📉 Key Metrics:
    - Market Capitalization: {market_cap}
    - P/E Ratio: {pe}
    - Dividend Yield: {yield_}

Based on this data, {stock_name} has shown **{trend_sentiment}** trends recently. The analyst sentiment indicates a potential {'upside' if 'Buy' in rating else 'neutral or caution'} view.

However, your investment should depend on your financial goals, risk appetite, and time horizon. Always consider diversifying and consult with a financial advisor before making investment decisions."""
    
    return advice



# === Other Utilities ===
def get_stock_sentiment(name: str, exchange: str):
    if exchange in INDIAN_EXCHANGES:
        headlines = [
            f"{name} shows strong performance in Indian markets.",
            f"Analysts bullish on {name} in Q3 results.",
            f"{name} maintains steady growth."
        ]
    else:
        headlines = [
            f"{name} reports earnings beat.",
            f"Institutional investors increasing positions in {name}.",
            f"{name} shows resilience in global markets."
        ]

    score = TextBlob(" ".join(headlines)).sentiment.polarity
    sentiment = "positive" if score > 0.2 else "negative" if score < -0.2 else "neutral"
    return sentiment
