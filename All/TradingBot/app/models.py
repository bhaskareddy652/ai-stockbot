from pydantic import BaseModel
from typing import List, Optional

class Query(BaseModel):
    question: str
    voice_mode: Optional[bool] = False

class StockQuery(BaseModel):
    symbol: str
    name: Optional[str] = None
    exchange: str
    question: str
    analyze_sentiment: bool = False

class NewsSummaryRequest(BaseModel):
    articles: List[str]
    symbol: str
