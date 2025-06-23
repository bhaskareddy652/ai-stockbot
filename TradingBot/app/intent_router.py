import re

# === EDUCATIONAL RESPONSES ===
EDUCATIONAL_ANSWERS = {
    "how_to_invest": (
        "To invest in the stock market, open a brokerage account, research companies, and begin with diversified mutual funds or ETFs. "
        "Be patient, stay consistent, and consider long-term strategies."
    ),
    "types_of_stocks": (
        "There are common stocks, preferred stocks, large-cap, mid-cap, small-cap, growth, and value stocks. "
        "Each type has its own risk and reward profile."
    ),
    "market_trend": (
        "The current market trend varies by region and sector. Monitor indices like Nifty, Sensex, Dow Jones, or S&P 500 to assess direction."
    ),
    "market_risks": (
        "Risks include market volatility, economic downturns, interest rate changes, inflation, political instability, and company performance."
    ),
    "stock_chart_reading": (
        "Stock charts display price movement. Look at trends, volume, and indicators like Moving Averages and RSI to interpret patterns."
    ),
    "key_indicators": (
        "Important indicators include GDP, inflation rate, interest rates, unemployment data, and central bank announcements."
    ),
    "diversification": (
        "Diversifying your portfolio means investing across various sectors, asset classes, or geographies to reduce risk."
    ),
    "long_term_investing": (
        "Long-term investing allows compounding returns and reduces the impact of short-term market fluctuations."
    ),
    "risk_tolerance": (
        "Risk tolerance is your ability to endure losses. It depends on age, income, financial goals, and investment timeline."
    ),
    "investment_mistakes": (
        "Avoid emotional trading, timing the market, lack of research, ignoring diversification, and not having a clear goal."
    ),
    "fundamental_analysis": (
        "Fundamental analysis studies a company’s earnings, balance sheet, competitive advantage, and market conditions to assess value."
    ),
    "technical_analysis": (
        "Technical analysis evaluates price patterns, volume, and indicators like MACD, RSI, and Bollinger Bands to forecast movement."
    ),
    "market_news": (
        "News like earnings reports, Fed decisions, geopolitical events, and inflation data can significantly impact stock prices."
    ),
}

# === INTENT DETECTION ===
def detect_intent(user_input: str) -> str:
    input_lower = user_input.lower()

    if re.search(r"^(hi|hello|hey|how are you|who are you|what can you do| can you help me)", input_lower):
        return "greeting"
    elif re.search(r"(should i buy|is .* a good buy|buy .* stock|can i buy)", input_lower):
        return "buy_advice"
    elif re.search(r"(price|current price|stock price)", input_lower):
        return "stock_price"
    elif re.search(r"(market trend|bullish|bearish|sentiment)", input_lower):
        return "market_trend"
    elif re.search(r"(how to invest|invest in stock|start investing)", input_lower):
        return "how_to_invest"
    elif re.search(r"(diversify|portfolio)", input_lower):
        return "portfolio_advice"
    elif re.search(r"(fundamental|valuation|earnings|pe ratio|financial health)", input_lower):
        return "fundamental_analysis"
    elif re.search(r"(technical|chart|resistance|support|indicators|candlestick)", input_lower):
        return "technical_analysis"
    elif re.search(r"(news|events|central bank|inflation|macro|headline)", input_lower):
        return "market_news"
    elif re.search(r"(risk tolerance|risk profile)", input_lower):
        return "risk_tolerance"
    elif re.search(r"(investment mistakes|mistakes to avoid)", input_lower):
        return "investment_mistakes"

    return "general"
