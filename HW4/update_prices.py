# update_prices.py
import yfinance as yf
import requests
from pymongo import MongoClient, UpdateOne
from dotenv import load_dotenv
import os
import time
from datetime import datetime
import pandas as pd

load_dotenv()
MONGO_URI = os.getenv("MONGO_URI")
FINNHUB_API_KEY = os.getenv("FINNHUB_API_KEY")

try:
    client = MongoClient(MONGO_URI)
    db = client.stock_portfolio_db
    prices_collection = db.prices
    holdings_collection = db.holdings
except Exception as e:
    print(f"Price updater could not connect to MongoDB: {e}")
    db = None

def fetch_from_yfinance(symbols, session):
    """Primary fetch function using yfinance."""
    print(f"Attempting to fetch {len(symbols)} symbols from yfinance...")
    try:
        data = yf.download(tickers=symbols, period='1d', progress=False, session=session)
        if data.empty:
            return {}
        
        results = {}
        for symbol in symbols:
            price, prev_close = (None, None)
            if len(symbols) == 1 and not data.empty:
                last_row = data.iloc[-1]
                price = last_row['Close']
                prev_close = last_row['Open']
            elif symbol in data['Close'] and not pd.isna(data['Close'][symbol].iloc[-1]):
                price = data['Close'][symbol].iloc[-1]
                prev_close = data['Open'][symbol].iloc[-1]
            
            if price and prev_close:
                results[symbol] = {'current_price': price, 'previous_close': prev_close}
        return results
    except Exception as e:
        print(f"Yfinance download failed: {e}")
        return {}

def fetch_from_finnhub(symbols, session):
    """Fallback fetch function using Finnhub."""
    if not FINNHUB_API_KEY:
        return {}
    
    print(f"Attempting Finnhub fallback for {len(symbols)} symbols...")
    results = {}
    for symbol in symbols:
        try:
            quote_url = f"https://finnhub.io/api/v1/quote?symbol={symbol}&token={FINNHUB_API_KEY}"
            res = session.get(quote_url, timeout=5)
            res.raise_for_status()
            data = res.json()
            if data.get('c', 0) > 0:
                results[symbol] = {'current_price': data['c'], 'previous_close': data['pc']}
            time.sleep(1)
        except Exception as e:
            print(f"Finnhub failed for {symbol}: {e}")
    return results

def update_stock_prices():
    """Main function to fetch and update all unique stock prices in the database."""
    if db is None:
        print("No database connection. Aborting price update.")
        return

    try:
        unique_symbols = holdings_collection.distinct("symbol")
        if not unique_symbols:
            print("No holdings found. Nothing to update.")
            return
    except Exception as e:
        print(f"Error fetching unique symbols: {e}")
        return

    print(f"Found {len(unique_symbols)} unique symbols to update: {', '.join(unique_symbols)}")

    session = requests.Session()
    session.headers['User-Agent'] = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    
    price_data = fetch_from_yfinance(unique_symbols, session)
    
    failed_symbols = [s for s in unique_symbols if s not in price_data]
    if failed_symbols:
        finnhub_data = fetch_from_finnhub(failed_symbols, session)
        price_data.update(finnhub_data)

    if not price_data:
        print("Could not fetch any price data from any source.")
        return

    update_operations = []
    for symbol, data in price_data.items():
        try:
            name = yf.Ticker(symbol, session=session).info.get('longName', symbol)
        except:
            name = symbol

        operation = UpdateOne(
            {'symbol': symbol},
            {'$set': {
                'symbol': symbol,
                'current_price': data['current_price'],
                'previous_close': data['previous_close'],
                'name': name,
                'last_updated': datetime.utcnow()
            }},
            upsert=True
        )
        update_operations.append(operation)

    if update_operations:
        print(f"Preparing to bulk update {len(update_operations)} price records...")
        result = prices_collection.bulk_write(update_operations)
        print(f"Bulk update complete. Matched: {result.matched_count}, Upserted: {result.upserted_count}")

if __name__ == "__main__":
    update_stock_prices()