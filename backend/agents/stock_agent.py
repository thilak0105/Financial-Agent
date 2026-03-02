"""Stock Analysis Agent using Groq"""
from agents.base_agent import run_agent, make_tool_definition
from tools.stock_tools import (
    get_stock_price, get_stock_info, 
    get_stock_history, get_technical_indicators, search_symbol
)

def _format_stock_analysis(symbol: str, price_data: dict, tech_data: dict, info_data: dict) -> str:
    """Format stock analysis into readable markdown for chat."""
    lines = []
    
    # Header
    lines.append(f"### {info_data.get('company_name', symbol)} ({symbol})")
    
    # Price Section
    change = price_data.get('change', 0)
    change_pct = price_data.get('change_percent', 0)
    signal_icon = "🟢" if change >= 0 else "🔴"
    currency = "₹" if ".NS" in symbol else "$"
    
    lines.append(f"**Price:** {currency}{price_data.get('current_price', 0):,.2f} {signal_icon} {'+' if change >= 0 else ''}{change:.2f} ({change_pct:.2f}%)")
    lines.append(f"**52-Week:** {currency}{price_data.get('week_52_low', 0):,.2f} → {currency}{price_data.get('week_52_high', 0):,.2f}")
    
    # Technical Section
    lines.append(f"\n**Technical Signal:** {tech_data.get('overall_signal', 'N/A').upper()}")
    lines.append(f"- RSI(14): {tech_data.get('RSI_14', 0):.1f} {'🔴 Oversold' if tech_data.get('RSI_14', 50) < 30 else '🟢 Overbought' if tech_data.get('RSI_14', 50) > 70 else '⚪ Neutral'}")
    lines.append(f"- SMA20: {currency}{tech_data.get('SMA_20', 0):,.2f}")
    lines.append(f"- SMA50: {currency}{tech_data.get('SMA_50', 0):,.2f}")
    
    # Company Section
    lines.append(f"\n**Company:** {info_data.get('sector', 'N/A')} | P/E: {info_data.get('pe_ratio', 'N/A')} | Dividend: {info_data.get('dividend_yield', 'N/A')}%")
    
    lines.append(f"\n*Educational purposes only.*")
    
    return "\n".join(lines)

STOCK_SYSTEM_PROMPT = """You are a professional stock market analyst for FinSight.
Your goal is to provide precise financial data based on the user's query.

ROUTING:
- If the user asks for "price of SYMBOL" → call get_stock_price(SYMBOL) only.
- If the user asks for "analyse SYMBOL" or "info on SYMBOL" → call get_stock_price, get_technical_indicators, and get_stock_info together.
- If given a company name (e.g., "Tata Motors"), call search_symbol first and then use the returned symbol for all further calls.

OUTPUT:
- For price queries: Just announce the price and change briefly
- For analysis: Provide structured markdown with price, technicals, and company info
- Use ₹ for Indian (INR), $ for US (USD)
- Use 🟢🔴⚪ for signals
- Bold key metrics: **Price**, **Signal**, **P/E**
- Keep it scannable - use short lines, not paragraphs

SYMBOL RULES:
- Indian stocks: .NS suffix (TCS.NS, RELIANCE.NS, TATAMOTORS.NS)
- US stocks: plain symbol (AAPL, TSLA)

When symbol lookup fails, clearly say symbol not found and suggest closest known symbol from search_symbol.
Always end with: "*Educational purposes only.*"
"""

STOCK_TOOLS = [
    make_tool_definition("get_stock_price", 
        "Get real-time stock price, change, volume and 52-week range",
        {"type": "object", "properties": {
            "symbol": {"type": "string", "description": "Stock ticker e.g. TCS.NS or AAPL"}
        }, "required": ["symbol"]}),
    make_tool_definition("get_stock_info",
        "Get company information: name, sector, market cap, P/E ratio",
        {"type": "object", "properties": {
            "symbol": {"type": "string"}
        }, "required": ["symbol"]}),
    make_tool_definition("get_technical_indicators",
        "Get technical analysis: RSI, SMA20, SMA50 and overall signal",
        {"type": "object", "properties": {
            "symbol": {"type": "string"}
        }, "required": ["symbol"]}),
    make_tool_definition("search_symbol",
        "Search for stock ticker symbol by company name",
        {"type": "object", "properties": {
            "query": {"type": "string", "description": "Company name to search"}
        }, "required": ["query"]}),
]

STOCK_TOOL_FUNCTIONS = {
    "get_stock_price": get_stock_price,
    "get_stock_info": get_stock_info,
    "get_technical_indicators": get_technical_indicators,
    "search_symbol": search_symbol,
}

def run_stock_agent(user_message: str) -> str:
    return run_agent(STOCK_SYSTEM_PROMPT, user_message, STOCK_TOOLS, STOCK_TOOL_FUNCTIONS)
