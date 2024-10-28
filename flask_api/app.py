from flask import Flask, jsonify, request
from flask_cors import CORS
import yfinance as yf
import time
import concurrent.futures

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

# List of NSE stocks and broad market indexes (reduced number for faster response)
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

# List of index tickers (reduced list)
indexes = [
    '^NSEI', '^NSMIDCAP', 'NIFTY100.NS', 'NIFTY200.NS', 'NIFTY500.NS', 
    'NIFTYMID50.NS', 'NIFTYMID100.NS', 'NIFTYSMALL100.NS', '^INDIAVIX',
    'NIFTYMID150.NS', 'NIFTYSMALL50.NS', 'NIFTYSMALL250.NS', 'NIFTYMIDSML400.NS'
]

# Function to fetch financial news for stocks and indexes concurrently
def fetch_news():
    news_list = []

    # Helper function to fetch news for a single ticker
    def fetch_single_news(ticker_name):
        ticker = yf.Ticker(ticker_name)
        try:
            return ticker.news[:3] if ticker.news else []
        except Exception as e:
            print(f"Error fetching news for {ticker_name}: {e}")
            return []

    # Fetch news concurrently for indexes and stocks
    with concurrent.futures.ThreadPoolExecutor() as executor:
        # Submit tasks for indexes
        index_futures = {executor.submit(fetch_single_news, index): index for index in indexes}
        # Submit tasks for stocks
        stock_futures = {executor.submit(fetch_single_news, stock): stock for stock in stocks}
        
        # Collect results for indexes
        for future in concurrent.futures.as_completed(index_futures):
            index = index_futures[future]
            for article in future.result():
                news_list.append({
                    'title': article['title'],
                    'link': article['link'],
                    'stock': index
                })
        
        # Collect results for stocks
        for future in concurrent.futures.as_completed(stock_futures):
            stock = stock_futures[future]
            for article in future.result():
                news_list.append({
                    'title': article['title'],
                    'link': article['link'],
                    'stock': stock
                })

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
