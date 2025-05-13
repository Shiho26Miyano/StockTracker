# StockTracker

A Python web application to track stock prices for Apple, Microsoft, Amazon, Google, Meta, Tesla, Nvidia, JPMorgan, Bank of America, and Walmart.

## Features

- View real-time stock data from Yahoo Finance
- Interactive candlestick charts for individual stocks
- Compare multiple stocks with normalized performance charts
- Select different time periods (1 day to 5 years)
- Responsive design for desktop and mobile

<img width="1338" alt="Screenshot 2025-05-12 at 1 23 14 AM" src="https://github.com/user-attachments/assets/ea3783ec-121d-4f9c-ae81-2518b6714de5" />


## Requirements

- Python 3.11
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

## Stock Data Retrieval Flowchart

```mermaid
flowchart TD
    A[User requests stock data (ticker, period)] --> B[Call yfinance: Ticker(ticker).history(period)]
    B --> C{Is DataFrame empty?}
    C -- No --> D[Return stock data to user]
    C -- Yes --> E[Log warning: No data for ticker/period]
    E --> F[Try alias ticker (e.g., GOOGL -> GOOG)]
    F --> G[Call yfinance: Ticker(alias).history(period)]
    G --> H{Is DataFrame empty?}
    H -- No --> I[Return alias stock data to user]
    H -- Yes --> J[Return error: No data available for ticker and period]
    J --> K[Suggest: Try different period, check ticker, or try again later]
```

## Notes

- Stock data is fetched from Yahoo Finance (yfinance)
- The application updates data on request, not in real-time
- Market data may be delayed by 15-20 minutes

## Deployment

For production deployment, consider using Gunicorn:

```
gunicorn app:app
```

Or deploy to a platform like Fly.io or Railway using the included Procfile and runtime.txt for Python 3.11 compatibility.
