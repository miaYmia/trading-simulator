# app.py
# ---------------
# Streamlit app that lets users simulate a moving average crossover trading strategy
# Includes:
# - User input for stock symbols
# - Chart with buy/sell signals using Plotly
# - Portfolio performance chart
# - Data preview and feedback messages

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from fetch_data import (
    fetch_daily_stock_data,
    add_moving_averages,
    simulate_sma_crossover_strategy,
    save_to_db,
)

# Configure the Streamlit app layout and title
st.set_page_config(page_title="Trading Strategy Simulator", layout="centered")

st.title("📈 Trading Strategy Simulator")
st.markdown("Enter a stock ticker to simulate a moving average crossover strategy.")

# Text input for stock symbol
symbol = st.text_input("Stock Symbol", value="MSFT").upper()

# Plotly chart for price with buy/sell markers
def plot_signals(df, sim_results):
    fig = go.Figure()

    # Price and moving averages
    fig.add_trace(go.Scatter(x=df.index, y=df["Close"], mode="lines", name="Close Price"))
    fig.add_trace(go.Scatter(x=df.index, y=df["SMA_5"], mode="lines", name="SMA 5"))
    fig.add_trace(go.Scatter(x=df.index, y=df["SMA_10"], mode="lines", name="SMA 10"))

    # Identify buy/sell crossover points from simulation output
    position_series = sim_results["Position"]
    buy_dates = position_series[(position_series.shift(1) != "long") & (position_series == "long")].index
    sell_dates = position_series[(position_series.shift(1) == "long") & (position_series != "long")].index

    # Add buy markers
    fig.add_trace(go.Scatter(
        x=buy_dates,
        y=df.loc[buy_dates]["Close"],
        mode="markers",
        marker=dict(color="green", size=10, symbol="triangle-up"),
        name="Buy Signal"
    ))

    # Add sell markers
    fig.add_trace(go.Scatter(
        x=sell_dates,
        y=df.loc[sell_dates]["Close"],
        mode="markers",
        marker=dict(color="red", size=10, symbol="triangle-down"),
        name="Sell Signal"
    ))

    fig.update_layout(title="Price with Buy/Sell Signals", xaxis_title="Date", yaxis_title="Price")
    return fig

# Run simulation on button click
if st.button("Run Simulation"):
    with st.spinner("Fetching data and running strategy..."):
        try:
            # Get and process data
            df = fetch_daily_stock_data(symbol)
            df = add_moving_averages(df)
            save_to_db(df, symbol)
            results = simulate_sma_crossover_strategy(df)

            # Show visualizations and data
            st.subheader("Price Chart with Buy/Sell Signals")
            st.plotly_chart(plot_signals(df, results))

            st.subheader("Portfolio Value Over Time")
            st.line_chart(results["Portfolio Value"])

            st.subheader("Recent Data Snapshot")
            st.dataframe(df.tail())

            st.success("Simulation complete ✅")

        except Exception as e:
            st.error(f"An error occurred: {e}")
