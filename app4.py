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
all_stocks = ['UNITDSPR.NS', 'DLF.NS', 'IDFCFIRSTB.NS', 'PETRONET.NS', 'CHOLAFIN.NS', 'DRREDDY.NS', 'M&MFIN.NS', 'BAJAJ-AUTO.NS', 'SBIN.NS', 'FEDERALBNK.NS', 'PNB.NS', 'AEGISLOG.NS', 'BATAINDIA.NS', 'HEROMOTOCO.NS', 'RELAXO.NS', 'SBICARD', 'VOLTAS.NS', 'MUTHOOTFIN.NS', 'TECHM.NS', 'ONGC.NS', 'EMAMILTD.NS', 'MARICO.NS', 'HINDALCO.NS', 'BRIGADE.NS', 'AUROPHARMA.NS', 'BOSCHLTD.NS', 'GODREJCP.NS', 'LICHSGFIN.NS', 'KOTAKBANK.NS', 'VBL.NS', 'ASHOKLEY.NS', 'WIPRO.NS', 'LAURUSLABS.NS', 'MARUTI.NS', 'NETWORK18.NS', 'MPHASIS.NS', 'CUB.NS', 'MAXHEALTH.NS', 'HATHWAY.NS', 'DISHTV.NS', 'MGL.NS', 'BANDHANBNK.NS', 'UBL.NS', 'RAJESHEXPO.NS', 'GODREJPROP.NS', 'ZYDUSLIFE.NS', 'BPCL.NS', 'ORIENTELEC.NS', 'SUNTV.NS', 'ZEEL.NS', 'ADANIGREEN.NS', 'VEDL.NS', 'BHARATFORG.NS', 'LODHA.NS', 'HINDUNILVR.NS', 'BAJAJFINSV.NS', 'SUNPHARMA.NS', 'HINDCOPPER.NS', 'OIL.NS', 'RECLTD.NS', 'BIOCON.NS', 'GSPL.NS', 'TATASTEEL.NS', 'STAR.NS', 'TATAMOTORS.NS', 'PFIZER.NS', 'SOBHA.NS', 'NATIONALUM.NS', 'APLAPOLLO.NS', 'JINDALSTEL.NS', 'TVSMOTOR.NS', 'ICICIPRULI.NS', 'SUNTECK.NS', 'COFORGE.NS', 'MAHABANK.NS', 'HDFCBANK.NS', 'PVRINOX.NS', 'VGUARD.NS', 'BRITANNIA.NS', 'UNIONBANK.NS', 'EXIDEIND.NS', 'BALKRISIND.NS', 'RELIANCE.NS', 'TATAPOWER.NS', 'UCOBANK.NS', 'ICICIGI.NS', 'JSL.NS', 'JSWSTEEL.NS', 'CROMPTON.NS', 'TIINDIA.NS', 'ABBOTINDIA.NS', 'APLLTD.NS', 'SONACOMS.NS', 'IEX.NS', 'SYNGENE.NS', 'ARE&M.NS', 'ALKEM.NS', 'ADANIENT.NS', 'GLAND.NS', 'INFY.NS', 'POWERGRID.NS', 'SHRIRAMFIN', 'GUJGASLTD.NS', 'ICICIBANK.NS', 'LALPATHLAB.NS', 'INDUSINDBK.NS', 'HDFCAMC.NS', 'INDIANB.NS', 'GAIL.NS', 'SANOFI.NS', 'IGL.NS', 'APOLLOHOSP.NS', 'LTIM.NS', 'BANKINDIA.NS', 'RADICO.NS', 'ATGL.NS', 'CANBK.NS', 'J&KBANK.NS', 'WELCORP.NS', 'TATACONSUM.NS', 'BAJFINANCE.NS', 'NESTLEIND.NS', 'ADANIENSOL.NS', 'M&M.NS', 'SAIL.NS', 'AUBANK.NS', 'CIPLA.NS', 'CASTROLIND.NS', 'PRESTIGE.NS', 'BLUESTARCO.NS', 'RBLBANK.NS', 'PEL.NS', 'WHIRLPOOL.NS', 'TCS.NS', 'PERSISTENT.NS', 'LUPIN.NS', 'PGHH.NS', 'EMBDL.NS', 'NMDC.NS', 'COALINDIA.NS', 'DIXON.NS', 'HDFCLIFE.NS', 'HINDPETRO.NS', 'DIVISLAB.NS', 'LTTS.NS', 'COLPAL.NS', 'HAVELLS.NS', 'CENTRALBK.NS', 'PFC.NS', 'MRF.NS', 'KAJARIACER.NS', 'HCLTECH.NS', 'AMBER.NS', 'HINDZINC.NS', 'NTPC.NS', 'SBILIFE.NS', 'AXISBANK.NS', 'TITAN.NS', 'EICHERMOT.NS', 'METROPOLIS.NS', 'TTKPRESTIG.NS', 'GRANULES.NS', 'GLENMARK.NS', 'BANKBARODA.NS', 'MOIL.NS', 'MOTHERSON.NS', 'RATNAMANI.NS', 'NAZARA.NS', 'IOB.NS', 'ITC.NS', 'IPCALAB.NS', 'SAREGAMA.NS', 'IOC.NS', 'NATCOPHARM.NS', 'OBEROIRLTY.NS', 'PHOENIXLTD.NS', 'TORNTPHARM.NS', 'DABUR.NS', 'JIOFIN.NS']

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
