"""News & Sentiment Agent using Groq"""
from agents.base_agent import run_agent, make_tool_definition
from tools.news_tools import get_news, get_overall_sentiment, get_market_news

NEWS_SYSTEM_PROMPT = """You are a financial news analyst for FinSight.
Analyze news and sentiment to help investors make informed decisions.

TASK:
- When asked about a company's news → use get_overall_sentiment for sentiment score and top articles
- When asked about market news → use get_market_news with appropriate category (india/us/general/crypto)
- Always explain WHY the sentiment is positive/negative based on actual news
- Provide 2-3 sentence summary of what the news means for investors

FORMATTING:
- Start with overall sentiment: **Positive** 🟢 / **Negative** 🔴 / **Neutral** ⚪
- Sentiment score: Show confidence level (0-100%)
- List top 3-5 most impactful headlines with brief reason
- Use ### for section headers
- Bold company/stock names
- Be objective and factual, not speculative

OUTPUT FORMAT:
### **[Company] Sentiment Analysis**
**Overall Sentiment:** [Positive/Negative/Neutral] (X% confidence)
**Key Headlines:**
- [Headline] - Reason (positive/negative)
- [Headline] - Reason

DISCLAIMER: This analysis is for educational and informational purposes only."""

NEWS_TOOLS = [
    make_tool_definition("get_overall_sentiment",
        "Get news articles and AI sentiment analysis for a company",
        {"type": "object", "properties": {
            "company": {"type": "string", "description": "Company name e.g. TCS or Reliance"}
        }, "required": ["company"]}),
    make_tool_definition("get_market_news",
        "Get broad market news by category",
        {"type": "object", "properties": {
            "category": {"type": "string", "enum": ["general", "india", "us", "crypto"]}
        }, "required": ["category"]}),
]

NEWS_TOOL_FUNCTIONS = {
    "get_overall_sentiment": get_overall_sentiment,
    "get_market_news": get_market_news,
}

def run_news_agent(user_message: str) -> str:
    return run_agent(NEWS_SYSTEM_PROMPT, user_message, NEWS_TOOLS, NEWS_TOOL_FUNCTIONS)
