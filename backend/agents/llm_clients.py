"""
Centralized LLM clients for FinSight.
Different APIs used for different features to maximize free tier limits.
- GitHub Models: Orchestrator + Stock Agent (150k tokens/day)
- Groq: Portfolio Agent (100k tokens/day)  
- Gemini: News Sentiment (1500 requests/day)
"""
import os
from dotenv import load_dotenv
load_dotenv()

# ── GitHub Models Client (Orchestrator + Stock Agent) ──
from openai import OpenAI as OpenAIClient

github_client = OpenAIClient(
    base_url="https://models.inference.ai.azure.com",
    api_key=os.getenv("GITHUB_TOKEN"),
    timeout=25.0
)
GITHUB_MODEL = "gpt-4o-mini"

# ── Groq Client (Portfolio Agent) ──
from groq import Groq
groq_client = Groq(api_key=os.getenv("GROQ_API_KEY"), timeout=25.0)
GROQ_MODEL = "llama-3.3-70b-versatile"

# ── Gemini Client (News Sentiment) ──
import google.generativeai as genai
gemini_client = genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
GEMINI_MODEL = "gemini-1.5-flash"

def call_github(messages: list, max_tokens: int = 4000) -> str:
    """Call GitHub Models - use for orchestrator and stock agent"""
    try:
        response = github_client.chat.completions.create(
            model=GITHUB_MODEL,
            messages=messages,
            temperature=0.1,
            max_tokens=max_tokens
        )
        return response.choices[0].message.content
    except Exception as e:
        # Fallback to Groq if GitHub fails
        try:
            response = groq_client.chat.completions.create(
                model=GROQ_MODEL,
                messages=messages,
                temperature=0.1,
                max_tokens=max_tokens
            )
            return response.choices[0].message.content
        except Exception as e2:
            raise Exception(f"Both GitHub and Groq failed: {str(e)} | {str(e2)}")

def call_groq(messages: list, max_tokens: int = 4000, tools=None) -> any:
    """Call Groq - use for portfolio agent (tool calling)"""
    try:
        params = {
            "model": GROQ_MODEL,
            "messages": messages,
            "temperature": 0.1,
            "max_tokens": max_tokens
        }
        if tools:
            params["tools"] = tools
            params["tool_choice"] = "auto"
        return groq_client.chat.completions.create(**params)
    except Exception as e:
        # Fallback to GitHub if Groq is rate limited
        params.pop("tools", None)
        params.pop("tool_choice", None)
        response = github_client.chat.completions.create(
            model=GITHUB_MODEL,
            **{k: v for k, v in params.items() if k != "model"}
        )
        # Wrap in same format
        return response

def call_gemini(prompt: str) -> str:
    """Call Gemini - use for news sentiment analysis"""
    try:
        model = genai.GenerativeModel(GEMINI_MODEL)
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        # Fallback to Groq if Gemini quota exceeded
        try:
            response = groq_client.chat.completions.create(
                model=GROQ_MODEL,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3,
                max_tokens=2000
            )
            return response.choices[0].message.content
        except Exception as e2:
            raise Exception(f"Both Gemini and Groq failed: {str(e)} | {str(e2)}")
