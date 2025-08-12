import streamlit as st
import pandas as pd
import pandas_ta as ta
import os
import datetime
from strategy import apply_strategy, load_data  # assuming you have these defined

st.title("📈 Stock Strategy Analyzer")

# Sidebar Inputs for Stock and Timeframe
stock = st.selectbox("Select Stock", ["RELIANCE", "TCS", "INFY"], key="stock_select")
timeframe = st.selectbox("Select Timeframe", ["1", "5", "15", "30", "60"], key="timeframe_select")

# Inputs for Date Range and Indicator Periods
from_date = st.date_input("From Date", value=datetime.date(2025, 7, 10), key="from_date")
to_date = st.date_input("To Date", value=datetime.date(2025, 7, 23), key="to_date")

ema_period = st.slider("EMA Period", min_value=5, max_value=50, value=20, key="ema_period")
rsi_period = st.slider("RSI Period", min_value=5, max_value=50, value=14, key="rsi_period")
supertrend_period = st.slider("Supertrend Period", min_value=5, max_value=50, value=10, key="supertrend_period")
supertrend_multiplier = st.slider("Supertrend Multiplier", min_value=1.0, max_value=10.0, value=3.0, step=0.1, key="supertrend_multiplier")

# Trigger the analysis when the button is pressed
if st.button("Run Analysis"):
    # Construct the file path based on stock and timeframe
    file_path = f"stock_data/NSE_{stock.upper()}_{timeframe}.csv"

    # Check if the file exists
    if not os.path.exists(file_path):
        st.error(f"❌ CSV file not found: {file_path}")
    else:
        # Load the filtered data
        df = load_data(file_path, from_date, to_date)

        if df.empty:
            st.warning("⚠️ No data found in the selected date range.")
        else:
            # Apply the strategy to the data
            trades_df, total_profit, win_rate = apply_strategy(
                df,
                ema_period=ema_period,
                rsi_period=rsi_period,
                supertrend_period=supertrend_period,
                supertrend_multiplier=supertrend_multiplier
            )
 
            # Show the raw filtered data
            st.subheader("📋 Filtered OHLCV Data")
            st.dataframe(df.head())  # Display the first 5 rows

            # Show the trades executed
            st.subheader("📊 Trades Executed")
            if not trades_df.empty:
                st.dataframe(trades_df)  # Show the trades DataFrame
            else:
                st.warning("⚠️ No trades were executed based on the strategy.")

            # Display the profit and win rate summary
            st.markdown(f"💰 **Total Profit:** ₹{total_profit:.2f}")
            st.markdown(f"✅ **Win Rate:** {win_rate:.2f}%")
