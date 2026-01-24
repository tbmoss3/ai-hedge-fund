"""
LLM-Powered Sentiment Analysis Service.

Replaces keyword-based sentiment with nuanced LLM analysis.
Analyzes news articles to extract sentiment, key themes, and risk factors.
"""

import logging
from typing import Optional
from pydantic import BaseModel, Field

from src.utils.llm import call_llm

logger = logging.getLogger(__name__)


class SentimentAnalysis(BaseModel):
    """Structured output for sentiment analysis."""
    score: float = Field(ge=-1.0, le=1.0, description="Sentiment score from -1 (very negative) to +1 (very positive)")
    confidence: int = Field(ge=0, le=100, description="Confidence in the sentiment assessment 0-100")
    summary: str = Field(description="1-2 sentence summary of overall sentiment")
    key_themes: list[str] = Field(description="3-5 key themes from the news")
    risks_mentioned: list[str] = Field(description="Any risks or concerns mentioned")
    catalysts_mentioned: list[str] = Field(description="Positive catalysts or opportunities mentioned")


def analyze_sentiment(
    ticker: str,
    company_name: str,
    news_articles: list[dict],
    state: Optional[dict] = None,
) -> dict:
    """
    Analyze sentiment from news articles using LLM.

    Args:
        ticker: Stock ticker symbol
        company_name: Company name for context
        news_articles: List of news article dicts with 'title', 'summary', 'date'
        state: Optional agent state for LLM configuration

    Returns:
        Dict with sentiment analysis results
    """
    result = {
        "score": 0.0,
        "confidence": 0,
        "summary": "No news available for analysis",
        "key_themes": [],
        "risks_mentioned": [],
        "catalysts_mentioned": [],
        "articles_analyzed": 0,
    }

    if not news_articles:
        return result

    # Format articles for prompt
    formatted_articles = []
    for i, article in enumerate(news_articles[:10], 1):  # Limit to 10 articles
        title = article.get("title", "")
        summary = article.get("summary", article.get("text", ""))[:500]
        date = article.get("date", article.get("published", ""))
        formatted_articles.append(f"{i}. [{date}] {title}\n   {summary}")

    articles_text = "\n\n".join(formatted_articles)

    prompt = f"""Analyze the sentiment of the following news articles about {company_name} ({ticker}).

Provide a comprehensive sentiment analysis including:
1. Overall sentiment score from -1.0 (very negative) to +1.0 (very positive)
2. Confidence level in your assessment (0-100)
3. Brief summary of the overall sentiment
4. Key themes emerging from the news
5. Any risks or concerns mentioned
6. Positive catalysts or opportunities mentioned

NEWS ARTICLES:
{articles_text}

Respond in JSON format matching the SentimentAnalysis schema."""

    try:
        analysis = call_llm(
            prompt=prompt,
            pydantic_model=SentimentAnalysis,
            agent_name="sentiment_analyzer",
            state=state,
        )

        result = {
            "score": analysis.score,
            "confidence": analysis.confidence,
            "summary": analysis.summary,
            "key_themes": analysis.key_themes,
            "risks_mentioned": analysis.risks_mentioned,
            "catalysts_mentioned": analysis.catalysts_mentioned,
            "articles_analyzed": len(news_articles[:10]),
        }

    except Exception as e:
        logger.error(f"Error in sentiment analysis for {ticker}: {e}")
        result["summary"] = f"Error in analysis: {str(e)}"

    return result


def get_sentiment_label(score: float) -> str:
    """Convert sentiment score to human-readable label."""
    if score >= 0.5:
        return "very_positive"
    elif score >= 0.2:
        return "positive"
    elif score > -0.2:
        return "neutral"
    elif score > -0.5:
        return "negative"
    else:
        return "very_negative"
