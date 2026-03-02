# finsight/backend/tools/trading_tools.py

"""
This module provides tools for paper trading with Alpaca and a placeholder
for a real-money Indian trading engine. It allows buying/selling stocks
and retrieving portfolio/trade history.

Requirements:
- pip install alpaca-py python-dotenv

API Keys required in .env:
- ALPACA_API_KEY: Your Alpaca API key
- ALPACA_SECRET_KEY: Your Alpaca API secret key
"""

import os
import json
import re
from pathlib import Path
from dotenv import load_dotenv
from alpaca.trading.client import TradingClient
from alpaca.trading.requests import MarketOrderRequest
from alpaca.trading.enums import OrderSide, TimeInForce

# Load environment variables
load_dotenv()

# --- Alpaca Paper Trading Functions (New) ---

def _is_alpaca_configured() -> bool:
    api_key = os.getenv("ALPACA_API_KEY", "")
    secret_key = os.getenv("ALPACA_SECRET_KEY", "")
    invalid_values = {"", "your_alpaca_api_key_here", "your_alpaca_secret_key_here"}
    return api_key not in invalid_values and secret_key not in invalid_values


def _use_local_us_paper_mode() -> bool:
    mode = os.getenv("US_PAPER_ENGINE", "local").strip().lower()
    return mode in {"local", "sim", "simulation", "fallback", "true", "1"}


def _normalize_trade_symbol(symbol: str) -> str:
    normalized = str(symbol or "").strip().upper()
    normalized = normalized.replace(">", ".")
    normalized = re.sub(r"\s+", "", normalized)
    normalized = re.sub(r"[^A-Z0-9\.\-]", "", normalized)

    if normalized.endswith("NS") and not normalized.endswith(".NS") and len(normalized) > 2:
        normalized = f"{normalized[:-2]}.NS"

    return normalized

def get_alpaca_client():
    """Initializes and returns the Alpaca TradingClient for paper trading."""
    api_key = os.getenv("ALPACA_API_KEY")
    secret_key = os.getenv("ALPACA_SECRET_KEY")
    if not api_key or api_key == "your_alpaca_api_key_here":
        raise ValueError("Alpaca API keys not configured")
    return TradingClient(api_key, secret_key, paper=True)

def alpaca_buy(symbol: str, quantity: int) -> dict:
    """
    Places a market buy order on Alpaca.
    
    Args:
        symbol (str): The stock symbol to buy.
        quantity (int): The number of shares to buy.
        
    Returns:
        dict: A confirmation dictionary or an error dictionary.
    """
    try:
        client = get_alpaca_client()
        order_data = MarketOrderRequest(
            symbol=symbol,
            qty=quantity,
            side=OrderSide.BUY,
            time_in_force=TimeInForce.GTC
        )
        order = client.submit_order(order_data)
        return {
            "status": "success",
            "action": "BUY",
            "symbol": symbol,
            "quantity": quantity,
            "order_id": str(order.id),
            "order_status": str(order.status),
            "timestamp": str(order.submitted_at)
        }
    except Exception:
        return us_engine.buy(symbol, quantity)

def alpaca_sell(symbol: str, quantity: int) -> dict:
    """
    Places a market sell order on Alpaca.
    
    Args:
        symbol (str): The stock symbol to sell.
        quantity (int): The number of shares to sell.
        
    Returns:
        dict: A confirmation dictionary or an error dictionary.
    """
    try:
        client = get_alpaca_client()
        order_data = MarketOrderRequest(
            symbol=symbol,
            qty=quantity,
            side=OrderSide.SELL,
            time_in_force=TimeInForce.GTC
        )
        order = client.submit_order(order_data)
        return {
            "status": "success",
            "action": "SELL",
            "symbol": symbol,
            "quantity": quantity,
            "order_id": str(order.id),
            "order_status": str(order.status),
            "timestamp": str(order.submitted_at)
        }
    except Exception:
        return us_engine.sell(symbol, quantity)

def get_alpaca_portfolio() -> dict:
    """
    Retrieves the current Alpaca paper trading portfolio.
    
    Returns:
        dict: A dictionary with account details and holdings, or an error.
    """
    try:
        if _use_local_us_paper_mode():
            return us_engine.get_portfolio()

        if not _is_alpaca_configured():
            return us_engine.get_portfolio()
        
        client = get_alpaca_client()
        account = client.get_account()
        positions = client.get_all_positions()
        
        holdings = []
        for pos in positions:
            holdings.append({
                "symbol": str(pos.symbol),
                "quantity": float(pos.qty),
                "avg_buy_price": float(pos.avg_entry_price),
                "current_price": float(pos.current_price),
                "current_value": float(pos.market_value),
                "unrealized_pnl": float(pos.unrealized_pl),
                "unrealized_pnl_percent": float(pos.unrealized_plpc) * 100
            })
            
        return {
            "currency": "USD",
            "cash": float(account.cash),
            "portfolio_value": float(account.portfolio_value),
            "unrealized_pnl": sum(h["unrealized_pnl"] for h in holdings),
            "holdings": holdings
        }
    except Exception:
        return us_engine.get_portfolio()

def get_alpaca_trade_history() -> list:
    """
    Retrieves the last 20 trade orders from Alpaca.
    
    Returns:
        list: A list of trade history dictionaries, or a list with an error.
    """
    try:
        if _use_local_us_paper_mode():
            return us_engine.get_trade_history()

        if not _is_alpaca_configured():
            return us_engine.get_trade_history()
        client = get_alpaca_client()
        orders = client.get_orders()
        return [
            {
                "symbol": str(o.symbol),
                "action": str(o.side),
                "quantity": float(o.qty) if o.qty else 0,
                "status": str(o.status),
                "timestamp": str(o.submitted_at)
            }
            for o in orders[:20]
        ]
    except Exception:
        return us_engine.get_trade_history()

# --- Indian Market Engine (Placeholder) ---

class PaperTradingEngine:
    """
    A simple paper trading engine for the Indian market.
    It simulates a portfolio with basic buy/sell logic.
    This is a placeholder and does not connect to a real broker.
    """
    def __init__(self):
        self._state_file = Path(__file__).resolve().parent.parent / "data" / "india_portfolio.json"
        self.balance = 100000.0  # Initial balance of ₹1,00,000
        self.holdings = {}  # e.g., {"TCS.NS": {"quantity": 10, "avg_price": 3800.0}}
        self.trade_history = []
        self._load_state()

    def _save_state(self):
        try:
            self._state_file.parent.mkdir(parents=True, exist_ok=True)
            state = {
                "balance": float(self.balance),
                "holdings": self.holdings,
                "trade_history": self.trade_history,
            }
            self._state_file.write_text(json.dumps(state, ensure_ascii=False, indent=2))
        except Exception as e:
            print(f"[PaperTradingEngine] Failed to save state: {e}")

    def _load_state(self):
        try:
            if not self._state_file.exists():
                return
            state = json.loads(self._state_file.read_text())
            self.balance = float(state.get("balance", 100000.0))
            self.holdings = state.get("holdings", {}) or {}
            self.trade_history = state.get("trade_history", []) or []
        except Exception as e:
            print(f"[PaperTradingEngine] Failed to load state, starting fresh: {e}")
            self.balance = 100000.0
            self.holdings = {}
            self.trade_history = []

    def get_portfolio(self) -> dict:
        try:
            import yfinance as yf
            
            holdings_list = []
            total_current_value = 0.0
            total_invested = 0.0
            
            for symbol, data in self.holdings.items():
                try:
                    ticker = yf.Ticker(symbol)
                    current_price = None
                    try:
                        current_price = ticker.fast_info['lastPrice']
                    except:
                        pass
                    if not current_price:
                        hist = ticker.history(period='1d')
                        if not hist.empty:
                            current_price = float(hist['Close'].iloc[-1])
                        else:
                            current_price = data['avg_buy_price']
                    
                    current_price = float(current_price)
                    qty = data['quantity']
                    avg_price = data['avg_buy_price']
                    current_value = current_price * qty
                    invested = data.get('total_invested', avg_price * qty)
                    unrealized_pnl = current_value - invested
                    unrealized_pct = ((current_price - avg_price) / avg_price) * 100 if avg_price > 0 else 0
                    
                    total_current_value += current_value
                    total_invested += invested
                    
                    holdings_list.append({
                        "symbol": symbol,
                        "quantity": qty,
                        "avg_buy_price": round(avg_price, 2),
                        "current_price": round(current_price, 2),
                        "current_value": round(current_value, 2),
                        "unrealized_pnl": round(unrealized_pnl, 2),
                        "unrealized_pnl_percent": round(unrealized_pct, 2)
                    })
                except Exception as e:
                    # If price fetch fails for one holding, still include it with stored data
                    invested = data.get('total_invested', data['avg_buy_price'] * data['quantity'])
                    total_invested += invested
                    total_current_value += invested # Use invested value as current if price fails
                    holdings_list.append({
                        "symbol": symbol,
                        "quantity": data['quantity'],
                        "avg_buy_price": data['avg_buy_price'],
                        "current_price": data['avg_buy_price'],
                        "current_value": invested,
                        "unrealized_pnl": 0.0,
                        "unrealized_pnl_percent": 0.0,
                        "error": str(e)
                    })
            
            total_unrealized = total_current_value - total_invested
            
            return {
                "balance": round(self.balance, 2),
                "currency": "INR",
                "total_invested": round(total_invested, 2),
                "current_value_of_holdings": round(total_current_value, 2),
                "unrealized_pnl": round(total_unrealized, 2),
                "unrealized_pnl_percent": round(
                    (total_unrealized / total_invested * 100) if total_invested > 0 else 0, 2
                ),
                "total_portfolio_value": round(self.balance + total_current_value, 2),
                "holdings": holdings_list,
                "trade_count": len(self.trade_history)
            }
        except Exception as e:
            return {
                "balance": self.balance,
                "currency": "INR",
                "holdings": [],
                "error": str(e)
            }

    def get_trade_history(self):
        return self.trade_history

    def _get_live_price_with_symbol_fallback(self, symbol: str):
        import yfinance as yf

        candidates = [symbol]
        if symbol.endswith(".NS"):
            candidates.append(symbol[:-3] + ".BO")
        elif symbol.endswith(".BO"):
            candidates.append(symbol[:-3] + ".NS")

        for candidate in candidates:
            try:
                ticker = yf.Ticker(candidate)
                price = None
                try:
                    price = ticker.fast_info['lastPrice']
                except Exception:
                    pass

                if not price:
                    hist = ticker.history(period='1d')
                    if not hist.empty:
                        price = float(hist['Close'].iloc[-1])

                if price and float(price) > 0:
                    return float(price), candidate
            except Exception:
                continue

        return None, symbol

    def buy(self, symbol: str, quantity: int) -> dict:
        try:
            from datetime import datetime

            price, resolved_symbol = self._get_live_price_with_symbol_fallback(symbol)
            if not price:
                return {"error": f"Could not fetch price for {symbol}"}

            quantity = int(quantity)
            total_cost = price * quantity

            if self.balance < total_cost:
                return {
                    "error": f"Insufficient balance. Need ₹{total_cost:.2f} but have ₹{self.balance:.2f}"
                }

            # Execute trade
            self.balance -= total_cost

            if resolved_symbol in self.holdings:
                existing = self.holdings[resolved_symbol]
                total_qty = existing['quantity'] + quantity
                total_invested = existing.get('total_invested', existing['avg_buy_price'] * existing['quantity']) + total_cost
                self.holdings[resolved_symbol] = {
                    'quantity': total_qty,
                    'avg_buy_price': total_invested / total_qty,
                    'total_invested': total_invested
                }
            else:
                self.holdings[resolved_symbol] = {
                    'quantity': quantity,
                    'avg_buy_price': price,
                    'total_invested': total_cost
                }

            trade = {
                "action": "BUY",
                "symbol": resolved_symbol,
                "quantity": quantity,
                "price": price,
                "total_cost": total_cost,
                "remaining_balance": self.balance,
                "timestamp": datetime.now().isoformat()
            }
            self.trade_history.append(trade)
            self._save_state()

            return {
                "status": "success",
                "action": "BUY",
                "symbol": resolved_symbol,
                "quantity": quantity,
                "price": price,
                "total_cost": total_cost,
                "remaining_balance": self.balance,
                "timestamp": trade["timestamp"]
            }
        except Exception as e:
            return {"error": f"Buy failed: {str(e)}"}

    def sell(self, symbol: str, quantity: int) -> dict:
        try:
            from datetime import datetime

            quantity = int(quantity)

            resolved_symbol = symbol
            if symbol not in self.holdings:
                if symbol.endswith(".NS") and (symbol[:-3] + ".BO") in self.holdings:
                    resolved_symbol = symbol[:-3] + ".BO"
                elif symbol.endswith(".BO") and (symbol[:-3] + ".NS") in self.holdings:
                    resolved_symbol = symbol[:-3] + ".NS"

            if resolved_symbol not in self.holdings:
                return {"error": f"You don't own any shares of {symbol}"}

            owned_qty = self.holdings[resolved_symbol]['quantity']
            if owned_qty < quantity:
                return {"error": f"Insufficient shares. You own {owned_qty} but tried to sell {quantity}"}

            price, resolved_symbol = self._get_live_price_with_symbol_fallback(resolved_symbol)
            if not price:
                return {"error": f"Could not fetch price for {symbol}"}

            total_value = price * quantity
            avg_buy = self.holdings[resolved_symbol]['avg_buy_price']
            profit_loss = (price - avg_buy) * quantity
            profit_loss_pct = ((price - avg_buy) / avg_buy) * 100 if avg_buy > 0 else 0

            self.balance += total_value

            if owned_qty == quantity:
                del self.holdings[resolved_symbol]
            else:
                self.holdings[resolved_symbol]['quantity'] -= quantity
                self.holdings[resolved_symbol]['total_invested'] = (
                    self.holdings[resolved_symbol]['avg_buy_price'] * self.holdings[resolved_symbol]['quantity']
                )

            trade = {
                "action": "SELL",
                "symbol": resolved_symbol,
                "quantity": quantity,
                "price": price,
                "total_value": total_value,
                "profit_loss": profit_loss,
                "profit_loss_percent": profit_loss_pct,
                "remaining_balance": self.balance,
                "timestamp": datetime.now().isoformat()
            }
            self.trade_history.append(trade)
            self._save_state()

            return {
                "status": "success",
                "action": "SELL",
                "symbol": resolved_symbol,
                "quantity": quantity,
                "price": price,
                "total_value": total_value,
                "profit_loss": profit_loss,
                "profit_loss_percent": profit_loss_pct,
                "remaining_balance": self.balance,
                "timestamp": trade["timestamp"]
            }
        except Exception as e:
            return {"error": f"Sell failed: {str(e)}"}

    def reset(self):
        self.balance = 100000.0
        self.holdings = {}
        self.trade_history = []
        self._save_state()
        return {"status": "success", "message": "Indian paper portfolio reset."}

# Instantiate the engine for use across the application
india_engine = PaperTradingEngine()


class UsPaperTradingEngine:
    """Local USD paper trading fallback when Alpaca keys are not configured."""
    def __init__(self):
        self._state_file = Path(__file__).resolve().parent.parent / "data" / "us_portfolio.json"
        self.balance = 10000.0
        self.holdings = {}
        self.trade_history = []
        self._load_state()

    def _save_state(self):
        try:
            self._state_file.parent.mkdir(parents=True, exist_ok=True)
            state = {
                "balance": float(self.balance),
                "holdings": self.holdings,
                "trade_history": self.trade_history,
            }
            self._state_file.write_text(json.dumps(state, ensure_ascii=False, indent=2))
        except Exception as e:
            print(f"[UsPaperTradingEngine] Failed to save state: {e}")

    def _load_state(self):
        try:
            if not self._state_file.exists():
                return
            state = json.loads(self._state_file.read_text())
            self.balance = float(state.get("balance", 10000.0))
            self.holdings = state.get("holdings", {}) or {}
            self.trade_history = state.get("trade_history", []) or []
        except Exception as e:
            print(f"[UsPaperTradingEngine] Failed to load state, starting fresh: {e}")
            self.balance = 10000.0
            self.holdings = {}
            self.trade_history = []

    def _get_price(self, symbol: str):
        try:
            import yfinance as yf

            ticker = yf.Ticker(symbol)
            price = None
            try:
                price = ticker.fast_info['lastPrice']
            except Exception:
                pass

            if not price:
                try:
                    hist = ticker.history(period='1d')
                    if not hist.empty:
                        price = float(hist['Close'].iloc[-1])
                except Exception:
                    pass

            return float(price) if price else None
        except Exception:
            return None

    def get_portfolio(self) -> dict:
        holdings_list = []
        total_current_value = 0.0
        total_invested = 0.0

        for symbol, data in self.holdings.items():
            try:
                current_price = self._get_price(symbol) or data['avg_buy_price']
                qty = data['quantity']
                avg_price = data['avg_buy_price']
                current_value = current_price * qty
                invested = data.get('total_invested', avg_price * qty)
                unrealized_pnl = current_value - invested
                unrealized_pct = ((current_price - avg_price) / avg_price) * 100 if avg_price > 0 else 0

                total_current_value += current_value
                total_invested += invested

                holdings_list.append({
                    "symbol": symbol,
                    "quantity": qty,
                    "avg_buy_price": round(avg_price, 2),
                    "current_price": round(current_price, 2),
                    "current_value": round(current_value, 2),
                    "unrealized_pnl": round(unrealized_pnl, 2),
                    "unrealized_pnl_percent": round(unrealized_pct, 2)
                })
            except Exception:
                invested = data.get('total_invested', data['avg_buy_price'] * data['quantity'])
                total_invested += invested
                total_current_value += invested
                holdings_list.append({
                    "symbol": symbol,
                    "quantity": data['quantity'],
                    "avg_buy_price": data['avg_buy_price'],
                    "current_price": data['avg_buy_price'],
                    "current_value": invested,
                    "unrealized_pnl": 0.0,
                    "unrealized_pnl_percent": 0.0,
                })

        total_unrealized = total_current_value - total_invested
        return {
            "currency": "USD",
            "cash": round(self.balance, 2),
            "portfolio_value": round(self.balance + total_current_value, 2),
            "unrealized_pnl": round(total_unrealized, 2),
            "holdings": holdings_list,
            "source": "local-paper"
        }

    def get_trade_history(self):
        return self.trade_history

    def buy(self, symbol: str, quantity: int) -> dict:
        from datetime import datetime

        quantity = int(quantity)
        if quantity <= 0:
            return {"error": "Quantity must be greater than 0"}

        price = self._get_price(symbol)
        if not price or price <= 0:
            return {"error": f"Could not fetch price for {symbol}"}

        total_cost = price * quantity
        if self.balance < total_cost:
            return {"error": f"Insufficient balance. Need ${total_cost:.2f} but have ${self.balance:.2f}"}

        self.balance -= total_cost
        if symbol in self.holdings:
            existing = self.holdings[symbol]
            total_qty = existing['quantity'] + quantity
            total_invested = existing.get('total_invested', existing['avg_buy_price'] * existing['quantity']) + total_cost
            self.holdings[symbol] = {
                'quantity': total_qty,
                'avg_buy_price': total_invested / total_qty,
                'total_invested': total_invested
            }
        else:
            self.holdings[symbol] = {
                'quantity': quantity,
                'avg_buy_price': price,
                'total_invested': total_cost
            }

        trade = {
            "status": "success",
            "action": "BUY",
            "symbol": symbol,
            "quantity": quantity,
            "price": price,
            "total_cost": total_cost,
            "remaining_balance": self.balance,
            "timestamp": datetime.now().isoformat(),
            "source": "local-paper"
        }
        self.trade_history.append(trade)
        self._save_state()
        return trade

    def sell(self, symbol: str, quantity: int) -> dict:
        from datetime import datetime

        quantity = int(quantity)
        if quantity <= 0:
            return {"error": "Quantity must be greater than 0"}
        if symbol not in self.holdings:
            return {"error": f"You don't own any shares of {symbol}"}

        owned_qty = self.holdings[symbol]['quantity']
        if owned_qty < quantity:
            return {"error": f"Insufficient shares. You own {owned_qty} but tried to sell {quantity}"}

        price = self._get_price(symbol)
        if not price or price <= 0:
            return {"error": f"Could not fetch price for {symbol}"}

        avg_buy = self.holdings[symbol]['avg_buy_price']
        total_value = price * quantity
        profit_loss = (price - avg_buy) * quantity
        profit_loss_pct = ((price - avg_buy) / avg_buy) * 100 if avg_buy > 0 else 0

        self.balance += total_value
        if owned_qty == quantity:
            del self.holdings[symbol]
        else:
            self.holdings[symbol]['quantity'] -= quantity
            self.holdings[symbol]['total_invested'] = (
                self.holdings[symbol]['avg_buy_price'] * self.holdings[symbol]['quantity']
            )

        trade = {
            "status": "success",
            "action": "SELL",
            "symbol": symbol,
            "quantity": quantity,
            "price": price,
            "total_value": total_value,
            "profit_loss": profit_loss,
            "profit_loss_percent": profit_loss_pct,
            "remaining_balance": self.balance,
            "timestamp": datetime.now().isoformat(),
            "source": "local-paper"
        }
        self.trade_history.append(trade)
        self._save_state()
        return trade


us_engine = UsPaperTradingEngine()

# --- Generic Trading Functions ---

def place_trade(
    symbol: str,
    action: str = None,
    quantity: int = None,
    side: str = None,
    qty: int = None,
) -> dict:
    """
    Routes a trade order to the appropriate market engine.
    
    Args:
        symbol (str): The stock symbol.
        action (str): "BUY" or "SELL".
        quantity (int): The number of shares.
        
    Returns:
        dict: The result from the corresponding trading function.
    """
    try:
        if action is None and side is not None:
            action = side
        if quantity is None and qty is not None:
            quantity = qty

        if action is None or quantity is None:
            return {"error": "Missing required trade parameters: action/side and quantity/qty"}

        action = str(action).upper()
        symbol = _normalize_trade_symbol(symbol)
        quantity = int(quantity)

        if not symbol:
            return {"error": "Invalid symbol"}

        if quantity <= 0:
            return {"error": "Quantity must be greater than 0"}

        if symbol.endswith(".NS") or symbol.endswith(".BO"):
            # India paper trading
            if action == "BUY":
                return india_engine.buy(symbol, quantity)
            elif action == "SELL":
                return india_engine.sell(symbol, quantity)
            else:
                return {"error": f"Invalid action for Indian market: {action}"}
        else:
            # US paper trading (Alpaca when configured, else local fallback)
            if action == "BUY":
                if _use_local_us_paper_mode():
                    return us_engine.buy(symbol, quantity)
                if not _is_alpaca_configured():
                    return us_engine.buy(symbol, quantity)
                return alpaca_buy(symbol, quantity)
            elif action == "SELL":
                if _use_local_us_paper_mode():
                    return us_engine.sell(symbol, quantity)
                if not _is_alpaca_configured():
                    return us_engine.sell(symbol, quantity)
                return alpaca_sell(symbol, quantity)
            else:
                return {"error": f"Invalid action for US market: {action}"}
    except Exception as e:
        return {"error": str(e)}

def get_full_portfolio() -> dict:
    """
    Retrieves portfolio and trade history from all connected accounts.
    Fetches from both Alpaca (US) and our PaperTradingEngine (India).
    
    Returns:
        dict: A dictionary containing portfolio and history data.
    """
    try:
        alpaca_portfolio = get_alpaca_portfolio()
        alpaca_history = get_alpaca_trade_history()
        
        india_portfolio = india_engine.get_portfolio()
        india_history = india_engine.get_trade_history()
        
        return {
            "alpaca": {
                "portfolio": alpaca_portfolio,
                "history": alpaca_history
            },
            "india": {
                "portfolio": india_portfolio,
                "history": india_history
            }
        }
    except Exception as e:
        return {"error": f"Failed to get full portfolio: {str(e)}"}


# ============================================================================
# TEST BLOCK
# ============================================================================

if __name__ == "__main__":
    import json
    
    print("=== INDIA PAPER TRADING TEST ===\n")
    
    # Test buy
    print("1. Buying 2 shares of TCS.NS:")
    result = india_engine.buy("TCS.NS", 2)
    print(json.dumps(result, indent=2))
    
    print("\n2. Portfolio after buy:")
    portfolio = india_engine.get_portfolio()
    print(json.dumps(portfolio, indent=2))
    
    print("\n3. Trade history:")
    history = india_engine.get_trade_history()
    print(json.dumps(history, indent=2))
    
    # Uncomment to test Alpaca (requires valid API keys)
    # print("\n\n=== US PAPER TRADING TEST ===\n")
    # print("1. Buying 2 shares of AAPL:")
    # result = alpaca_buy("AAPL", 2)
    # print(json.dumps(result, indent=2))
    # 
    # print("\n2. US Portfolio:")
    # us_portfolio = get_alpaca_portfolio()
    # print(json.dumps(us_portfolio, indent=2))
    
    print("\n\n=== FULL PORTFOLIO ===")
    full = get_full_portfolio()
    print(json.dumps(full, indent=2))
