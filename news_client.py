# news_client.py - INDIA-FOCUSED LIVE TICKER (Banking, Govt Schemes, Women/Child/Senior, Market)
import os
import requests
from dotenv import load_dotenv

load_dotenv()
NEWS_API_KEY = os.getenv("NEWS_API_KEY")

if not NEWS_API_KEY:
    print("Warning: NEWS_API_KEY not found. Using demo headlines.")

# Main search function (same as before)
def fetch_news(query, lang="en", page_size=5):
    if not NEWS_API_KEY:
        return [{"title": f"Sample news about {query}", "description": "Demo description", "url": "#", "source": "Demo", "published_at": "2025-12-22"} for _ in range(3)]
    
    url = "https://newsapi.org/v2/everything"
    params = {
        "q": query,
        "language": lang,
        "pageSize": page_size,
        "sortBy": "publishedAt",
        "apiKey": NEWS_API_KEY
    }
    try:
        r = requests.get(url, params=params, timeout=20).json()
        if r.get("status") == "ok":
            return [
                {
                    "title": a["title"],
                    "description": a["description"],
                    "content": a["content"],
                    "url": a["url"],
                    "source": a["source"]["name"],
                    "published_at": a["publishedAt"][:10]
                } for a in r["articles"]
            ]
    except:
        pass
    return []

# NEW: Focused Live Ticker for Banking, Govt Schemes, Women/Child/Senior Citizen, Market
def fetch_ticker_headlines():
    if not NEWS_API_KEY:
        return "New Bank Interest Rates | Govt Scheme for Women | Senior Citizen Benefits | Child Education Scheme | Market Analysis | RBI Update | Stock Market News"
    
    # Multiple relevant keywords for India-focused useful news
    keywords = "(RBI OR bank OR interest rate OR government scheme OR women scheme OR child benefit OR senior citizen OR fixed deposit OR savings account OR market analysis OR Sensex OR Nifty OR stock market OR financial policy) India"
    
    url = f"https://newsapi.org/v2/everything?q={keywords}&language=en&pageSize=12&sortBy=publishedAt&apiKey={NEWS_API_KEY}"
    
    try:
        r = requests.get(url, timeout=20).json()
        if r.get("status") == "ok" and r["articles"]:
            titles = [a["title"] for a in r["articles"][:10]]
            return "  |  ".join(titles)
    except Exception as e:
        pass
    
    # Fallback useful suggestions
    return "Latest RBI Policy | New Bank FD Rates | Women Empowerment Scheme | Senior Citizen Benefits | Child Education Scheme | Market Outlook | Stock Tips | Govt Financial Updates"

def fetch_world_news(count=20):
    if not NEWS_API_KEY:
        return [{"title": f"World News {i+1}", "url": "#", "source": "Global", "published_at": "2025-12-22"} for i in range(count)]
    
    url = f"https://newsapi.org/v2/top-headlines?country=us&pageSize={count}&apiKey={NEWS_API_KEY}"
    try:
        r = requests.get(url).json()
        if r.get("status") == "ok":
            return [
                {"title": a["title"], "url": a["url"], "source": a["source"]["name"], "published_at": a["publishedAt"][:10]}
                for a in r["articles"]
            ]
    except:
        pass
    return [{"title": f"International Update {i+1}", "url": "#", "source": "World", "published_at": "2025-12-22"} for i in range(count)]