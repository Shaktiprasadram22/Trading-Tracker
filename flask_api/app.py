from flask import Flask, jsonify, request
from flask_cors import CORS
import yfinance as yf
import time

app = Flask(__name__)
CORS(app)

saved_articles = []

# Cache for news articles
news_cache = {
    'data': None,
    'last_update': 0
}

# Time to cache the news (in seconds), e.g., 15 minutes = 900 seconds
CACHE_DURATION = 900

# List of NSE stocks and broad market indexes
stocks = [
    'NTPC.NS', 'TECHM.NS', 'POLYCAB.NS', 'PVRINOX.NS', 'TATAPOWER.NS', 
    'LT.NS', 'HINDALCO.NS', 'HAVELLS.NS', 'TITAN.NS', 'DABUR.NS',
    'BANKBARODA.NS', 'CROMPTON.NS', 'TATACHEM.NS', 'IGL.NS', 
    'SBICARD.NS', 'VEDL.NS', 'DRREDDY.NS', 'CUMMINSIND.NS', 'OFSS.NS',
    'SUNTV.NS', 'IPCALAB.NS', 'ACC.NS', 'AUBANK.NS', 'ABB.NS', 
    'METROPOLIS.NS', 'ABCAPITAL.NS', 'AUROPHARMA.NS', 'ONGC.NS', 
    'GODREJPROP.NS', 'DIVISLAB.NS', 'HDFCLIFE.NS', 'HCLTECH.NS',
    'EICHERMOT.NS', 'SRF.NS', 'ABBOTINDIA.NS', 'RECLTD.NS', 'RELIANCE.NS', 
    'PETRONET.NS', 'WIPRO.NS', 'HDFCBANK.NS', 'TITAN.NS', 'TATASTEEL', 'BAJAJFINANCE',
]

# List of index tickers
indexes = [
    '^NSEI', '^NSMIDCAP', 'NIFTY100.NS', 'NIFTY200.NS', 'NIFTY500.NS', 
    'NIFTYMID50.NS', 'NIFTYMID100.NS', 'NIFTYSMALL100.NS', '^INDIAVIX',
    'NIFTYMID150.NS', 'NIFTYSMALL50.NS', 'NIFTYSMALL250.NS', 'NIFTYMIDSML400.NS'
]

# Function to fetch financial news for stocks and indexes
def fetch_news():
    news_list = []

    # Fetch news for indexes
    for index in indexes:
        ticker = yf.Ticker(index)
        try:
            index_news = ticker.news
            if index_news:
                for article in index_news[:3]:
                    news_list.append({
                        'title': article['title'],
                        'link': article['link'],
                        'stock': index
                    })
        except Exception as e:
            print(f"Error fetching news for {index}: {e}")

    # Fetch individual stock news
    for stock in stocks:
        ticker = yf.Ticker(stock)
        try:
            stock_news = ticker.news
            if stock_news:
                for article in stock_news[:3]:
                    news_list.append({
                        'title': article['title'],
                        'link': article['link'],
                        'stock': stock
                    })
        except Exception as e:
            print(f"Error fetching news for {stock}: {e}")

    return news_list

# Function to retrieve cached news or fetch fresh news if cache is expired
def get_cached_news():
    current_time = time.time()
    # Check if the cache is still valid (within the cache duration)
    if news_cache['data'] is None or (current_time - news_cache['last_update'] > CACHE_DURATION):
        # Fetch fresh news and update the cache
        print("Fetching fresh news data...")
        news_cache['data'] = fetch_news()
        news_cache['last_update'] = current_time
    else:
        print("Returning cached news data...")
    
    return news_cache['data']

# Route for /news
@app.route('/news', methods=['GET'])
def get_news():
    articles = get_cached_news()
    return jsonify(articles)

# Route for saving an article
@app.route('/save_article', methods=['POST'])
def save_article():
    article = request.json
    saved_articles.append(article)
    return jsonify({'message': 'Article saved successfully!'})

# Route for fetching saved articles
@app.route('/saved_articles', methods=['GET'])
def get_saved_articles():
    return jsonify(saved_articles)

# Route for deleting a saved article
@app.route('/delete_article', methods=['POST'])
def delete_article():
    article = request.json
    global saved_articles
    saved_articles = [a for a in saved_articles if a['title'] != article['title']]
    return jsonify({'message': 'Article deleted successfully!'})

if __name__ == '__main__':
    app.run(debug=True, port=5002)  # Run on port 5002
