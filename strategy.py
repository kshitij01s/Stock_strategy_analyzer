import pandas as pd
import pandas_ta as ta
import sys
import io
import os 
# Ensure UTF-8 output for emojis in some terminals
if sys.stdout.encoding != 'utf-8':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

import pandas as pd
import streamlit as st
import pandas as pd
df = pd.read_csv("stock_data/NSE_RELIANCE_1.csv")
print(df.columns)

def load_data(filepath, from_date, to_date):
    # Read CSV and parse 'time' column
    df = pd.read_csv(filepath, parse_dates=['time'])
    df.columns = df.columns.str.strip().str.lower()


    # Convert 'time' column to timezone-aware datetime
    df['time'] = pd.to_datetime(df['time'])
    df.set_index('time', inplace=True)
    
    if df.index.tz is None:
        df.index = df.index.tz_localize('UTC')
    tz = df.index.tz

    # Convert from_date and to_date to timezone-aware datetimes
    from_dt = pd.to_datetime(from_date).tz_localize(tz)
    to_dt = pd.to_datetime(to_date).tz_localize(tz) + pd.Timedelta(days=1) - pd.Timedelta(seconds=1)
    
    # Filter data
    filtered_df = df.loc[from_dt:to_dt]
    return filtered_df


# Streamlit app snippet
def main():
    st.title("Stock Data Viewer")
    filepath = "stock_data/NSE_RELIANCE_1.csv"
    
    from_date = st.date_input("From Date")
    to_date = st.date_input("To Date")
    
    if from_date and to_date and from_date <= to_date:
        data = load_data(filepath, from_date, to_date)
        if data.empty:
            st.warning("⚠️ No data returned. Check the file or date range.")
        else:
            st.dataframe(data)
    else:
        st.warning("Please select a valid date range.")

if __name__ == "__main__":
    main()


def apply_strategy(df,strategy_rules, ema_period=20, rsi_period=14, supertrend_period=10, supertrend_multiplier=3.0):
    """
    Applies the trading strategy to the DataFrame with columns:
    'Time', 'Open', 'High', 'Low', 'Close'

    Indicators used:
    - EMA(20)
    - RSI(14)
    - Supertrend (length=10, multiplier=3.0)

    Entry Condition:
    - Close > EMA
    - RSI < 30
    - Supertrend == 1

    Exit Condition:
    - RSI > 60 OR
    - Close < EMA OR
    - Supertrend == -1

    Returns:
        trades_df (pd.DataFrame): DataFrame of trades with Entry/Exit info and P/L
        total_profit (float): sum of all trade profits
        win_rate (float): percentage of profitable trades
    """
    df = df.copy()
    df.columns = [col.lower() for col in df.columns]
  # Standardize columns

    df['ema'] = ta.ema(df['close'], length=20)
    df['rsi'] = ta.rsi(df['close'], length=14)
    supertrend = ta.supertrend(df['high'], df['low'], df['close'], length=10, multiplier=3.0)

    
    
    # Compute indicators
    df['ema'] = ta.ema(df['close'], length=ema_period)
    df['rsi'] = ta.rsi(df['close'], length=rsi_period)
    
    # Supertrend
    st_df = ta.supertrend(
    high=df['high'],
    low=df['low'],
    close=df['close'],
    length=supertrend_period,
    multiplier=supertrend_multiplier
)
    df = df.join(st_df)

# ✅ Correct:
    signal_cols = [col for col in df.columns if "SUPERTd" in col or "supertrend" in col.lower()]

    if not signal_cols:
        raise KeyError("Supertrend signal column not found.")
    elif supertrend is not None and 'SUPERTd_10_3.0' in supertrend.columns:
        df['Supertrend'] = supertrend['SUPERTd_10_3.0']
    else:
        df['Supertrend'] = 0  # fallback if supertrend fails

    
    df['supertrend_signal'] = df[signal_cols[0]]

    # Trade logic
    trades = []
    in_trade = False
    entry_price = None
    entry_time = None

    for i in range(1, len(df)):
        row = df.iloc[i]

        if not in_trade:
            buy_conditions = []

            if strategy_rules["buy"].get("ema", False):
                buy_conditions.append(row['close'] > row['ema'])

            if strategy_rules["buy"].get("rsi", False):
                buy_conditions.append(row['rsi'] < strategy_rules["buy"].get("rsi_threshold", 30))

            if strategy_rules["buy"].get("supertrend", False):
                buy_conditions.append(row['supertrend_signal'] == 1)

            if buy_conditions and all(buy_conditions):
                entry_price = row['close']
                entry_time = row.name
                in_trade = True

        else:
            sell_conditions = []

            if strategy_rules["sell"].get("ema", False):
                sell_conditions.append(row['close'] < row['ema'])

            if strategy_rules["sell"].get("rsi", False):
                sell_conditions.append(row['rsi'] > strategy_rules["sell"].get("rsi_threshold", 60))

            if strategy_rules["sell"].get("supertrend", False):
                sell_conditions.append(row['supertrend_signal'] == -1)

            if sell_conditions and any(sell_conditions):
                exit_price = row['close']
                exit_time = row.name
                profit = exit_price - entry_price
                trades.append({
                    "Entry Time": entry_time,
                    "Exit Time": exit_time,
                    "Entry Price": entry_price,
                    "Exit Price": exit_price,
                    "P/L": round(profit, 2)
                })
                in_trade = False


    
    trades_df = pd.DataFrame(trades)
    total_profit = trades_df["P/L"].sum() if not trades_df.empty else 0.0
    win_rate = (trades_df["P/L"] > 0).mean() * 100 if not trades_df.empty else 0.0

    return trades_df, total_profit, win_rate




def main():
    st.title("📈 Stock Strategy Analyzer")
    filepath = st.text_input("CSV filepath:", "stock_data/NSE_RELIANCE_1.csv")
    from_date = st.date_input("From date")
    to_date = st.date_input("To date")

    if st.button("Run Analysis"):
        if not os.path.exists(filepath):
            st.error(f"❌ File not found: {filepath}")
            return

        df = load_data(filepath, from_date, to_date)
        if df.empty:
            st.warning("⚠️ No data for the selected range.")
            return

        try:
            trades_df, total_profit, win_rate = apply_strategy(df)
        except KeyError as e:
            st.error(e)
            return

        st.subheader("📊 Trades Executed")
        st.dataframe(trades_df)
        st.markdown(f"**Total Profit:** ₹{total_profit:.2f}")
        st.markdown(f"**Win Rate:** {win_rate:.2f}%")

if __name__ == "__main__":
    main()
print("Columns after indicators:\n", df.columns.tolist())
print("Sample rows:\n", df.head(3))

# Optional: quick test if run standalone
if __name__ == "__main__":
    import os

    test_file = os.path.join("stock_data", "NSE_RELIANCE_5.csv")

    if os.path.exists(test_file):
        df = pd.read_csv(test_file)
        df.columns = df.columns.str.capitalize()
        print("Columns in df:", df.columns.tolist())
        df.columns = [col.strip().lower() for col in df.columns]
        df['time'] = pd.to_datetime(df['time'])



        trades_df, total_profit, win_rate = apply_strategy(df)

        print("\n📊 Trades:")
        print(trades_df)

        print(f"\n💰 Total Profit: ₹{total_profit}")
        print(f"✅ Win Rate: {win_rate:.2f}%")
    else:
        print(f"❌ ERROR: Test CSV file not found: {test_file}")