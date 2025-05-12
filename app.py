from flask import Flask, render_template, request, jsonify
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
import plotly.utils
import json
from datetime import datetime, timedelta

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
        hist = stock.history(period=period)
        
        if hist.empty:
            return jsonify({"error": "No data available for this ticker"}), 400
        
        # Get company info
        try:
            info = stock.info
            company_name = info.get('shortName', ticker)
            current_price = info.get('currentPrice', hist['Close'].iloc[-1] if not hist.empty else 0)
        except:
            company_name = ticker
            current_price = hist['Close'].iloc[-1] if not hist.empty else 0
        
        # Create plot
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
        
        # Get the plot as JSON
        plot_json = json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)
        
        # Calculate performance metrics
        if len(hist) > 1:
            start_price = hist['Close'].iloc[0]
            end_price = hist['Close'].iloc[-1]
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
            hist = stock.history(period=period)
            
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
            print(f"Error processing {ticker}: {str(e)}")
    
    fig.update_layout(
        title='Comparative Stock Performance (% Change)',
        xaxis_title='Date',
        yaxis_title='Percent Change (%)',
        template='plotly_dark'
    )
    
    plot_json = json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)
    return jsonify({"plot": plot_json})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001, debug=True) 