import feedparser
import requests
from openai import OpenAI
import time

# Initialize OpenAI client (only if API key is provided)
OPENAI_API_KEY = ''
client = OpenAI(api_key=OPENAI_API_KEY) if OPENAI_API_KEY else None

def summarize_with_openai(text, model="gpt-3.5-turbo"):
    """Summarize using OpenAI API"""
    if not client:
        return None
        
    try:
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": "Summarize in 1-2 sentences for a financial audience."},
                {"role": "user", "content": text}
            ],
            max_tokens=100,
            temperature=0.3
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        print(f"OpenAI error: {e}")
        return None

def summarize_with_free_api(text):
    """Fallback to free summarization API"""
    try:
        response = requests.post(
            "https://api.smmry.com/",
            data={
                "sm_api_input": text,
                "SM_API_KEY": "1B3C4D5E6F7G8H9I0J"  # Free public key (may have limits)
            },
            timeout=10
        )
        return response.json().get('sm_api_content', 'Summary unavailable')
    except:
        return text[:150] + "..."  # Simple truncation fallback
        
def get_news(stock_symbol, max_articles=5):
    """Get news from Yahoo Finance RSS"""
    url = f"https://feeds.finance.yahoo.com/rss/2.0/headline?s={stock_symbol}"
    feed = feedparser.parse(url)
    
    news_items = []
    for entry in feed.entries[:max_articles]:
        try:
            title = entry.title.strip()
            if not title:
                continue
                
            # Try OpenAI first if available
            summary = (summarize_with_openai(title) if client 
                      else summarize_with_free_api(title))
            
            news_items.append({
                'title': title,
                'summary': summary if summary else title[:150] + "...",
                'url': entry.link,
                'published': entry.get('published', 'N/A')
            })
            
            time.sleep(1)  # Rate limiting
            
        except Exception as e:
            print(f"Error processing article: {e}")
            continue
            
    return news_items

if __name__ == "__main__":
    try:
        print("Fetching Apple news...")
        news_data = get_news("GOOG")
        
        print("\nLatest News Summaries:")
        for idx, article in enumerate(news_data, 1):
            print(f"\n{idx}. {article['title']}")
            print(f"   Summary: {article['summary']}")
            print(f"   URL: {article['url']}")
            print("-" * 80)
            
    except Exception as e:
        print(f"Error: {e}")
