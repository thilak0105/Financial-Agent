# finsight/backend/main.py
"""
Main FastAPI application for the FinSight AI Agent.
This file sets up all API endpoints, including:
- Real-time chat with the AI agent via Server-Sent Events (SSE).
- Endpoints for stock data, news, portfolio management, and trading.
"""
import os
import json
import asyncio
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sse_starlette.sse import EventSourceResponse
from pydantic import BaseModel

# --- Agent & Tool Imports ---
load_dotenv()
from agents.orchestrator import run_orchestrator
from tools.stock_tools import get_stock_price, get_stock_info, get_technical_indicators, get_stock_history
from tools.news_tools import get_overall_sentiment, get_market_news
from tools.trading_tools import (
    india_engine, 
    get_alpaca_portfolio, 
    place_trade, 
    get_full_portfolio
)

# --- FastAPI App Initialization ---
app = FastAPI(
    title="FinSight API",
    description="API for the FinSight AI Finance Agent",
    version="1.0.0"
)

# CORS configuration
origins = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://localhost:5174",
    "http://127.0.0.1:5174",
]

# Add production frontend URL from environment variable
frontend_url = os.getenv("FRONTEND_URL")
if frontend_url:
    origins.append(frontend_url)

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Health Check Endpoint ---
@app.get("/")
async def root():
    return {"status": "ok", "message": "FinSight API is running"}

@app.get("/api/health")
async def health():
    return {"status": "healthy", "version": "1.0.0"}

# --- Pydantic Models ---
class ChatRequest(BaseModel):
    message: str
    session_id: str = "default"

class TradeRequest(BaseModel):
    symbol: str
    action: str  # "BUY" or "SELL"
    quantity: int

# --- Agent Streaming Logic ---
conversation_store = {}  # session_id -> list of messages

async def run_agent_streaming(user_message: str, session_id: str):
    """Run orchestrator with conversation memory, stream response"""
    if session_id not in conversation_store:
        conversation_store[session_id] = []
    
    history = conversation_store[session_id]
    history.append({"role": "user", "content": user_message})
    
    recent_history = history[-6:] if len(history) > 6 else history
    
    if len(recent_history) > 1:
        context = "Previous conversation:\n"
        for msg in recent_history[:-1]:
            role = "User" if msg["role"] == "user" else "Assistant"
            context += f"{role}: {msg['content'][:200]}\n"
        context += f"\nCurrent question: {user_message}"
        message_with_context = context
    else:
        message_with_context = user_message
    
    loop = asyncio.get_event_loop()
    response = await loop.run_in_executor(
        None,
        run_orchestrator,
        message_with_context
    )
    
    history.append({"role": "assistant", "content": response})
    
    if len(history) > 20:
        conversation_store[session_id] = history[-20:]
    
    words = response.split(" ")
    for i, word in enumerate(words):
        chunk = word + (" " if i < len(words) - 1 else "")
        yield chunk
        await asyncio.sleep(0.02)




# --- API Endpoints ---
@app.get("/api/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "ok", "message": "FinSight API is running"}

@app.post("/api/chat")
async def chat(request: ChatRequest):
    async def generate():
        try:
            async for chunk in run_agent_streaming(
                request.message, 
                request.session_id
            ):
                yield {
                    "data": json.dumps({
                        "type": "text", 
                        "content": chunk
                    })
                }
            yield {"data": json.dumps({"type": "done"})}
        except Exception as e:
            yield {
                "data": json.dumps({
                    "type": "error", 
                    "content": str(e)
                })
            }
    return EventSourceResponse(generate())

@app.get("/api/stocks/{symbol}")
async def get_full_stock_details(symbol: str):
    """Get combined price and technical data for a stock."""
    try:
        price_data = get_stock_price(symbol)
        technical_data = get_technical_indicators(symbol)
        if "error" in price_data or "error" in technical_data:
            raise HTTPException(status_code=404, detail="Failed to fetch stock data.")
        return {
            "price_data": price_data,
            "technical_data": technical_data
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/stocks/{symbol}/info")
async def get_company_info(symbol: str):
    """Get company information for a stock."""
    try:
        info = get_stock_info(symbol)
        if "error" in info:
            raise HTTPException(status_code=404, detail=info["error"])
        return info
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/stocks/{symbol}/history")
async def get_stock_history_data(symbol: str, period: str = "3mo"):
    """Get historical stock data for charting."""
    try:
        history = get_stock_history(symbol, period)
        if "error" in history:
            raise HTTPException(status_code=404, detail=history["error"])
        return history
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/news/{company}")
async def get_company_news(company: str):
    """Get news and sentiment for a company."""
    try:
        sentiment = get_overall_sentiment(company)
        if "error" in sentiment:
            raise HTTPException(status_code=404, detail=sentiment["error"])
        return sentiment
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/market-news")
async def get_general_market_news(category: str = "general"):
    """Get broad market news by category."""
    try:
        news = get_market_news(category)
        if "error" in news:
            raise HTTPException(status_code=404, detail=news["error"])
        return news
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/portfolio")
async def get_portfolio():
    """Get portfolio data for both Indian and US markets."""
    try:
        # Get India portfolio from our PaperTradingEngine
        india_data = india_engine.get_portfolio()
        
        # Get US portfolio from Alpaca
        us_data = get_alpaca_portfolio()
        
        return {
            "india": india_data,
            "us": us_data
        }
    except Exception as e:
        # Log the exception for debugging
        print(f"Error in /api/portfolio: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/trade")
async def execute_trade(request: TradeRequest):
    """Execute a paper trade."""
    try:
        result = place_trade(
            symbol=request.symbol,
            action=request.action,
            quantity=request.quantity
        )
        if not isinstance(result, dict):
            raise HTTPException(status_code=500, detail="Trade engine returned invalid response")
        if "error" in result:
            raise HTTPException(status_code=400, detail=result["error"])
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/portfolio/reset")
async def reset_user_portfolio():
    """Reset the Indian paper trading portfolio."""
    try:
        return india_engine.reset()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/debug/portfolio")
async def debug_portfolio():
    india = india_engine.get_portfolio()
    return {
        "india_balance": india.get("balance"),
        "india_raw": india,
    }
