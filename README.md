# StockTracker

A Python web application to track stock prices for major companies like Apple, Microsoft, Amazon, Google, Meta, Tesla, Nvidia, JPMorgan, Bank of America, and Walmart.

## Features

- Real-time stock data from Yahoo Finance
- Interactive candlestick charts
- Compare multiple stocks with normalized performance
- Select different time periods (1 day to 5 years)
- Responsive design for desktop and mobile

## Requirements

- Python 3.11
- Flask
- yfinance
- pandas
- plotly
- requests

## Installation

```sh
git clone <repository-url>
cd stock-tracker-app
pip install -r requirements.txt
```

## Usage

```sh
python app.py
```
Then open your browser at: [http://127.0.0.1:5000/](http://127.0.0.1:5000/)

- Select a stock to view its price chart
- Select multiple stocks and click "Compare Selected" for comparative performance
- Change the time period using the dropdown menu

## Notes

- Stock data is fetched from Yahoo Finance (yfinance)
- Data updates on request (not real-time streaming)
- Market data may be delayed by 15-20 minutes

## Deployment

For production, use Gunicorn:

```sh
gunicorn app:app
```
Or deploy to a platform like Fly.io or Railway (see Procfile and runtime.txt for Python 3.11 compatibility).
