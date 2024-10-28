import os
from flask import Flask, jsonify, render_template, request
import yfinance as yf
import requests
from urllib.parse import unquote
import concurrent.futures
import time
from flask_cors import CORS

# Define absolute path to the 'public' folder for templates
public_dir = os.path.abspath('../public')

# Initialize Flask app with 'public' as the template folder
app = Flask(__name__, template_folder=public_dir)
CORS(app, resources={r"/*": {"origins": "http://localhost:3000"}})  # Enable CORS for localhost:3000

# Log template folder for debugging
print("Template folder:", app.template_folder)

ALPHA_VANTAGE_API_KEY = '88H7TCY7HHPZQITS'

# Dictionary of sectors and their associated stocks
sector_to_stocks = {
    "Technology": ["COFORGE.NS", "PERSISTENT.NS", "MPHASIS.NS", "LTTS.NS", "TECHM.NS", "HCLTECH.NS", "TCS.NS", "INFY.NS", "LTIM.NS", "WIPRO.NS"],
    "PSU Bank": ["IOB.NS", "J&KBANK.NS", "MAHABANK.NS", "BANKBARODA.NS", "PNB.NS", "CANBK.NS", "UNIONBANK.NS", "CENTRALBK.NS", "UCOBANK.NS", "SBIN.NS", "INDIANB.NS", "BANKINDIA.NS"],
    "Media & Entertainment": ["NETWORK18.NS", "HATHWAY.NS", "NAZARA.NS", "ZEEL.NS", "PVRINOX.NS", "SAREGAMA.NS", "DISHTV.NS", "SUNTV.NS"],
    "Nifty Financial Services": ["BAJFINANCE.NS","LICHSGFIN.NS","SBICARD","SHRIRAMFIN", "ICICIPRULI.NS", "IEX.NS", "PEL.NS", "HDFCBANK.NS", "SBILIFE.NS", "BAJAJFINSV.NS", "MUTHOOTFIN.NS", "KOTAKBANK.NS", "HDFCAMC.NS", "CHOLAFIN.NS", "RECLTD.NS", "SBIN.NS", "HDFCLIFE.NS", "PFC.NS", "ICICIBANK.NS", "AXISBANK.NS", "ICICIGI.NS", "M&MFIN.NS"],
    "Consumer Goods": ["VBL.NS", "COLPAL.NS","UBL.NS", "RADICO.NS", "TATACONSUM.NS", "PGHH.NS", "BRITANNIA.NS", "EMAMILTD.NS", "MARICO.NS", "DABUR.NS",  "ITC.NS", "UNITDSPR.NS", "GODREJCP.NS", "HINDUNILVR.NS", "NESTLEIND.NS"],
    "Bank Nifty": ["BANDHANBNK.NS", "AUBANK.NS", "BANKBARODA.NS", "PNB.NS", "HDFCBANK.NS", "KOTAKBANK.NS", "INDUSINDBK.NS", "FEDERALBNK.NS", "SBIN.NS", "ICICIBANK.NS", "AXISBANK.NS", "IDFCFIRSTB.NS"],
    "Construction": ["EMBDL.NS", "SUNTECK.NS", "GODREJPROP.NS", "LODHA.NS", "OBEROIRLTY.NS", "PRESTIGE.NS", "SOBHA.NS", "BRIGADE.NS", "PHOENIXLTD.NS", "DLF.NS"],
    "Consumption": ["AMBER.NS", "DIXON.NS", "VGUARD.NS", "VOLTAS.NS", "ORIENTELEC.NS", "BATAINDIA.NS", "CROMPTON.NS", "BLUESTARCO.NS", "TTKPRESTIG.NS", "RELAXO.NS", "HAVELLS.NS", "TITAN.NS", "KAJARIACER.NS", "WHIRLPOOL.NS", "RAJESHEXPO.NS"],
    "Metals": ["WELCORP.NS", "HINDZINC.NS", "MOIL.NS", "NATIONALUM.NS", "NMDC.NS", "COALINDIA.NS", "JSL.NS", "JINDALSTEL.NS", "VEDL.NS", "ADANIENT.NS", "RATNAMANI.NS", "HINDALCO.NS", "HINDCOPPER.NS", "JSWSTEEL.NS", "TATASTEEL.NS", "APLAPOLLO.NS", "SAIL.NS"],
    "Nifty Oil & Gas": ["MGL.NS", "CASTROLIND.NS", "ATGL.NS", "GUJGASLTD.NS", "GSPL.NS", "AEGISLOG.NS", "JIOFIN.NS", "BPCL.NS", "IGL.NS", "ONGC.NS", "PETRONET.NS", "GAIL.NS", "RELIANCE.NS", "HINDPETRO.NS", "IOC.NS", "OIL.NS"],
    "Private Bank": ["BANDHANBNK.NS", "HDFCBANK.NS", "KOTAKBANK.NS", "INDUSINDBK.NS", "FEDERALBNK.NS", "CUB.NS", "RBLBANK.NS", "ICICIBANK.NS", "AXISBANK.NS", "IDFCFIRSTB.NS"],
    "Energy": ["ADANIGREEN.NS", "TATAPOWER.NS", "BPCL.NS", "ONGC.NS", "GAIL.NS", "RELIANCE.NS", "IOC.NS", "NTPC.NS", "POWERGRID.NS", "ADANIENSOL.NS"],
    "Automobile": ["TIINDIA.NS", "MOTHERSON.NS", "BAJAJ-AUTO.NS", "EXIDEIND.NS", "SONACOMS.NS", "ARE&M.NS", "ASHOKLEY.NS", "BOSCHLTD.NS", "MARUTI.NS", "BHARATFORG.NS", "TATAMOTORS.NS", "BALKRISIND.NS", "HEROMOTOCO.NS", "MRF.NS", "EICHERMOT.NS", "M&M.NS", "TVSMOTOR.NS"],
    "Nifty Healthcare Index": ["GRANULES.NS","ALKEM.NS" ,"ZYDUSLIFE.NS","LUPIN.NS", "GLENMARK.NS", "APOLLOHOSP.NS", "LAURUSLABS.NS", "BIOCON.NS", "SYNGENE.NS", "METROPOLIS.NS", "TORNTPHARM.NS", "DRREDDY.NS", "AUROPHARMA.NS", "MAXHEALTH.NS", "IPCALAB.NS", "DIVISLAB.NS", "LALPATHLAB.NS", "CIPLA.NS", "ABBOTINDIA.NS", "SUNPHARMA.NS"],
    "Pharma": ["GRANULES.NS","LUPIN.NS","SUNPHARMA.NS","ALKEM.NS","ZYDUSLIFE.NS", "STAR.NS", "GLENMARK.NS", "LAURUSLABS.NS", "PFIZER.NS", "BIOCON.NS", "APLLTD.NS", "NATCOPHARM.NS", "TORNTPHARM.NS", "SANOFI.NS", "DRREDDY.NS", "AUROPHARMA.NS", "IPCALAB.NS", "DIVISLAB.NS", "CIPLA.NS", "ABBOTINDIA.NS", "GLAND.NS"]
}

# Cache for sector performance and stock data (expiration set to 15 minutes)
sector_data_cache = {
    'data': {},
    'last_update': {}
}

CACHE_DURATION = 900 # 15 minutes

# Function to fetch individual stock data
def fetch_stock_data(symbol):
    stock_info = yf.Ticker(symbol)
    hist = stock_info.history(period="5d")  # Change to "5d" to fetch up to 5 days of history

    if len(hist) >= 2:
        # Extract the last two days' close prices
        yesterday_close = hist['Close'][-2]
        today_close = hist['Close'][-1]

        # Log the fetched values for debugging purposes
        print(f"Fetched data for {symbol} - Yesterday Close: {yesterday_close}, Today Close: {today_close}")

        # Calculate the percentage change between yesterday's close and today's close
        if yesterday_close > 0:
            change = ((today_close - yesterday_close) / yesterday_close) * 100
        else:
            change = 0

        # Return the stock data
        return {
            'symbol': symbol,
            'yesterday_close': yesterday_close,
            'today_close': today_close,
            'change': round(change, 2)  # Round the change to 2 decimal places
        }
    
    return None

# Function to fetch and cache stock data for a specific sector
def get_top_stock(sector_name):
    current_time = time.time()
    sector_name = sector_name.lower()

    # Check if the data is cached and still valid
    if sector_name in sector_data_cache['data'] and (current_time - sector_data_cache['last_update'].get(sector_name, 0)) < CACHE_DURATION:
        print(f"Returning cached data for sector: {sector_name}")
        return sector_data_cache['data'][sector_name]['top_stock'], sector_data_cache['data'][sector_name]['all_stocks']
    
    matched_sector = None
    for sector in sector_to_stocks:
        if sector.lower() == sector_name:
            matched_sector = sector
            break
    
    if matched_sector:
        stock_symbols = sector_to_stocks.get(matched_sector, [])
        stock_data = []

        # Fetch stock data concurrently
        with concurrent.futures.ThreadPoolExecutor() as executor:
            results = executor.map(fetch_stock_data, stock_symbols)
        
        stock_data = [result for result in results if result]

        # Sort stocks by percentage change
        sorted_stocks = sorted(stock_data, key=lambda x: x['change'], reverse=True)

        if sorted_stocks:
            top_stock = sorted_stocks[0]
            # Cache the result
            sector_data_cache['data'][sector_name] = {
                'top_stock': top_stock,
                'all_stocks': sorted_stocks
            }
            sector_data_cache['last_update'][sector_name] = current_time
            print(f"Updated cache for sector: {sector_name}")
            return top_stock, sorted_stocks
        else:
            return None, []
    else:
        return None, []

# Route to get trending stocks in a sector
@app.route('/trending', methods=['GET'])
def get_trending():
    sector = request.args.get('sector')
    print(f"Received sector: '{sector}'")  # Debugging log
    if sector:
        sector = unquote(sector)
        top_stock, all_stocks = get_top_stock(sector)
        if top_stock:
            return jsonify({
                'top_stock': top_stock,
                'all_stocks': all_stocks
            })
        else:
            return jsonify({
                'error': f'Sector "{sector}" not found or no stock data available'
            }), 404
    else:
        return jsonify({
            'error': 'Sector not provided in the request'
        }), 400

# Main route to render tracking.html
@app.route('/')
def index():
    return render_template('tracking.html')

if __name__ == '__main__':
    app.run(debug=True, port=5003)
