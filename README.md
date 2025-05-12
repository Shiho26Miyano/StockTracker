# StockTracker

A Python web application to track stock prices for Apple, TikTok (ByteDance), Walmart, and Costco.

## Features

- View real-time stock data from Yahoo Finance
- Interactive candlestick charts for individual stocks
- Compare multiple stocks with normalized performance charts
- Select different time periods (1 day to 5 years)
- Responsive design for desktop and mobile

## Requirements

- Python 3.12
- Flask
- yfinance
- pandas
- plotly
- requests

## Installation

1. Clone this repository:
```
git clone <repository-url>
cd stock-tracker-app
```

2. Install required packages:
```
pip install -r requirements.txt
```

## Usage

1. Run the application:
```
python app.py
```

2. Open a web browser and navigate to:
```
http://127.0.0.1:5000/
```

3. Use the interface to:
   - Select a stock from the list to view its price chart
   - Select multiple stocks and click "Compare Selected" to see comparative performance
   - Change the time period using the dropdown menu

## Notes

- Stock data is fetched from Yahoo Finance (yfinance)
- ByteDance (TikTok parent company) is represented by the ticker BDNCE.MX as an example
- The application updates data on request, not in real-time
- Market data may be delayed by 15-20 minutes

## Deployment

For production deployment, consider using Gunicorn:

```
gunicorn app:app
```

Or deploy to a platform like Heroku using the included Procfile.
