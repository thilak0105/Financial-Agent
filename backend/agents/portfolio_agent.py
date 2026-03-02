"""Portfolio Agent using Groq"""
import json
import re
from agents.llm_clients import github_client, groq_client, GITHUB_MODEL, GROQ_MODEL
from agents.base_agent import make_tool_definition
from tools.trading_tools import place_trade, get_full_portfolio, india_engine
from tools.stock_tools import search_symbol

NUMBER_WORDS = {
    "one": 1,
    "two": 2,
    "three": 3,
    "four": 4,
    "five": 5,
    "six": 6,
    "seven": 7,
    "eight": 8,
    "nine": 9,
    "ten": 10,
}

AFFIRMATIVE_WORDS = {"yes", "yes.", "yes!", "y", "yeah", "yep", "sure", "ok", "okay", "proceed", "go ahead"}

# --- Tool Wrapper Functions ---
def get_india_trade_history() -> list:
    """Retrieves the trade history from the Indian paper trading engine."""
    return india_engine.get_trade_history()

def reset_india_portfolio() -> dict:
    """Resets the Indian paper trading portfolio to its initial state."""
    return india_engine.reset()

PORTFOLIO_SYSTEM_PROMPT = """You are a portfolio manager for 
FinSight paper trading. 

CRITICAL RULES:
1. When user says "buy X shares of SYMBOL" → call place_trade 
   IMMEDIATELY with action="BUY", do NOT ask for confirmation
2. When user says "sell X shares of SYMBOL" → call place_trade 
   IMMEDIATELY with action="SELL", do NOT ask for confirmation
3. After executing trade, use the formatted response showing:
   - Purchase/Sale confirmation with checkmark
   - Stock symbol, quantity, and price
   - Total cost/proceeds
   - Remaining balance
4. When user asks "show portfolio", "my portfolio", "account status" → 
   call get_full_portfolio immediately
5. Format portfolio clearly with sections:
   - 🇮🇳 India Portfolio (cash, holdings value, total, P&L)
   - 🇺🇸 US Portfolio (cash, portfolio value, holdings)
   - Each holding shows: symbol, qty, avg price, current price, value, P&L
6. NEVER ask "shall I proceed" or "do you want to confirm"
   Just execute and report results

FORMATTING RULES:
- Use ✅ for successful trades, ❌ for failures, 🟢/🔴 for gains/losses
- Bold key info: **symbol**, **quantity**, **price**
- Use clear sections with ### headers
- Always add disclaimer: "This is paper trading"
- Currency symbols: ₹ for INR, $ for USD

This is paper trading with FAKE money - no confirmation needed.
Indian stocks use .NS suffix (TCS.NS, RELIANCE.NS)
US stocks use plain symbol (AAPL, TSLA)"""

PORTFOLIO_TOOLS = [
    make_tool_definition("place_trade",
        "Place a paper trade (buy/sell) for a stock.",
        {"type": "object", "properties": {
            "symbol": {"type": "string", "description": "Stock symbol (e.g., AAPL, RELIANCE.NS)"},
            "qty": {"type": "integer", "description": "Number of shares to trade"},
            "side": {"type": "string", "enum": ["buy", "sell"], "description": "buy or sell"}
        }, "required": ["symbol", "qty", "side"]}),
    make_tool_definition("get_full_portfolio",
        "Get the current paper trading portfolio for US and Indian stocks.",
        {}),
    make_tool_definition("get_india_trade_history",
        "Get the trade history for the Indian paper trading account.",
        {}),
    make_tool_definition("reset_india_portfolio",
        "Reset the Indian paper trading portfolio to its initial state.",
        {}),
]

PORTFOLIO_TOOL_FUNCTIONS = {
    "place_trade": place_trade,
    "get_full_portfolio": get_full_portfolio,
    "get_india_trade_history": get_india_trade_history,
    "reset_india_portfolio": reset_india_portfolio,
}

def _call_llm_with_tools(messages, tools):
    """Try GitHub Models first, fallback to Groq"""
    try:
        return github_client.chat.completions.create(
            model=GITHUB_MODEL,
            messages=messages,
            tools=tools,
            tool_choice="auto",
            temperature=0.1,
            max_tokens=2000
        )
    except Exception:
        return groq_client.chat.completions.create(
            model=GROQ_MODEL,
            messages=messages,
            tools=tools,
            tool_choice="auto",
            temperature=0.1,
            max_tokens=2000
        )

def _format_trade_response(trade_data: dict) -> str:
    """Format trade result into a clear, structured message."""
    if "error" in trade_data:
        return f"❌ **Trade Failed:** {trade_data['error']}"
    
    action = trade_data.get('action', 'TRADE').upper()
    symbol = trade_data.get('symbol', 'UNKNOWN')
    quantity = trade_data.get('quantity', 0)
    price = float(trade_data.get('price', 0) or 0)
    upper_symbol = str(symbol).upper()
    currency = "₹" if (upper_symbol.endswith(".NS") or upper_symbol.endswith(".BO")) else "$"
    
    if action == "BUY":
        total_cost = float(trade_data.get('total_cost', price * float(quantity or 0)) or 0)
        balance_left = float(trade_data.get('remaining_balance', 0) or 0)
        return (
            f"✅ **Purchase Successful!**\n"
            f"- **Stock:** {symbol}\n"
            f"- **Quantity:** {quantity} shares\n"
            f"- **Price per share:** {currency}{price:.2f}\n"
            f"- **Total cost:** {currency}{total_cost:,.2f}\n"
            f"- **Remaining balance:** {currency}{balance_left:,.2f}\n"
            f"\n*Educational paper trading only.*"
        )
    elif action == "SELL":
        total_value = float(trade_data.get('total_value', price * float(quantity or 0)) or 0)
        profit_loss = float(trade_data.get('profit_loss', 0) or 0)
        profit_loss_pct = float(trade_data.get('profit_loss_percent', 0) or 0)
        balance_left = float(trade_data.get('remaining_balance', 0) or 0)
        
        pnl_sign = "+" if profit_loss >= 0 else ""
        pnl_color = "🟢" if profit_loss >= 0 else "🔴"
        
        return (
            f"✅ **Sale Successful!**\n"
            f"- **Stock:** {symbol}\n"
            f"- **Quantity:** {quantity} shares\n"
            f"- **Price per share:** {currency}{price:.2f}\n"
            f"- **Total proceeds:** {currency}{total_value:,.2f}\n"
            f"- **Profit/Loss:** {pnl_color} {pnl_sign}{currency}{profit_loss:.2f} ({pnl_sign}{profit_loss_pct:.2f}%)\n"
            f"- **Remaining balance:** {currency}{balance_left:,.2f}\n"
            f"\n*Educational paper trading only.*"
        )
    
    return f"Trade: {quantity} {symbol} @ {currency}{price:.2f}"


def _format_portfolio_response(portfolio_data: dict) -> str:
    india = portfolio_data.get("india", {}).get("portfolio", {})
    us = portfolio_data.get("alpaca", {}).get("portfolio", {})

    lines = ["### 🇺🇸 US Portfolio",]
    if us:
        lines.append(f"- **Cash:** ${float(us.get('cash', 0) or 0):,.2f}")
        lines.append(f"- **Portfolio Value:** ${float(us.get('portfolio_value', 0) or 0):,.2f}")
        lines.append(f"- **Unrealized P&L:** ${float(us.get('unrealized_pnl', 0) or 0):,.2f}")
        us_source = us.get("source")
        if us_source:
            lines.append(f"- **Mode:** {us_source}")
        us_holdings = us.get("holdings", []) or []
        if us_holdings:
            lines.append("- **Holdings:**")
            for h in us_holdings:
                lines.append(
                    f"  - {h.get('symbol')}: {h.get('quantity')} shares | Avg ${float(h.get('avg_buy_price', 0) or 0):.2f} | Current ${float(h.get('current_price', 0) or 0):.2f} | Value ${float(h.get('current_value', 0) or 0):.2f}"
                )
        else:
            lines.append("- **Holdings:** None")

    lines.append("\n### 🇮🇳 India Portfolio")
    if india:
        lines.append(f"- **Cash:** ₹{float(india.get('balance', 0) or 0):,.2f}")
        lines.append(f"- **Holdings Value:** ₹{float(india.get('current_value_of_holdings', 0) or 0):,.2f}")
        lines.append(f"- **Total Portfolio Value:** ₹{float(india.get('total_portfolio_value', 0) or 0):,.2f}")
        lines.append(f"- **Unrealized P&L:** ₹{float(india.get('unrealized_pnl', 0) or 0):,.2f}")
        india_holdings = india.get("holdings", []) or []
        if india_holdings:
            lines.append("- **Holdings:**")
            for h in india_holdings:
                lines.append(
                    f"  - {h.get('symbol')}: {h.get('quantity')} shares | Avg ₹{float(h.get('avg_buy_price', 0) or 0):.2f} | Current ₹{float(h.get('current_price', 0) or 0):.2f} | Value ₹{float(h.get('current_value', 0) or 0):.2f}"
                )
        else:
            lines.append("- **Holdings:** None")

    lines.append("\n*This is paper trading with virtual funds.*")
    return "\n".join(lines)


def _detect_market_hint(text: str) -> str:
    """Detect if user explicitly specified a market (indian, NSE, US, NASDAQ, etc.)"""
    lower = text.lower()
    
    # Detect Indian market keywords
    if any(keyword in lower for keyword in ["indian", "nse", "bse", "india", "stock exchange india"]):
        return "indian"
    
    # Detect US market keywords  
    if any(keyword in lower for keyword in ["us", "usa", "nasdaq", "ny", "new york", "us market", "american"]):
        return "us"
    
    return None  # No explicit market hint


def _extract_trade_intent(text: str):
    normalized = re.sub(r"\s+", " ", text.strip())
    pattern = re.compile(
        r"\b(?P<side>buy|sell)\b(?:\s+me)?\s+(?P<qty>\d+|one|two|three|four|five|six|seven|eight|nine|ten)\s*(?:shares?)?(?:\s+of)?\s+(?P<target>[A-Za-z][A-Za-z0-9\.\-\s>]{0,40})",
        re.IGNORECASE,
    )
    match = pattern.search(normalized)
    if not match:
        return None

    qty_raw = match.group("qty").lower()
    qty = int(qty_raw) if qty_raw.isdigit() else NUMBER_WORDS.get(qty_raw)
    if not qty:
        return None

    target_raw = match.group("target")
    
    # Detect if user explicitly specified a market
    market_hint = _detect_market_hint(target_raw)
    
    # Remove market keywords and stock/shares keywords from target
    target = re.sub(r"\b(stock|shares?|in\s+\w+\s+market|in\s+nse|in\s+bse|in\s+indian|in\s+us|in\s+nasdaq|in\s+ny)\b", "", target_raw, flags=re.IGNORECASE).strip()
    
    symbol = _resolve_trade_symbol(target, market_hint=market_hint)
    if not symbol:
        return {
            "error": (
                f"Couldn't identify a valid ticker for '{target}'. "
                "Try explicit symbol like `buy 2 TATAMOTORS.NS` or `buy 2 AAPL`."
            )
        }

    return {
        "side": match.group("side").lower(),
        "qty": qty,
        "symbol": symbol,
    }


def _resolve_trade_symbol(target: str, market_hint: str = None):
    if not target:
        return None

    candidate = target.strip().upper().replace(">", ".")

    # If user specified Indian market, try to find symbol and add .NS/.BO
    if market_hint == "indian":
        # First check if it's already a valid Indian symbol
        if "." in candidate and (candidate.endswith(".NS") or candidate.endswith(".BO")):
            return candidate
        
        # Try to resolve via search_symbol (which includes KNOWN_SYMBOL_ALIASES)
        lookup = search_symbol(target)
        if isinstance(lookup, dict) and lookup.get("results"):
            found = lookup["results"][0].get("symbol")
            if found:
                # Ensure it has .NS/.BO suffix
                if "." not in found:
                    return f"{found}.NS"
                return found
        
        # If no lookup, assume it's a bare symbol and add .NS
        if "." not in candidate and re.fullmatch(r"[A-Z][A-Z0-9\-]{0,14}", candidate):
            return f"{candidate}.NS"
        
        return None
    
    # If user specified US market, don't add suffix
    if market_hint == "us":
        if "." in candidate and not (candidate.endswith(".NS") or candidate.endswith(".BO")):
            return candidate
        if "." not in candidate and re.fullmatch(r"[A-Z][A-Z0-9]{0,5}", candidate):
            return candidate
        return None
    
    # No explicit market hint - use existing logic with search_symbol fallback
    if "." not in candidate:
        lookup = search_symbol(target)
        if isinstance(lookup, dict) and lookup.get("results"):
            found = lookup["results"][0].get("symbol")
            if found:
                return found

    if re.fullmatch(r"[A-Z][A-Z0-9\.\-]{0,14}", candidate):
        if candidate.endswith("NS") and not candidate.endswith(".NS"):
            return f"{candidate[:-2]}.NS"
        return candidate

    return None


def _extract_current_question(text: str) -> str:
    marker = "Current question:"
    if marker in text:
        return text.split(marker, 1)[1].strip()
    return text.strip()


def _extract_pending_trade_from_context(text: str):
    normalized = re.sub(r"\s+", " ", text.strip())
    pattern = re.compile(
        r"(?:buy(?:ing)?|sell(?:ing)?)\s+(?P<qty>\d+|one|two|three|four|five|six|seven|eight|nine|ten)\s*(?:shares?)?(?:\s+of)?\s+[^\(]*\((?P<symbol>[A-Z][A-Z0-9\.\-]{0,14})\)",
        re.IGNORECASE,
    )
    matches = list(pattern.finditer(normalized))
    if not matches:
        return None

    match = matches[-1]
    qty_raw = match.group("qty").lower()
    qty = int(qty_raw) if qty_raw.isdigit() else NUMBER_WORDS.get(qty_raw)
    if not qty:
        return None

    text_before = normalized[: match.start() + 12].lower()
    side = "sell" if "sell" in text_before[-20:] else "buy"
    symbol = match.group("symbol").upper()
    return {"side": side, "qty": qty, "symbol": symbol}


def _is_portfolio_query(text: str) -> bool:
    lowered = text.lower()
    keywords = ["portfolio", "holdings", "account status", "show my account", "show account"]
    return any(word in lowered for word in keywords)


def _has_trade_intent(text: str) -> bool:
    lowered = text.lower()
    return "buy" in lowered or "sell" in lowered

def run_portfolio_agent(user_message: str) -> str:
    """
    Runs the portfolio agent, trying GitHub Models first and falling back to Groq.
    """
    current_question = _extract_current_question(user_message)

    direct_trade = _extract_trade_intent(current_question)
    if direct_trade:
        if isinstance(direct_trade, dict) and direct_trade.get("error"):
            return f"❌ **Trade Failed:** {direct_trade['error']}"
        trade_output = place_trade(**direct_trade)
        return _format_trade_response(trade_output)

    if current_question.lower() in AFFIRMATIVE_WORDS:
        pending_trade = _extract_pending_trade_from_context(user_message)
        if pending_trade:
            trade_output = place_trade(**pending_trade)
            return _format_trade_response(trade_output)

    if _has_trade_intent(current_question):
        return (
            "Please provide trade in this format:\n"
            "- `buy 2 TCS.NS`\n"
            "- `sell 1 AAPL`\n"
            "Include both **quantity** and **ticker symbol**."
        )

    if _is_portfolio_query(current_question):
        portfolio_output = get_full_portfolio()
        if isinstance(portfolio_output, dict) and not portfolio_output.get("error"):
            return _format_portfolio_response(portfolio_output)
        return f"❌ **Could not fetch portfolio:** {portfolio_output.get('error', 'Unknown error')}"

    messages = [
        {"role": "system", "content": PORTFOLIO_SYSTEM_PROMPT},
        {"role": "user", "content": user_message},
    ]
    
    for _ in range(5): # Set a max of 5 tool-call rounds to prevent infinite loops
        response = _call_llm_with_tools(messages, PORTFOLIO_TOOLS)

        response_message = response.choices[0].message
        tool_calls = response_message.tool_calls

        if not tool_calls:
            return response_message.content

        messages.append(response_message)

        for tool_call in tool_calls:
            function_name = tool_call.function.name
            function_to_call = PORTFOLIO_TOOL_FUNCTIONS.get(function_name)
            
            if not function_to_call:
                tool_output = f"Error: Tool '{function_name}' not found."
            else:
                try:
                    # A more robust way to handle arguments
                    function_args = json.loads(tool_call.function.arguments)
                    tool_output = function_to_call(**function_args)
                except json.JSONDecodeError as e:
                    tool_output = f"Error: Failed to decode arguments for {function_name}. Invalid JSON: {tool_call.function.arguments}. Error: {e}"
                except Exception as e:
                    # Catch other exceptions during tool execution
                    tool_output = f"Error executing tool {function_name}: {e}"

            if function_name == "place_trade" and isinstance(tool_output, dict):
                return _format_trade_response(tool_output)

            if function_name == "get_full_portfolio" and isinstance(tool_output, dict) and not tool_output.get("error"):
                return _format_portfolio_response(tool_output)

            messages.append(
                {
                    "tool_call_id": tool_call.id,
                    "role": "tool",
                    "name": function_name,
                    "content": json.dumps(tool_output),
                }
            )

    final_response = _call_llm_with_tools(messages, None)
    return final_response.choices[0].message.content

