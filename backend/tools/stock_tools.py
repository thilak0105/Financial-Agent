# finsight/backend/tools/stock_tools.py

"""
This module provides a set of tools for fetching and analyzing stock data using the yfinance library.
It includes functions to get real-time stock prices, historical data, company information,
and technical indicators like SMA and RSI. All functions are designed to be used by the Stock Agent,
handle errors gracefully, and return JSON-serializable dictionaries.
"""

import yfinance as yf
import pandas as pd
import numpy as np
import re


KNOWN_SYMBOL_ALIASES = {
    "reliance": "RELIANCE.NS",
    "tcs": "TCS.NS",
    "infosys": "INFY.NS",
    "infy": "INFY.NS",
    "hdfc bank": "HDFCBANK.NS",
    "hdfc": "HDFCBANK.NS",
    "icici bank": "ICICIBANK.NS",
    "icici": "ICICIBANK.NS",
    "sbi": "SBIN.NS",
    "state bank": "SBIN.NS",
    "tata motors": "TATAMOTORS.NS",
    "tatamotors": "TATAMOTORS.NS",
    "tata steel": "TATASTEEL.NS",
    "tatasteel": "TATASTEEL.NS",
    "nsdl": "NSDL.BO",
    "l&t": "LT.NS",
    "larsen": "LT.NS",
    "axis bank": "AXISBANK.NS",
    "axis": "AXISBANK.NS",
    "apple": "AAPL",
    "google": "GOOGL",
    "microsoft": "MSFT",
    "tesla": "TSLA",
    "amazon": "AMZN",
}


def _normalize_symbol_input(symbol: str) -> str:
    text = str(symbol or "").strip().upper()
    text = text.replace(">", ".")
    text = re.sub(r"\s+", "", text)
    text = re.sub(r"[^A-Z0-9\.\-]", "", text)
    if text.endswith("NS") and not text.endswith(".NS") and len(text) > 2:
        text = f"{text[:-2]}.NS"
    return text


def _symbol_candidates(symbol: str) -> list[str]:
    raw = str(symbol or "").strip()
    cleaned_key = re.sub(r"\s+", " ", raw.lower()).strip()
    normalized = _normalize_symbol_input(raw)

    candidates = []
    if cleaned_key in KNOWN_SYMBOL_ALIASES:
        candidates.append(KNOWN_SYMBOL_ALIASES[cleaned_key])

    if normalized:
        candidates.append(normalized)
        if "." not in normalized and normalized.isalnum():
            candidates.append(f"{normalized}.NS")
            candidates.append(f"{normalized}.BO")
        elif normalized.endswith(".NS"):
            candidates.append(normalized[:-3] + ".BO")
        elif normalized.endswith(".BO"):
            candidates.append(normalized[:-3] + ".NS")

    seen = set()
    ordered = []
    for candidate in candidates:
        if candidate and candidate not in seen:
            ordered.append(candidate)
            seen.add(candidate)
    return ordered


def _resolve_symbol(symbol: str) -> str:
    candidates = _symbol_candidates(symbol)
    if not candidates:
        return _normalize_symbol_input(symbol)

    for candidate in candidates:
        try:
            ticker = yf.Ticker(candidate)
            info = ticker.info or {}
            if info.get("regularMarketPrice") is not None or info.get("longName"):
                return candidate

            history = ticker.history(period="5d")
            if not history.empty:
                return candidate
        except Exception:
            continue

    return candidates[0]

def get_stock_price(symbol: str) -> dict:
    """
    Fetches the latest stock price data for a given symbol.

    Args:
        symbol (str): The stock symbol (e.g., "AAPL", "RELIANCE.NS").

    Returns:
        dict: A dictionary containing the latest price information or an error message.
    """
    try:
        resolved_symbol = _resolve_symbol(symbol)
        stock = yf.Ticker(resolved_symbol)
        info = {}
        try:
            info = stock.info or {}
        except Exception:
            info = {}

        # yfinance sometimes returns empty dicts for invalid symbols
        if not info or info.get('regularMarketPrice') is None:
            history = stock.history(period="5d", interval="1d")
            if history.empty:
                return {"error": f"Invalid symbol or no data found for {symbol}"}

            closes = history["Close"].dropna()
            highs = history["High"].dropna()
            lows = history["Low"].dropna()
            volumes = history["Volume"].dropna()

            if closes.empty:
                return {"error": f"Invalid symbol or no data found for {symbol}"}

            current_price = float(closes.iloc[-1])
            previous_close = float(closes.iloc[-2]) if len(closes) > 1 else current_price
            change = current_price - previous_close
            change_percent = (change / previous_close * 100) if previous_close else 0.0

            return {
                "symbol": resolved_symbol,
                "current_price": current_price,
                "previous_close": previous_close,
                "change": float(change),
                "change_percent": float(change_percent),
                "volume": int(volumes.iloc[-1]) if not volumes.empty else 0,
                "day_high": float(highs.iloc[-1]) if not highs.empty else current_price,
                "day_low": float(lows.iloc[-1]) if not lows.empty else current_price,
                "week_52_high": float(highs.max()) if not highs.empty else current_price,
                "week_52_low": float(lows.min()) if not lows.empty else current_price,
                "currency": "INR" if resolved_symbol.endswith(".NS") else "USD"
            }

        return {
            "symbol": info.get("symbol") or resolved_symbol,
            "current_price": float(info.get("regularMarketPrice")),
            "previous_close": float(info.get("previousClose")),
            "change": float(info.get("regularMarketPrice", 0) - info.get("previousClose", 0)),
            "change_percent": float(((info.get("regularMarketPrice", 0) - info.get("previousClose", 0)) / info.get("previousClose", 1)) * 100),
            "volume": int(info.get("regularMarketVolume", 0)),
            "day_high": float(info.get("dayHigh", 0)),
            "day_low": float(info.get("dayLow", 0)),
            "week_52_high": float(info.get("fiftyTwoWeekHigh", 0)),
            "week_52_low": float(info.get("fiftyTwoWeekLow", 0)),
            "currency": info.get("currency", "N/A")
        }
    except Exception as e:
        return {"error": f"Failed to fetch stock price for {symbol}: {str(e)}"}

def get_stock_info(symbol: str) -> dict:
    """
    Fetches general company information for a given stock symbol.

    Args:
        symbol (str): The stock symbol.

    Returns:
        dict: A dictionary containing company details or an error message.
    """
    try:
        resolved_symbol = _resolve_symbol(symbol)
        stock = yf.Ticker(resolved_symbol)
        info = stock.info

        if not info or info.get('longName') is None:
            return {"error": f"Invalid symbol or no data found for {symbol}"}

        return {
            "symbol": info.get("symbol") or resolved_symbol,
            "company_name": info.get("longName"),
            "sector": info.get("sector"),
            "industry": info.get("industry"),
            "market_cap": int(info.get("marketCap", 0)),
            "pe_ratio": float(info.get("trailingPE") or info.get("forwardPE") or 0.0),
            "dividend_yield": float(info.get("dividendYield", 0) * 100), # Convert to percentage
            "description": info.get("longBusinessSummary"),
            "country": info.get("country"),
            "website": info.get("website")
        }
    except Exception as e:
        return {"error": f"Failed to fetch stock info for {symbol}: {str(e)}"}

def get_stock_history(symbol: str, period: str = "3mo") -> dict:
    """
    Fetches historical OHLCV data for a given stock symbol.

    Args:
        symbol (str): The stock symbol.
        period (str): The time period for the data (e.g., "1d", "5d", "1mo", "3mo", "6mo", "1y").

    Returns:
        dict: A dictionary containing historical data or an error message.
    """
    try:
        resolved_symbol = _resolve_symbol(symbol)
        stock = yf.Ticker(resolved_symbol)
        history = stock.history(period=period)

        if history.empty:
            return {"error": f"No historical data found for {symbol} for period {period}"}

        # Convert numpy types to native Python types
        history.reset_index(inplace=True)
        history['Date'] = history['Date'].dt.strftime('%Y-%m-%d')
        
        data = history[['Date', 'Open', 'High', 'Low', 'Close', 'Volume']].to_dict('records')
        
        # Clean data from numpy types
        cleaned_data = []
        for record in data:
            cleaned_record = {k: (float(v) if isinstance(v, (np.number, float)) else (int(v) if isinstance(v, np.integer) else v)) for k, v in record.items()}
            cleaned_record['date'] = cleaned_record.pop('Date') # Rename key for frontend
            cleaned_data.append(cleaned_record)

        return {
            "symbol": resolved_symbol,
            "period": period,
            "data": cleaned_data
        }
    except Exception as e:
        return {"error": f"Failed to fetch stock history for {symbol}: {str(e)}"}

def get_technical_indicators(symbol: str) -> dict:
    """
    Calculates key technical indicators for a given stock symbol.

    Args:
        symbol (str): The stock symbol.

    Returns:
        dict: A dictionary with technical indicators and an overall signal.
    """
    try:
        resolved_symbol = _resolve_symbol(symbol)
        stock = yf.Ticker(resolved_symbol)
        history = stock.history(period="100d")

        if history.empty or len(history.index) < 20:
            return {"error": f"Not enough historical data to calculate indicators for {symbol}"}

        close_prices = history['Close']
        current_price = close_prices.iloc[-1]

        # SMAs
        sma_20 = close_prices.rolling(window=20).mean().iloc[-1]
        sma_50 = close_prices.rolling(window=50).mean().iloc[-1]

        # RSI
        delta = close_prices.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        rsi_14 = 100 - (100 / (1 + rs.iloc[-1]))

        # Signals
        price_vs_sma20 = "above" if current_price > sma_20 else "below"
        price_vs_sma50 = "above" if current_price > sma_50 else "below"
        
        if rsi_14 > 70:
            rsi_signal = "overbought"
        elif rsi_14 < 30:
            rsi_signal = "oversold"
        else:
            rsi_signal = "neutral"

        # Overall Signal Logic
        if price_vs_sma20 == "above" and price_vs_sma50 == "above" and rsi_signal != "overbought":
            overall_signal = "bullish"
        elif price_vs_sma20 == "below" and price_vs_sma50 == "below" and rsi_signal != "oversold":
            overall_signal = "bearish"
        else:
            overall_signal = "neutral"
            
        summary = f"{resolved_symbol} is trading {'above' if current_price > sma_50 else 'below'} its 50-day SMA and {'above' if current_price > sma_20 else 'below'} its 20-day SMA. The 14-day RSI is {rsi_14:.2f}, indicating a {rsi_signal} condition. The overall short-term outlook is {overall_signal}."

        return {
            "symbol": resolved_symbol,
            "current_price": float(current_price),
            "SMA_20": float(sma_20),
            "SMA_50": float(sma_50),
            "RSI_14": float(rsi_14),
            "price_vs_SMA20": price_vs_sma20,
            "price_vs_SMA50": price_vs_sma50,
            "RSI_signal": rsi_signal,
            "overall_signal": overall_signal,
            "summary": summary
        }
    except Exception as e:
        return {"error": f"Failed to calculate technical indicators for {symbol}: {str(e)}"}

def search_symbol(query: str) -> dict:
    """
    Searches for stock symbols based on a company name query.
    Note: yfinance does not have a direct search function. This uses a workaround.
    For production, a dedicated financial API or a pre-compiled list is better.
    This implementation is a placeholder.
    """
    # This is a hardcoded fallback as yfinance has no public search API.
    # A real implementation would use a dedicated search provider.
    known_stocks = {
        "reliance": {"symbol": "RELIANCE.NS", "name": "Reliance Industries", "exchange": "NSE"},
        "tcs": {"symbol": "TCS.NS", "name": "Tata Consultancy Services", "exchange": "NSE"},
        "infosys": {"symbol": "INFY.NS", "name": "Infosys", "exchange": "NSE"},
        "infy": {"symbol": "INFY.NS", "name": "Infosys", "exchange": "NSE"},
        "tata motors": {"symbol": "TATAMOTORS.NS", "name": "Tata Motors", "exchange": "NSE"},
        "tatamotors": {"symbol": "TATAMOTORS.NS", "name": "Tata Motors", "exchange": "NSE"},
        "tata steel": {"symbol": "TATASTEEL.NS", "name": "Tata Steel", "exchange": "NSE"},
        "tatasteel": {"symbol": "TATASTEEL.NS", "name": "Tata Steel", "exchange": "NSE"},
        "nsdl": {"symbol": "NSDL.BO", "name": "National Securities Depository Limited", "exchange": "BSE"},
        "hdfc bank": {"symbol": "HDFCBANK.NS", "name": "HDFC Bank", "exchange": "NSE"},
        "hdfc": {"symbol": "HDFCBANK.NS", "name": "HDFC Bank", "exchange": "NSE"},
        "icici bank": {"symbol": "ICICIBANK.NS", "name": "ICICI Bank", "exchange": "NSE"},
        "icici": {"symbol": "ICICIBANK.NS", "name": "ICICI Bank", "exchange": "NSE"},
        "sbi": {"symbol": "SBIN.NS", "name": "State Bank of India", "exchange": "NSE"},
        "state bank": {"symbol": "SBIN.NS", "name": "State Bank of India", "exchange": "NSE"},
        "l&t": {"symbol": "LT.NS", "name": "Larsen & Toubro", "exchange": "NSE"},
        "larsen": {"symbol": "LT.NS", "name": "Larsen & Toubro", "exchange": "NSE"},
        "axis bank": {"symbol": "AXISBANK.NS", "name": "Axis Bank", "exchange": "NSE"},
        "axis": {"symbol": "AXISBANK.NS", "name": "Axis Bank", "exchange": "NSE"},
        "apple": {"symbol": "AAPL", "name": "Apple Inc.", "exchange": "NASDAQ"},
        "google": {"symbol": "GOOGL", "name": "Alphabet Inc.", "exchange": "NASDAQ"},
        "microsoft": {"symbol": "MSFT", "name": "Microsoft Corporation", "exchange": "NASDAQ"},
        "tesla": {"symbol": "TSLA", "name": "Tesla, Inc.", "exchange": "NASDAQ"},
        "amazon": {"symbol": "AMZN", "name": "Amazon.com, Inc.", "exchange": "NASDAQ"},
    }
    
    # Clean query: remove common words like stock, shares, market, etc.
    clean_query = re.sub(r"\b(stock|shares?|in\s+\w+\s+market|in\s+nse|in\s+bse|in\s+indian|in\s+us|in\s+nasdaq|in\s+ny)\b", "", query.lower(), flags=re.IGNORECASE).strip()
    
    results = []
    
    # First try: exact substring or startswith match (handles "sbi" -> finds "sbi" key)
    for name, data in known_stocks.items():
        if clean_query in name.lower() or name.lower().startswith(clean_query):
            results.append(data)
    
    # Second try: token-based matching (if first word matches)
    if not results:
        tokens = clean_query.split()
        if tokens:
            first_token = tokens[0]
            for name, data in known_stocks.items():
                if first_token in name.lower().split():
                    results.append(data)
    
    if not results:
        return {"error": f"No symbols found for query: '{query}'. Try a more specific name."}

    return {
        "query": query,
        "results": results
    }

# Test block
if __name__ == "__main__":
    print("--- Testing get_stock_price ---")
    print("TCS.NS:", get_stock_price("TCS.NS"))
    print("AAPL:", get_stock_price("AAPL"))
    print("INVALID:", get_stock_price("INVALIDSYMBOL"))
    
    print("\n--- Testing get_stock_info ---")
    print("RELIANCE.NS:", get_stock_info("RELIANCE.NS"))

    print("\n--- Testing get_stock_history ---")
    # Limiting output for brevity
    history_data = get_stock_history("INFY.NS", period="5d")
    if 'data' in history_data:
        print("INFY.NS (last 2 days):", history_data['data'][-2:])
    else:
        print("INFY.NS:", history_data)

    print("\n--- Testing get_technical_indicators ---")
    print("RELIANCE.NS:", get_technical_indicators("RELIANCE.NS"))
    
    print("\n--- Testing search_symbol ---")
    print("Reliance:", search_symbol("Reliance"))
    print("Apple:", search_symbol("Apple"))
    print("Unknown:", search_symbol("UnknownCompany"))
