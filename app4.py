from flask import Flask, jsonify, render_template, request
from flask_caching import Cache
import yfinance as yf
import requests
from concurrent.futures import ThreadPoolExecutor
import logging
import time

app = Flask(__name__)

# Configure cache for quick data retrieval (timeout 5 mins)
cache = Cache(app, config={'CACHE_TYPE': 'simple', 'CACHE_DEFAULT_TIMEOUT': 300})

# Set up logging
logging.basicConfig(level=logging.INFO)

# Alpha Vantage API Key
ALPHA_VANTAGE_API_KEY = 'GHOZ1MVIGNYP6S27'

# List of all supported stocks
all_stocks = [
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

# Retry wrapper
def retry_fetch(func, ticker, retries=3, delay=2):
    for i in range(retries):
        result = func(ticker)
        if result is not None:
            return result
        logging.warning(f"Retry {i+1} for {ticker} after delay.")
        time.sleep(delay)
    logging.error(f"Failed to fetch data for {ticker} after {retries} retries.")
    return None

# Function to fetch historical data and calculate support and resistance, and current price
def fetch_stock_data(ticker):
    try:
        stock = yf.Ticker(ticker)
        
        # Fetch last 5 days of data to ensure we have previous day's data
        data = stock.history(period="5d", interval="1m")
        
        if not data.empty:
            # Filter data to get the last two days
            recent_data = data[-2*390:]  # Each trading day has around 390 minutes of data

            # Today's data
            today_data = recent_data[recent_data.index.date == recent_data.index[-1].date()]
            current_price = today_data['Close'].iloc[-1]
            today_high = today_data['High'].max()
            today_low = today_data['Low'].min()
            logging.info(f"Today’s data for {ticker}: Current={current_price}, High={today_high}, Low={today_low}")

            # Previous day's data for support/resistance calculations
            prev_day_data = recent_data[recent_data.index.date == recent_data.index[-2*390].date()]
            if not prev_day_data.empty:
                high = prev_day_data['High'].max()
                low = prev_day_data['Low'].min()
                close = prev_day_data['Close'].iloc[-1]

                # Calculate Pivot Point, Support, and Resistance
                pivot = (high + low + close) / 3
                support = (2 * pivot) - high
                resistance = (2 * pivot) - low

                return {
                    'ticker': ticker,
                    'current_price': current_price,
                    'today_high': today_high,
                    'today_low': today_low,
                    'support': support,
                    'resistance': resistance
                }
            else:
                logging.warning(f"Previous day data is insufficient for support/resistance for {ticker}")
                return None
        else:
            logging.warning(f"No valid data returned from yfinance for {ticker}")
            return None
    except Exception as e:
        logging.error(f"Error fetching data for {ticker}: {e}")
        return None


# Cache the specific stock data request for better performance
@app.route('/get_selected_stock_data', methods=['GET'])
def get_selected_stock_data():
    tickers = request.args.get('tickers')
    if not tickers:
        return jsonify({"error": "No tickers provided"}), 400
    
    tickers = tickers.split(',')
    selected_stocks = [ticker.strip().upper() for ticker in tickers if ticker.strip().upper() in all_stocks]
    
    if not selected_stocks:
        logging.warning("None of the requested tickers are available.")
        return jsonify({"error": "None of the requested tickers are available"}), 404

    stocks_data = []
    with ThreadPoolExecutor(max_workers=5) as executor:
        futures = [executor.submit(retry_fetch, fetch_stock_data, ticker) for ticker in selected_stocks]
        for future in futures:
            result = future.result()
            if result:
                stocks_data.append(result)
    
    if not stocks_data:
        logging.error("No valid data returned for the requested tickers.")
        return jsonify({"error": "No valid data returned for the requested tickers"}), 404

    logging.info("Stocks data to be returned: %s", stocks_data)
    return jsonify(stocks_data)

# Route to serve the HTML page
@app.route('/')
def index():
    return render_template('stock.html')

if __name__ == '__main__':
    app.run(debug=True, port=5004)
