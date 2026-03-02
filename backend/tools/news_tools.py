# finsight/backend/tools/news_tools.py

"""
This module provides tools for fetching financial news using NewsAPI and analyzing
sentiment using Google's Gemini AI. It includes functions to get company-specific news,
analyze sentiment across multiple articles, calculate overall sentiment metrics,
and fetch broad market news by category.

Requirements:
- pip install google-generativeai requests python-dotenv

API Keys required in .env:
- NEWS_API_KEY: Your NewsAPI key (free tier: 100 requests/day)
- GEMINI_API_KEY: Your Google Gemini API key
"""

import os
import json
import requests # type: ignore
from dotenv import load_dotenv # type: ignore
from agents.llm_clients import call_gemini

# Load environment variables
load_dotenv()

# Configure NewsAPI
NEWS_API_KEY = os.getenv("NEWS_API_KEY")





def get_news(company: str, num_articles: int = 8) -> dict:
    """
    Fetches financial news articles for a given company using NewsAPI.

    Args:
        company (str): The company name to search for.
        num_articles (int): Number of articles to fetch (default: 8).

    Returns:
        dict: A dictionary containing the company name, total results, and list of articles.
    """
    try:
        if not NEWS_API_KEY:
            return {"error": "NEWS_API_KEY not found in environment variables"}

        # Build query to focus on financial news
        query = f"{company} AND (stock OR shares OR market OR earnings OR financial)"
        
        # NewsAPI endpoint and parameters
        url = "https://newsapi.org/v2/everything"
        params = {
            "q": query,
            "language": "en",
            "sortBy": "publishedAt",
            "pageSize": num_articles,
            "apiKey": NEWS_API_KEY
        }

        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        
        data = response.json()
        
        if data.get("status") != "ok":
            return {"error": f"NewsAPI error: {data.get('message', 'Unknown error')}"}
        
        if data.get("totalResults", 0) == 0:
            return {"error": f"No articles found for {company}"}

        # Clean and format articles
        articles = []
        for article in data.get("articles", []):
            articles.append({
                "title": article.get("title", "No title"),
                "description": article.get("description", "No description"),
                "source": article.get("source", {}).get("name", "Unknown"),
                "published_at": article.get("publishedAt", ""),
                "url": article.get("url", "")
            })

        return {
            "company": company,
            "total_results": len(articles),
            "articles": articles
        }
    
    except requests.exceptions.RequestException as e:
        return {"error": f"Failed to fetch news for {company}: {str(e)}"}
    except Exception as e:
        return {"error": f"Unexpected error in get_news: {str(e)}"}


def analyze_sentiment(articles: list) -> list:
    """
    Analyzes the sentiment of news articles using Google Gemini AI.
    
    Args:
        articles (list): List of article dictionaries with 'title' and 'description' keys.
    
    Returns:
        list: The same list of articles with sentiment analysis added to each.
    """
    try:
        gemini_api_key = os.getenv("GEMINI_API_KEY")
        if not gemini_api_key:
            # Return articles without sentiment if no API key
            for article in articles:
                article["sentiment"] = "Unknown"
                article["reason"] = "GEMINI_API_KEY not configured"
                article["score"] = 0.0
            return articles

        if not articles:
            return articles

        # Prepare headlines for batch analysis
        headlines_text = "\n".join([f"{i+1}. {article['title']}" for i, article in enumerate(articles)])
        
        prompt = f"""You are a financial news sentiment analyzer. 
For each headline below, respond with ONLY a JSON array where each item has:
'sentiment': one of 'Positive', 'Negative', 'Neutral'
'reason': one short sentence explaining why (max 10 words)
'score': a number from -1.0 (very negative) to 1.0 (very positive)

Headlines:
{headlines_text}

Respond with ONLY the JSON array, no other text."""

        # Call Gemini API
        response_text = call_gemini(prompt)
        
        # Remove markdown code blocks if present
        if response_text.startswith("```json"):
            response_text = response_text[7:]
        if response_text.startswith("```"):
            response_text = response_text[3:]
        if response_text.endswith("```"):
            response_text = response_text[:-3]
        
        response_text = response_text.strip()
        
        # Parse JSON
        sentiment_results = json.loads(response_text)
        
        # Merge sentiment back into articles
        for i, article in enumerate(articles):
            if i < len(sentiment_results):
                article["sentiment"] = sentiment_results[i].get("sentiment", "Neutral")
                article["reason"] = sentiment_results[i].get("reason", "No reason provided")
                article["score"] = float(sentiment_results[i].get("score", 0.0))
            else:
                article["sentiment"] = "Neutral"
                article["reason"] = "Analysis incomplete"
                article["score"] = 0.0
        
        return articles
    
    except json.JSONDecodeError as e:
        # Fallback: mark all as neutral if parsing fails
        for article in articles:
            article["sentiment"] = "Neutral"
            article["reason"] = "Sentiment analysis parsing failed"
            article["score"] = 0.0
        return articles
    
    except Exception as e:
        # Fallback: mark all as unknown on error
        for article in articles:
            article["sentiment"] = "Unknown"
            article["reason"] = f"Error: {str(e)[:30]}"
            article["score"] = 0.0
        return articles


def get_overall_sentiment(company: str) -> dict:
    """
    Fetches news for a company, analyzes sentiment, and provides an overall sentiment report.
    
    Args:
        company (str): The company name to analyze.
    
    Returns:
        dict: A comprehensive sentiment report with statistics and analyzed articles.
    """
    try:
        # Fetch news
        news_result = get_news(company, num_articles=8)
        
        if "error" in news_result:
            return news_result
        
        articles = news_result.get("articles", [])
        
        # Analyze sentiment
        articles_with_sentiment = analyze_sentiment(articles)
        
        # Calculate statistics
        sentiment_breakdown = {"Positive": 0, "Negative": 0, "Neutral": 0, "Unknown": 0}
        total_score = 0.0
        
        for article in articles_with_sentiment:
            sentiment = article.get("sentiment", "Unknown")
            sentiment_breakdown[sentiment] = sentiment_breakdown.get(sentiment, 0) + 1
            total_score += article.get("score", 0.0)
        
        average_score = total_score / len(articles_with_sentiment) if articles_with_sentiment else 0.0
        
        # Determine overall sentiment
        if average_score > 0.2:
            overall_sentiment = "Positive"
        elif average_score < -0.2:
            overall_sentiment = "Negative"
        else:
            overall_sentiment = "Neutral"
        
        # Generate summary using an LLM
        summary = f"{company} has {overall_sentiment.lower()} news coverage with {sentiment_breakdown['Positive']} positive, {sentiment_breakdown['Negative']} negative, and {sentiment_breakdown['Neutral']} neutral articles."
        
        gemini_api_key = os.getenv("GEMINI_API_KEY")
        if gemini_api_key:
            try:
                # Ask Gemini to generate a better summary
                titles = [article['title'] for article in articles_with_sentiment[:5]]
                summary_prompt = f"""Based on these news headlines about {company}, write ONE concise sentence summarizing the overall sentiment and key themes:

{chr(10).join(titles)}

Write only the summary sentence, nothing else."""
                
                summary = call_gemini(summary_prompt).strip()
            except:
                pass  # Use default summary if LLM fails
        
        return {
            "company": company,
            "overall_sentiment": overall_sentiment,
            "average_score": round(average_score, 2),
            "sentiment_breakdown": sentiment_breakdown,
            "summary": summary,
            "articles": articles_with_sentiment
        }
    
    except Exception as e:
        return {"error": f"Failed to analyze overall sentiment for {company}: {str(e)}"}


def get_market_news(category: str = "general") -> dict:
    """
    Fetches broad market news by category (not company-specific).
    
    Args:
        category (str): The market category - "general", "india", "us", or "crypto".
    
    Returns:
        dict: A dictionary containing the category and list of articles.
    """
    try:
        if not NEWS_API_KEY:
            return {"error": "NEWS_API_KEY not found in environment variables"}

        # Build query based on category
        query_map = {
            "india": "Indian stock market NSE BSE Sensex Nifty",
            "us": "US stock market NYSE NASDAQ Fed",
            "crypto": "cryptocurrency Bitcoin Ethereum crypto market",
            "general": "global stock market finance economy"
        }
        
        query = query_map.get(category.lower(), query_map["general"])
        
        # NewsAPI endpoint and parameters
        url = "https://newsapi.org/v2/everything"
        params = {
            "q": query,
            "language": "en",
            "sortBy": "publishedAt",
            "pageSize": 8,
            "apiKey": NEWS_API_KEY
        }

        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        
        data = response.json()
        
        if data.get("status") != "ok":
            return {"error": f"NewsAPI error: {data.get('message', 'Unknown error')}"}
        
        # Clean and format articles
        articles = []
        for article in data.get("articles", []):
            articles.append({
                "title": article.get("title", "No title"),
                "description": article.get("description", "No description"),
                "source": article.get("source", {}).get("name", "Unknown"),
                "published_at": article.get("publishedAt", ""),
                "url": article.get("url", "")
            })

        return {
            "category": category,
            "articles": articles
        }
    
    except requests.exceptions.RequestException as e:
        return {"error": f"Failed to fetch market news: {str(e)}"}
    except Exception as e:
        return {"error": f"Unexpected error in get_market_news: {str(e)}"}


# Test block
if __name__ == "__main__":
    print("--- Testing get_news ---")
    news = get_news("Apple", num_articles=3)
    print(json.dumps(news, indent=2))
    
    print("\n--- Testing get_overall_sentiment ---")
    sentiment_report = get_overall_sentiment("Tesla")
    print(json.dumps(sentiment_report, indent=2))
    
    print("\n--- Testing get_market_news ---")
    market = get_market_news("india")
    print(json.dumps(market, indent=2))
