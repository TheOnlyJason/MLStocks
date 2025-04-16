import feedparser
import requests
from bs4 import BeautifulSoup
import time
from concurrent.futures import ThreadPoolExecutor
import socket
from textblob import TextBlob  # For sentiment analysis
import matplotlib.pyplot as plt
from io import BytesIO
import base64
from flask import Flask, render_template, request, jsonify
import yfinance as yf
import matplotlib
from datetime import datetime, timedelta

matplotlib.use('Agg')  # Use non-GUI backend for Flask

app = Flask(__name__, static_folder='static')



def get_recommendation(title, summary):
    """Generate buy/sell/hold recommendation based on sentiment and keywords"""
    try:
        # Combine title and summary for analysis
        analysis_text = f"{title}. {summary}"
        
        # Keyword analysis
        positive_keywords = [
            'buy', 'outperform', 'bullish', 'growth', 'positive outlook', 'strong performance',
            'strong buy', 'recommend buying', 'rise', 'increase', 'upward trend', 'hit new highs',
            'top pick', 'gain', 'record high', 'expected to increase', 'expected to outperform', 
            'expected to rise', 'price target raised', 'stock gains', 'buy now', 'breakout', 'momentum',
            'accelerate growth', 'strong earnings'
        ]
        negative_keywords = [
            'sell', 'underperform', 'bearish', 'weak', 'cut', 'negative outlook', 'falling stock', 
            'decline', 'weak performance', 'hold off', 'price target cut', 'sell-off', 'drop', 'downtrend', 
            'sell recommendation', 'avoid', 'risk', 'losing streak', 'declining stock', 'losing market share', 
            'falling short', 'bear market', 'slump', 'plummet', 'cut earnings forecast', 'expected to fall', 
            'expected to underperform', 'downward revision', 'downward pressure'
        ]
        neutral_keywords = [
            'hold', 'neutral', 'wait and see', 'steady', 'no clear direction', 'uncertain', 'market conditions',
            'flat performance', 'no major changes', 'mixed results', 'expected to stabilize', 'holding steady',
            'limited movement', 'unchanged', 'uncertain outlook', 'neutral stance'
        ]
        
        # Check for strong explicit keywords in the title
        if any(keyword in title.lower() for keyword in negative_keywords):
            return "SELL", "Negative keywords detected in title"
        elif any(keyword in title.lower() for keyword in positive_keywords):
            return "BUY", "Positive keywords detected in title"
        
        # Count keyword matches in title and summary
        positive_count = sum(keyword in analysis_text.lower() for keyword in positive_keywords)
        negative_count = sum(keyword in analysis_text.lower() for keyword in negative_keywords)
        neutral_count = sum(keyword in analysis_text.lower() for keyword in neutral_keywords)
        
        # Generate recommendation based on keyword counts
        if negative_count > positive_count:
            return "SELL", "More negative keywords detected"
        elif positive_count > negative_count:
            return "BUY", "More positive keywords detected"
        elif neutral_count > 0:
            return "HOLD", "Neutral keywords detected"
        else:
            # If no clear signal, fall back to sentiment analysis
            sentiment = TextBlob(analysis_text).sentiment.polarity
            if sentiment > 0.3:
                return "BUY", "Strong positive sentiment"
            elif sentiment < -0.3:
                return "SELL", "Strong negative sentiment"
            else:
                return "HOLD", "Neutral sentiment"
            
    except Exception as e:
        print(f"Recommendation error: {e}")
        return "HOLD", "Unable to analyze"

def process_article(entry):
    """Enhanced article processing with recommendation"""
    try:
        title = entry.title.strip()
        print(f"Processing: {title[:60]}...")
        
        article_text = get_article_text(entry.link)
        full_text = f"{title}. {article_text[:3000]}"
        summary = summarize_with_free_api(full_text)
        
        # Get recommendation
        rec, reason = get_recommendation(title, summary)
        
        return {
            'title': title,
            'summary': summary,
            'url': entry.link,
            'published': entry.get('published', 'N/A'),
            'source': entry.get('source', {}).get('title', 'Unknown Source'),
            'recommendation': rec,
            'reason': reason
        }
    except Exception as e:
        print(f"Error processing article: {e}")
        return None

def summarize_with_free_api(text):
    """Improved summarization with multiple fallback options"""
    # First try SMMRY API
    try:
        # Verify we can resolve the hostname first
        socket.gethostbyname('api.smmry.com')
        
        response = requests.post(
            "https://api.smmry.com",
            params={
                "SM_API_KEY": "1B3C4D5E6F7G8H9I0J",
                "SM_LENGTH": 2
            },
            data={"sm_api_input": text},
            timeout=15
        )
        if response.status_code == 200:
            return response.json().get('sm_api_content', None)
    except (socket.gaierror, requests.exceptions.RequestException) as e:
        print(f"SMMRY API unavailable, using fallback: {e}")
    
    # Fallback 1: Simple text truncation with better sentence detection
    sentences = text.split('. ')
    if len(sentences) > 1:
        return '. '.join(sentences[:2]) + '...'
    
    # Fallback 2: Return first 200 characters
    return text[:200] + "..."

def get_article_text(url):
    """Enhanced article text extraction"""
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept-Language': 'en-US,en;q=0.9'
        }
        response = requests.get(url, headers=headers, timeout=15)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Remove unwanted elements more aggressively
        for element in soup(['script', 'style', 'nav', 'footer', 'iframe', 'aside', 'form', 'button', 'header']):
            element.decompose()
        
        # Find main content using multiple strategies
        article = (soup.find('article') or soup.find(class_=lambda x: x and any(cls in x.lower() for cls in ['content', 'article', 'main']))) or soup
        
        # Get clean paragraphs
        paragraphs = []
        for p in article.find_all('p')[:10]:
            text = p.get_text().strip()
            if len(text.split()) > 5:  # Only keep meaningful paragraphs
                paragraphs.append(text)
        
        return ' '.join(paragraphs)
    except Exception as e:
        print(f"Error extracting article text: {e}")
        return ""

def process_article(entry):
    """Enhanced article processing with recommendation"""
    try:
        title = entry.title.strip()
        print(f"Processing: {title[:60]}...")
        
        article_text = get_article_text(entry.link)
        full_text = f"{title}. {article_text[:3000]}"  # Increased context
        
        summary = summarize_with_free_api(full_text)
        
        # Get recommendation
        rec, reason = get_recommendation(title, summary)
        
        return {
            'title': title,
            'summary': summary,
            'url': entry.link,
            'published': entry.get('published', 'N/A'),
            'recommendation': rec,
            'reason': reason
        }
    except Exception as e:
        print(f"Error processing article: {e}")
        return None

def get_news(stock_symbol, max_articles=20):
    """Improved news fetching with better parallel processing"""
    url = f"https://feeds.finance.yahoo.com/rss/2.0/headline?s={stock_symbol}"
    
    try:
        feed = feedparser.parse(url)
        print(f"Total articles found in feed: {len(feed.entries)}")  # Log the number of articles fetched
        
        if not feed.entries:
            print("No articles found in the RSS feed")
            return []
        
        news_items = []
        
        # Process articles with dynamic thread count based on max_articles
        max_workers = min(5, max(1, max_articles // 3))
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = []
            for entry in feed.entries[:max_articles]:
                futures.append(executor.submit(process_article, entry))
                time.sleep(0.5)  # Reduced stagger time
            
            for future in futures:
                result = future.result()
                if result:
                    news_items.append(result)
        
        return sorted(news_items, key=lambda x: x['published'], reverse=True)
        
    except Exception as e:
        print(f"Error fetching news: {e}")
        return []
    
def generate_pie_chart(articles):
    """Generates a pie chart for buy/sell/hold recommendations."""
    recommendations = {"BUY": 0, "SELL": 0, "HOLD": 0}

    # Count recommendations
    for article in articles:
        rec = article.get('recommendation', 'HOLD')  # Default to 'HOLD' if not present
        if rec in recommendations:
            recommendations[rec] += 1

    # Data for the pie chart
    labels = recommendations.keys()
    sizes = recommendations.values()

    # Plot the pie chart
    fig, ax = plt.subplots(figsize=(7, 7))
    ax.pie(sizes, labels=labels, autopct='%1.1f%%', startangle=90, colors=['#4CAF50', '#F44336', '#FFC107'])
    ax.axis('equal')  # Equal aspect ratio ensures that pie is drawn as a circle.

    # Save pie chart to a BytesIO object
    img = BytesIO()
    plt.savefig(img, format='png')
    img.seek(0)

    # Encode image to base64
    img_base64 = base64.b64encode(img.getvalue()).decode('utf-8')
    
    return img_base64

# Add this new function to fetch stock data
def get_stock_data(stock_symbol):
    """Fetch live stock data using yfinance"""
    try:
        stock = yf.Ticker(stock_symbol)
        data = stock.history(period='1d')
        
        if data.empty:
            return None
            
        # Get additional info
        info = stock.info
        return {
            'symbol': stock_symbol,
            'current_price': round(data['Close'].iloc[-1], 2),
            'previous_close': round(info.get('regularMarketPreviousClose', data['Close'].iloc[-2] if len(data) > 1 else data['Close'].iloc[-1]), 2),
            'change': round(data['Close'].iloc[-1] - info.get('regularMarketPreviousClose', data['Close'].iloc[-2] if len(data) > 1 else data['Close'].iloc[-1]), 2),
            'change_percent': round((data['Close'].iloc[-1] / info.get('regularMarketPreviousClose', data['Close'].iloc[-2] if len(data) > 1 else data['Close'].iloc[-1]) - 1) * 100, 2),
            'name': info.get('shortName', stock_symbol),
            'market_cap': f"{info.get('marketCap', 0)/1e9:.2f}B" if info.get('marketCap') else 'N/A'
        }
    except Exception as e:
        print(f"Error fetching stock data: {e}")
        return None
    
def get_historical_data(stock_symbol, period='1mo'):
    """Fetch historical stock data for charting with different time periods"""
    try:
        stock = yf.Ticker(stock_symbol)
        hist = stock.history(period=period)
        
        if hist.empty:
            return None
            
        return {
            'dates': [date.strftime('%Y-%m-%d') for date in hist.index],
            'prices': [round(price, 2) for price in hist['Close'].tolist()],
            'volumes': [int(vol) for vol in hist['Volume'].tolist()],
            'period': period
        }
    except Exception as e:
        print(f"Error fetching historical data: {e}")
        return None

@app.route('/get_chart_data')
def get_chart_data():
    stock_symbol = request.args.get('symbol', 'TSLA')
    period = request.args.get('period', '1mo')
    data = get_historical_data(stock_symbol, period)
    return jsonify(data)

# Update your index route
@app.route('/', methods=['GET', 'POST'])
def index():
    stock_symbol = request.args.get('stock_symbol', 'TSLA').upper()

    articles = get_news(stock_symbol, max_articles=20)
    stock_data = get_stock_data(stock_symbol)
    historical_data = get_historical_data(stock_symbol)
    
    if not articles:
        return "No articles were fetched. Check your internet connection or try again later."

    pie_chart = generate_pie_chart(articles)
    
    return render_template('index.html', 
                        articles=articles, 
                        pie_chart=pie_chart,
                        stock_data=stock_data,
                        stock_symbol=stock_symbol,
                        historical_data=historical_data)

if __name__ == "__main__":
    app.run(debug=True)
    



