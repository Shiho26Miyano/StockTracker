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
import random
import requests
from requests.exceptions import HTTPError

app = Flask(__name__)

# Cache for storing stock data (TTL: 10 minutes)
stock_cache = TTLCache(maxsize=100, ttl=600)

# Rate limiting configuration
RATE_LIMIT = 30  # requests
RATE_WINDOW = 60  # seconds
request_history = {}

# Yahoo Finance rate limiting handling
YF_MAX_RETRIES = int(os.environ.get('YF_MAX_RETRIES', 5))
YF_BACKOFF_FACTOR = float(os.environ.get('YF_BACKOFF_FACTOR', 2))
YF_INITIAL_WAIT = float(os.environ.get('YF_INITIAL_WAIT', 2))
YF_TIMEOUT = int(os.environ.get('YF_TIMEOUT', 30))

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

def get_stock_with_retry(ticker, period):
    """Fetch stock data with exponential backoff retry logic"""
    retries = 0
    while retries < YF_MAX_RETRIES:
        try:
            # Use a session with increased timeout
            session = requests.Session()
            session.timeout = YF_TIMEOUT
            
            stock = yf.Ticker(ticker, session=session)
            
            # First try to get history data with minimal parameters
            hist = stock.history(period=period)
            
            # If we got history data, try to get minimal info separately
            # This helps avoid the more complex and error-prone full info request
            info = {}
            try:
                # Only get essential info fields
                minimal_info = stock.get_fast_info()
                info = {
                    'shortName': minimal_info.get('shortName', ticker),
                    'regularMarketPrice': minimal_info.get('regularMarketPrice', None),
                    'previousClose': minimal_info.get('previousClose', None)
                }
            except Exception as info_err:
                app.logger.warning(f"Could not get fast info for {ticker}: {str(info_err)}")
                # Fallback to full info only if needed
                try:
                    info = stock.info
                except Exception as full_info_err:
                    app.logger.warning(f"Could not get full info for {ticker}: {str(full_info_err)}")
                    # Continue anyway since we have hist data
            
            # Check if we got valid data
            if hist.empty:
                raise ValueError("Empty history data received")
            
            return {
                "history": hist,
                "info": info
            }
            
        except HTTPError as e:
            if hasattr(e, 'response') and e.response and e.response.status_code == 429:
                wait_time = YF_INITIAL_WAIT * (YF_BACKOFF_FACTOR ** retries) + random.uniform(0, 1)
                app.logger.warning(f"Rate limited by Yahoo Finance. Retrying in {wait_time:.2f} seconds...")
                time.sleep(wait_time)
                retries += 1
            else:
                app.logger.error(f"HTTP error for {ticker}: {str(e)}")
                # Try a different approach
                if retries < YF_MAX_RETRIES - 1:
                    wait_time = YF_INITIAL_WAIT * (YF_BACKOFF_FACTOR ** retries) + random.uniform(0, 1)
                    app.logger.warning(f"Retrying with different approach in {wait_time:.2f} seconds...")
                    time.sleep(wait_time)
                    retries += 1
                else:
                    raise
        except Exception as e:
            # For other exceptions, retry with backoff
            wait_time = YF_INITIAL_WAIT * (YF_BACKOFF_FACTOR ** retries) + random.uniform(0, 1)
            app.logger.warning(f"Error fetching data for {ticker}: {str(e)}. Retrying in {wait_time:.2f} seconds...")
            time.sleep(wait_time)
            retries += 1
    
    # If we've exhausted retries, try one last approach with just historical data
    try:
        app.logger.warning(f"Last attempt for {ticker}: fetching only historical data")
        stock = yf.Ticker(ticker)
        hist = stock.history(period=period)
        
        if not hist.empty:
            return {
                "history": hist,
                "info": {"shortName": ticker}
            }
    except Exception as last_err:
        app.logger.error(f"Final attempt failed for {ticker}: {str(last_err)}")
        
    # If we get here, all attempts have failed
    raise Exception(f"Failed to fetch data for {ticker} after {YF_MAX_RETRIES} retries")

def get_cached_stock_data(ticker, period):
    """Get stock data with caching and retry logic"""
    cache_key = f"{ticker}_{period}"
    
    # Try to get from cache first
    if cache_key in stock_cache:
        app.logger.info(f"Cache hit for {ticker}")
        return stock_cache[cache_key]
    
    # If not in cache, fetch with retry logic
    app.logger.info(f"Cache miss for {ticker}, fetching from Yahoo Finance")
    data = get_stock_with_retry(ticker, period)
    
    # Store in cache
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
            # Add a small random delay to prevent simultaneous Yahoo Finance requests
            time.sleep(random.uniform(0.1, 0.5))
            
            stock_data = get_cached_stock_data(ticker, period)
            hist = stock_data["history"]
            info = stock_data["info"]
            
            if hist.empty:
                return jsonify({"error": "No data available for this ticker"}), 400
            
            # Get company name with multiple fallbacks
            company_name = ticker
            if info:
                if 'shortName' in info:
                    company_name = info.get('shortName')
                elif 'longName' in info:
                    company_name = info.get('longName')
            
            # Get current price with multiple fallbacks
            current_price = None
            if info:
                for price_field in ['currentPrice', 'regularMarketPrice', 'previousClose', 'open']:
                    if price_field in info and info[price_field] is not None:
                        current_price = info[price_field]
                        break
            
            # If we still don't have a price, use history
            if current_price is None and not hist.empty:
                current_price = hist['Close'].iloc[-1]
            
            # If we still don't have a price (very unlikely), use a placeholder
            if current_price is None:
                current_price = 0
                
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
            response.headers['Cache-Control'] = 'public, max-age=600'
            return response
            
        except Exception as e:
            app.logger.error(f"Error processing stock data for {ticker}: {str(e)}")
            
            # Create a simple fallback visualization
            dates = pd.date_range(start=datetime.now() - timedelta(days=30), end=datetime.now(), freq='D')
            fallback_fig = go.Figure()
            
            fallback_fig.add_annotation(
                x=0.5,
                y=0.5,
                xref="paper",
                yref="paper",
                text=f"Unable to load data for {ticker}<br>Please try again later",
                showarrow=False,
                font=dict(size=20)
            )
            
            fallback_fig.update_layout(
                title=f'Data Temporarily Unavailable - {ticker}',
                template='plotly_dark',
                xaxis=dict(visible=False),
                yaxis=dict(visible=False)
            )
            
            fallback_plot = json.dumps(fallback_fig, cls=plotly.utils.PlotlyJSONEncoder)
            
            response_data = {
                "plot": fallback_plot,
                "current_price": 0,
                "percent_change": 0,
                "company_name": ticker,
                "last_updated": datetime.now().isoformat(),
                "error": f"Failed to fetch stock data: {str(e)}",
                "is_fallback": True
            }
            
            response = make_response(jsonify(response_data))
            # Short cache time for errors
            response.headers['Cache-Control'] = 'public, max-age=60'
            return response
            
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
        errors = []
        successful_tickers = []
        
        for ticker in tickers:
            try:
                # Add a small random delay between stocks
                time.sleep(random.uniform(0.5, 1.0))
                
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
                    successful_tickers.append(ticker)
            except Exception as e:
                app.logger.error(f"Error processing {ticker}: {str(e)}")
                errors.append(f"{ticker}: {str(e)}")
        
        # If we couldn't get data for any tickers
        if not fig.data and errors:
            # Create fallback visualization
            fallback_fig = go.Figure()
            
            fallback_fig.add_annotation(
                x=0.5,
                y=0.5,
                xref="paper",
                yref="paper",
                text="Unable to load comparison data<br>Please try again later",
                showarrow=False,
                font=dict(size=20)
            )
            
            fallback_fig.update_layout(
                title='Data Temporarily Unavailable',
                template='plotly_dark',
                xaxis=dict(visible=False),
                yaxis=dict(visible=False)
            )
            
            fallback_plot = json.dumps(fallback_fig, cls=plotly.utils.PlotlyJSONEncoder)
            return jsonify({
                "plot": fallback_plot, 
                "error": "Failed to retrieve data for any tickers", 
                "details": errors,
                "is_fallback": True
            })
        
        # If we're here, we have at least some data
        if successful_tickers:
            fig.update_layout(
                title='Comparative Stock Performance (% Change)',
                xaxis_title='Date',
                yaxis_title='Percent Change (%)',
                template='plotly_dark'
            )
            
            # Add annotation if some tickers failed
            if errors:
                failed_tickers = [e.split(':')[0].strip() for e in errors]
                fig.add_annotation(
                    x=0.5,
                    y=0.02,
                    xref="paper",
                    yref="paper",
                    text=f"Failed to load: {', '.join(failed_tickers)}",
                    showarrow=False,
                    font=dict(size=12, color="red")
                )
        
        plot_json = json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)
        
        response_data = {
            "plot": plot_json,
            "successful_tickers": successful_tickers
        }
        
        if errors:
            response_data["partial_errors"] = errors
        
        response = make_response(jsonify(response_data))
        response.headers['Cache-Control'] = 'public, max-age=600'
        return response
        
    except Exception as e:
        app.logger.error(f"General error in compare_stocks: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500

@app.route('/health')
def health_check():
    """Health check endpoint for monitoring and container orchestration."""
    try:
        # Just check if pandas is working, don't hit external APIs for health check
        pd.DataFrame([1])  # Test pandas
        return jsonify({
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "version": os.environ.get("APP_VERSION", "1.0.0")
        })
    except Exception as e:
        app.logger.error(f"Health check failed: {str(e)}")
        return jsonify({
            "status": "unhealthy",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }), 500

if __name__ == '__main__':
    # Get port from environment variable or default to 8080
    port = int(os.environ.get("PORT", 8080))
    debug = os.environ.get("FLASK_DEBUG", "False") == "True"
    app.run(host='0.0.0.0', port=port, debug=debug) 