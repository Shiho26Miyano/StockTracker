from flask import Flask, render_template, request, jsonify
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
import plotly.utils
import json
from datetime import datetime, timedelta
import os

app = Flask(__name__)

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

@app.route('/')
def index():
    return render_template('index.html', tickers=STOCK_TICKERS)

@app.route('/get_stock_data', methods=['POST'])
def get_stock_data():
    data = request.json
    ticker = data.get('ticker')
    period = data.get('period', '1mo')  # Default to 1 month
    
    try:
        stock = yf.Ticker(ticker)
        stock_data = stock.history(period=period)
        
        if stock_data.empty:
            app.logger.warning(f"No data for ticker {ticker} with period {period}")
            return jsonify({"error": f"No data available for ticker {ticker} and period {period}"}), 400
        
        # Get company info
        try:
            info = stock.info
            company_name = info.get('shortName', ticker)
            current_price = info.get('currentPrice', stock_data['Close'].iloc[-1] if not stock_data.empty else 0)
        except:
            company_name = ticker
            current_price = stock_data['Close'].iloc[-1] if not stock_data.empty else 0
        
        # Create plot
        fig = go.Figure()
        fig.add_trace(go.Candlestick(
            x=stock_data.index,
            open=stock_data['Open'],
            high=stock_data['High'],
            low=stock_data['Low'],
            close=stock_data['Close'],
            name=ticker
        ))
        
        fig.update_layout(
            title=f'{company_name} Stock Price',
            xaxis_title='Date',
            yaxis_title='Price (USD)',
            template='plotly_dark',
            xaxis_rangeslider_visible=False
        )
        
        # Get the plot as JSON
        plot_json = json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)
        
        # Calculate performance metrics
        if len(stock_data) > 1:
            start_price = stock_data['Close'].iloc[0]
            end_price = stock_data['Close'].iloc[-1]
            percent_change = ((end_price - start_price) / start_price) * 100
        else:
            percent_change = 0
            
        return jsonify({
            "plot": plot_json,
            "current_price": round(current_price, 2),
            "percent_change": round(percent_change, 2),
            "company_name": company_name
        })
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/compare', methods=['POST'])
def compare_stocks():
    data = request.json
    tickers = data.get('tickers', [])
    period = data.get('period', '1mo')
    
    if not tickers:
        return jsonify({"error": "No tickers provided"}), 400
    
    fig = go.Figure()
    
    # Normalize all data to percentage change from first day
    for ticker in tickers:
        try:
            stock = yf.Ticker(ticker)
            stock_data = stock.history(period=period)
            
            if not stock_data.empty:
                base_price = stock_data['Close'].iloc[0]
                normalized_prices = [(price/base_price - 1) * 100 for price in stock_data['Close']]
                
                fig.add_trace(go.Scatter(
                    x=stock_data.index,
                    y=normalized_prices,
                    mode='lines',
                    name=ticker
                ))
        except Exception as e:
            print(f"Error processing {ticker}: {str(e)}")
    
    fig.update_layout(
        title='Comparative Stock Performance (% Change)',
        xaxis_title='Date',
        yaxis_title='Percent Change (%)',
        template='plotly_dark'
    )
    
    plot_json = json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)
    return jsonify({"plot": plot_json})

@app.route('/test_yf')
def test_yf():
    import yfinance as yf
    try:
        hist = yf.Ticker("AAPL").history(period="1mo")
        if hist.empty:
            return "No data"
        return hist.to_html()
    except Exception as e:
        return str(e)

def max_profit(prices):
    min_price = float('inf')
    max_profit = 0
    for price in prices:
        if price < min_price:
            min_price = price
        elif price - min_price > max_profit:
            max_profit = price - min_price
    return max_profit

@app.route('/profit_calculator', methods=['GET', 'POST'])
def profit_calculator():
    result = None
    prices_input = ''
    if request.method == 'POST':
        prices_input = request.form.get('prices', '')
        try:
            prices = list(map(int, prices_input.split(',')))
            result = max_profit(prices)
        except Exception as e:
            result = f"Error: {e}"
    return render_template('profit_calculator.html', result=result, prices_input=prices_input)

if __name__ == '__main__':
    # Get port from environment variable or default to 5001
    port = int(os.environ.get("PORT", 5001))
    # In production, you shouldn't run with debug=True
    debug = os.environ.get("FLASK_DEBUG", "True") == "True"
    app.run(host='0.0.0.0', port=port, debug=debug) 