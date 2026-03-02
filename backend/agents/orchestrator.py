"""Orchestrator Agent using Groq"""
from agents.base_agent import run_agent, make_tool_definition
from agents.stock_agent import run_stock_agent
from agents.news_agent import run_news_agent
from agents.portfolio_agent import run_portfolio_agent
from groq import Groq
import os
groq_client = Groq(api_key=os.getenv("GROQ_API_KEY"))

ORCHESTRATOR_SYSTEM_PROMPT = """You are FinSight, an intelligent financial AI assistant.
You MUST ALWAYS use your available tools to answer questions. Never answer from memory.

CRITICAL ROUTING RULES:
1.  For any "buy" or "sell" command → call portfolio_manager IMMEDIATELY.
    - Example: "buy 10 AAPL", "sell 5 TSLA"
2.  For portfolio status ("show portfolio", "my holdings") → call portfolio_manager.
3.  For stock analysis ("analyze TSLA", "price of GOOG") → call stock_analyst.
4.  For news/sentiment ("news on Apple", "market sentiment") → call news_analyst.
5.  For complex questions needing multiple data points (e.g., "should I buy X?"), 
    call the necessary tools sequentially (e.g., stock_analyst then news_analyst).

IMPORTANT:
- NEVER ask for confirmation on trades. The portfolio_manager is designed to execute immediately.
- After getting tool results, present them clearly.
- Do not say "I am routing to..." - just use the tools and present results.
- Be conversational like a personal financial advisor.
- Always clarify this is for educational/paper trading purposes only."""

ORCHESTRATOR_TOOLS = [
    make_tool_definition("run_stock_agent",
        "Delegate a query to the stock analysis agent.",
        {"type": "object", "properties": {
            "user_message": {"type": "string", "description": "The user's original query about stocks"}
        }, "required": ["user_message"]}),
    make_tool_definition("run_news_agent",
        "Delegate a query to the news and sentiment analysis agent.",
        {"type": "object", "properties": {
            "user_message": {"type": "string", "description": "The user's original query about news"}
        }, "required": ["user_message"]}),
    make_tool_definition("run_portfolio_agent",
        "Delegate a query to the portfolio and trading agent.",
        {"type": "object", "properties": {
            "user_message": {"type": "string", "description": "The user's original query about their portfolio or trading"}
        }, "required": ["user_message"]}),
]

ORCHESTRATOR_TOOL_FUNCTIONS = {
    "run_stock_agent": run_stock_agent,
    "run_news_agent": run_news_agent,
    "run_portfolio_agent": run_portfolio_agent,
}

def run_orchestrator(user_message: str):
    """
    Runs the main orchestrator agent.
    This is the entry point for all user queries.
    """
    # The 'run_agent' function from base_agent handles the full loop.
    return run_agent(
        system_prompt=ORCHESTRATOR_SYSTEM_PROMPT,
        user_message=user_message,
        tools=ORCHESTRATOR_TOOLS,
        tool_functions=ORCHESTRATOR_TOOL_FUNCTIONS
    )
