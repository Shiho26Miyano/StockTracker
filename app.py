from flask import Flask, render_template, request, jsonify, make_response
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
import plotly.utils
import json
from datetime import datetime, timedelta
import os
from functools import wraps
import time
from cachetools import TTLCache

app = Flask(__name__)

# Cache for storing stock data (TTL: 5 minutes)
stock_cache = TTLCache(maxsize=100, ttl=300)

# Rate limiting configuration
RATE_LIMIT = 30  # requests
RATE_WINDOW = 60  # seconds
request_history = {}

def rate_limit(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        now = time.time()
        ip = request.remote_addr
        
        # Clean old requests
        if ip in request_history:
            request_history[ip] = [t for t in request_history[ip] if now - t < RATE_WINDOW]
        else:
            request_history[ip] = []
        
        if len(request_history[ip]) >= RATE_LIMIT:
            return jsonify({"error": "Rate limit exceeded. Please try again later."}), 429
        
        request_history[ip].append(now)
        return f(*args, **kwargs)
    return decorated_function

# Stock tickers mapping
STOCK_TICKERS = {
    "apple": "AAPL",
    "microsoft": "MSFT",
    "amazon": "AMZN",
    "google": "GOOGL",
    "meta": "META",
    "tesla": "TSLA", 
    "nvidia": "NVDA",
    "jpmorgan": "JPM",
    "bankofamerica": "BAC",
    "walmart": "WMT"
}

def get_cached_stock_data(ticker, period):
    cache_key = f"{ticker}_{period}"
    if cache_key in stock_cache:
        return stock_cache[cache_key]
    
    stock = yf.Ticker(ticker)
    hist = stock.history(period=period)
    info = stock.info
    
    data = {
        "history": hist,
        "info": info
    }
    stock_cache[cache_key] = data
    return data

@app.route('/')
def index():
    return render_template('index.html', tickers=STOCK_TICKERS)

@app.route('/get_stock_data', methods=['POST'])
@rate_limit
def get_stock_data():
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "No JSON data provided"}), 400
        
        ticker = data.get('ticker')
        period = data.get('period', '1mo')
        
        if not ticker:
            return jsonify({"error": "No ticker provided"}), 400
        
        try:
            stock_data = get_cached_stock_data(ticker, period)
            hist = stock_data["history"]
            info = stock_data["info"]
            
            if hist.empty:
                return jsonify({"error": "No data available for this ticker"}), 400
            
            company_name = info.get('shortName', ticker)
            current_price = info.get('currentPrice', hist['Close'].iloc[-1] if not hist.empty else 0)
            
            fig = go.Figure()
            fig.add_trace(go.Candlestick(
                x=hist.index,
                open=hist['Open'],
                high=hist['High'],
                low=hist['Low'],
                close=hist['Close'],
                name=ticker
            ))
            
            fig.update_layout(
                title=f'{company_name} Stock Price',
                xaxis_title='Date',
                yaxis_title='Price (USD)',
                template='plotly_dark',
                xaxis_rangeslider_visible=False
            )
            
            plot_json = json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)
            
            if len(hist) > 1:
                start_price = hist['Close'].iloc[0]
                end_price = hist['Close'].iloc[-1]
                percent_change = ((end_price - start_price) / start_price) * 100
            else:
                percent_change = 0
            
            response_data = {
                "plot": plot_json,
                "current_price": round(current_price, 2),
                "percent_change": round(percent_change, 2),
                "company_name": company_name,
                "last_updated": datetime.now().isoformat()
            }
            
            response = make_response(jsonify(response_data))
            response.headers['Cache-Control'] = 'public, max-age=300'
            return response
            
        except Exception as e:
            app.logger.error(f"Error processing stock data for {ticker}: {str(e)}")
            return jsonify({"error": f"Failed to fetch stock data: {str(e)}"}), 500
            
    except Exception as e:
        app.logger.error(f"General error in get_stock_data: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500

@app.route('/compare', methods=['POST'])
@rate_limit
def compare_stocks():
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "No JSON data provided"}), 400
        
        tickers = data.get('tickers', [])
        period = data.get('period', '1mo')
        
        if not tickers:
            return jsonify({"error": "No tickers provided"}), 400
        
        if len(tickers) > 5:
            return jsonify({"error": "Maximum 5 stocks can be compared at once"}), 400
        
        fig = go.Figure()
        
        for ticker in tickers:
            try:
                stock_data = get_cached_stock_data(ticker, period)
                hist = stock_data["history"]
                
                if not hist.empty:
                    base_price = hist['Close'].iloc[0]
                    normalized_prices = [(price/base_price - 1) * 100 for price in hist['Close']]
                    
                    fig.add_trace(go.Scatter(
                        x=hist.index,
                        y=normalized_prices,
                        mode='lines',
                        name=ticker
                    ))
            except Exception as e:
                app.logger.error(f"Error processing {ticker}: {str(e)}")
        
        fig.update_layout(
            title='Comparative Stock Performance (% Change)',
            xaxis_title='Date',
            yaxis_title='Percent Change (%)',
            template='plotly_dark'
        )
        
        plot_json = json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)
        
        response = make_response(jsonify({"plot": plot_json}))
        response.headers['Cache-Control'] = 'public, max-age=300'
        return response
        
    except Exception as e:
        app.logger.error(f"General error in compare_stocks: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500

@app.route('/health')
def health_check():
    return jsonify({
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "version": os.environ.get("APP_VERSION", "1.0.0")
    })

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5001))
    debug = os.environ.get("FLASK_DEBUG", "False") == "True"
    app.run(host='0.0.0.0', port=port, debug=debug) 