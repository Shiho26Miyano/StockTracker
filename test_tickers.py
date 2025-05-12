import yfinance as yf
import pandas as pd

# List of potential stock tickers to test
tickers_to_test = [
    "AAPL",  # Apple
    "MSFT",  # Microsoft
    "AMZN",  # Amazon
    "GOOGL", # Alphabet (Google)
    "GOOG",  # Alphabet (Google) Class C
    "META",  # Meta (Facebook)
    "TSLA",  # Tesla
    "NVDA",  # NVIDIA
    "JPM",   # JPMorgan Chase
    "BAC",   # Bank of America
    "WMT",   # Walmart
    "COST",  # Costco
    "JNJ",   # Johnson & Johnson
    "PG",    # Procter & Gamble
    "MA",    # Mastercard
    "V",     # Visa
    "DIS",   # Disney
    "NFLX",  # Netflix
    "PYPL",  # PayPal
    "ADBE",  # Adobe
    "INTC",  # Intel
    "AMD",   # AMD
    "T",     # AT&T
    "VZ",    # Verizon
    "KO",    # Coca-Cola
    "PEP",   # PepsiCo
    "XOM",   # ExxonMobil
    "CVX"    # Chevron
]

print("Testing stock tickers...")
accessible_tickers = []

for ticker_symbol in tickers_to_test:
    print(f"Testing {ticker_symbol}...", end="")
    try:
        ticker = yf.Ticker(ticker_symbol)
        hist = ticker.history(period="5d")
        
        if not hist.empty:
            company_name = ticker.info.get('shortName', ticker_symbol)
            accessible_tickers.append((ticker_symbol, company_name))
            print(f" SUCCESS - {company_name}")
        else:
            print(" FAILED - No data available")
            
    except Exception as e:
        print(f" ERROR - {str(e)}")
    
    # Stop after finding 10 accessible tickers
    if len(accessible_tickers) >= 10:
        break

print("\n\nAccessible Tickers:")
print("==================")
for i, (symbol, name) in enumerate(accessible_tickers, 1):
    print(f"{i}. {symbol}: {name}")

if accessible_tickers:
    print("\nSample code for app.py:")
    print("# Stock tickers mapping")
    print("STOCK_TICKERS = {")
    for symbol, name in accessible_tickers:
        key = name.lower().replace(' ', '_')
        print(f'    "{key}": "{symbol}",')
    print("}")
else:
    print("\nNo accessible tickers found. Check your internet connection or Yahoo Finance API status.") 