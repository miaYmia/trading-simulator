# fetch_data.py
# --------------
# This script contains all the backend logic for:
# - Fetching real-time market data from Alpha Vantage
# - Adding technical indicators (SMA)
# - Simulating a trading strategy
# - Saving data to a local SQLite database

import sqlite3
import requests
import pandas as pd
import os
from dotenv import load_dotenv
from pathlib import Path

# Load the API key from a .env file securely
env_path = Path(__file__).parent / '.env'
load_dotenv(dotenv_path=env_path)
API_KEY = os.getenv("ALPHA_VANTAGE_KEY")

# Fetch historical daily stock price data from Alpha Vantage
def fetch_daily_stock_data(symbol):
    url = "https://www.alphavantage.co/query"
    params = {
        "function": "TIME_SERIES_DAILY",  # free endpoint
        "symbol": symbol,
        "outputsize": "compact",
        "apikey": API_KEY
    }

    response = requests.get(url, params=params)
    data = response.json()

    if "Time Series (Daily)" not in data:
        raise ValueError(f"API error or limit hit: {data}")

    # Convert API response into DataFrame
    df = pd.DataFrame.from_dict(data["Time Series (Daily)"], orient="index")
    df = df.rename(columns={
        "1. open": "Open",
        "2. high": "High",
        "3. low": "Low",
        "4. close": "Close",
        "6. volume": "Volume"
    })

    df.index = pd.to_datetime(df.index)
    df = df.sort_index()
    return df.astype(float)

# Add moving average columns to the DataFrame
def add_moving_averages(df, windows=[5, 10]):
    for window in windows:
        df[f"SMA_{window}"] = df["Close"].rolling(window=window).mean()
    return df
# Simulate a simple SMA crossover trading strategy
def simulate_sma_crossover_strategy(df, initial_cash=10000):
    cash = initial_cash
    shares = 0
    portfolio = []

    prev_sma_5 = prev_sma_10 = None
    position = None  # Track current position

    for date, row in df.iterrows():
        sma_5 = row.get("SMA_5")
        sma_10 = row.get("SMA_10")
        price = row["Close"]

        if pd.isna(sma_5) or pd.isna(sma_10):
            portfolio.append((date, cash + shares * price, position))
            continue

        # Buy condition: SMA_5 crosses above SMA_10
        if sma_5 > sma_10 and (prev_sma_5 is None or prev_sma_5 <= prev_sma_10) and cash > 0:
            shares = cash // price
            cash -= shares * price
            position = 'long'

        # Sell condition: SMA_5 crosses below SMA_10
        elif sma_5 < sma_10 and (prev_sma_5 is None or prev_sma_5 >= prev_sma_10) and shares > 0:
            cash += shares * price
            shares = 0
            position = None

        total_value = cash + shares * price
        portfolio.append((date, total_value, position))

        prev_sma_5, prev_sma_10 = sma_5, sma_10

    return pd.DataFrame(portfolio, columns=["Date", "Portfolio Value", "Position"]).set_index("Date")

# Save stock data to a SQLite database
def save_to_db(df, symbol, db_name="stocks.db"):
    conn = sqlite3.connect(db_name)
    cursor = conn.cursor()

    # Create table if it doesn't already exist
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS daily_prices (
            symbol TEXT,
            date TEXT PRIMARY KEY,
            open REAL,
            high REAL,
            low REAL,
            close REAL,
            volume INTEGER
        )
    """)

    # Insert or update rows
    for index, row in df.iterrows():
        date_str = index.strftime("%Y-%m-%d")
        cursor.execute("""
            INSERT OR REPLACE INTO daily_prices (symbol, date, open, high, low, close, volume)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            symbol,
            date_str,
            row["Open"],
            row["High"],
            row["Low"],
            row["Close"],
            int(row["Volume"])
        ))

    conn.commit()
    conn.close()

# For local testing: run this file directly
if __name__ == "__main__":
    symbol = "MSFT"
    df = fetch_daily_stock_data(symbol)
    df = add_moving_averages(df)
    print(df.tail())
    save_to_db(df, symbol)
    sim_results = simulate_sma_crossover_strategy(df)
    print(sim_results.tail())
