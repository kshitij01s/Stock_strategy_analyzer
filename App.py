import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), "Stock_Strategy_Analyzer"))

from strategy import apply_strategy
from utils import load_csv, get_stock_list
from indicators import compute_indicators
import pandas as pd

import altair as alt
import sys
import os
from datetime import datetime

# Add parent directory to path for imports
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from utils import load_csv, get_stock_list
from strategy import apply_strategy


USE_STREAMLIT = True  # Change to False to run Flask app
# Load CSV file from Stock_data/ folder
def load_data(stock, timeframe):
    file_path = f"Stock_data/NSE_{stock}_{timeframe}.csv"
    if not os.path.exists(file_path):
        st.error(f"CSV file not found: {file_path}")
        return pd.DataFrame()
    return pd.read_csv(file_path)


if USE_STREAMLIT:
    import streamlit as st

    # --- Streamlit Config ---
    st.set_page_config(page_title="📊 Stock Strategy Analyzer", layout="wide")

    DATA_FOLDER = "stock_data"

    # --- Check stock data folder ---
    if not os.path.exists(DATA_FOLDER):
        st.error("❌ 'stock_data' folder not found. Make sure it exists next to app.py.")
        st.stop()
        
    # --- Sidebar Inputs ---
    st.sidebar.header("📁 User Input")
    stock_list = get_stock_list(DATA_FOLDER)
    st.sidebar.header("Indicator Settings")
    ema_period = st.sidebar.number_input("EMA Period", min_value=1, max_value=100, value=20)
    rsi_period = st.sidebar.number_input("RSI Period", min_value=1, max_value=100, value=14)
    supertrend_period = st.sidebar.number_input("Supertrend Period", min_value=1, max_value=100, value=7)
    supertrend_multiplier = st.sidebar.number_input("Supertrend Multiplier", min_value=0.5, max_value=10.0, value=3.0)

    st.sidebar.header("⚙️ Strategy Rules")

    st.sidebar.markdown("### 📥 Buy Entry Conditions")
    use_ema_buy = st.sidebar.checkbox("Close > EMA", value=True)
    use_rsi_buy = st.sidebar.checkbox("RSI < X", value=True)
    rsi_buy_threshold = st.sidebar.slider("RSI Buy Threshold", 10, 50, 30)
    use_supertrend_buy = st.sidebar.checkbox("Supertrend = Buy", value=False)

    st.sidebar.markdown("### 📤 Sell Exit Conditions")
    use_ema_sell = st.sidebar.checkbox("Close < EMA", value=True)
    use_rsi_sell = st.sidebar.checkbox("RSI > Y", value=True)
    rsi_sell_threshold = st.sidebar.slider("RSI Sell Threshold", 50, 90, 60)
    use_supertrend_sell = st.sidebar.checkbox("Supertrend = Sell", value=False)

# --- Strategy Rules ---
    st.sidebar.subheader("📌 Strategy Rules")

    strategy_rules = {
        "buy": {
            "ema": st.sidebar.checkbox("Use EMA for Buy", value=True),
            "rsi": st.sidebar.checkbox("Use RSI for Buy", value=True),
            "rsi_threshold": st.sidebar.slider("Buy RSI Threshold", 1, 50, 30),
            "supertrend": st.sidebar.checkbox("Use Supertrend for Buy", value=True)
        },
        "sell": {
            "ema": st.sidebar.checkbox("Use EMA for Sell", value=True),
            "rsi": st.sidebar.checkbox("Use RSI for Sell", value=True),
            "rsi_threshold": st.sidebar.slider("Sell RSI Threshold", 50, 100, 60),
            "supertrend": st.sidebar.checkbox("Use Supertrend for Sell", value=True)
        }
    }

    if not stock_list:
        st.sidebar.error("No stock CSV files found.")
        st.stop()

    stock = st.sidebar.selectbox("📈 Choose a Stock", stock_list)
    timeframe = st.sidebar.selectbox("⏱️ Select Timeframe", ["1", "5", "15", "30", "60", "D"])
    from_date = st.sidebar.date_input("📅 From Date")
    to_date = st.sidebar.date_input("📅 To Date")
    run_btn = st.sidebar.button("▶ Run Analysis")

    # --- Main Title ---
    st.title("📊 Stock Strategy Analyzer")

    # --- Run Analysis ---
    if run_btn:
        filename = os.path.join(DATA_FOLDER, f"NSE_{stock}_{timeframe}.csv")
        if not os.path.exists(filename):
            st.error(f"❌ File not found: `{filename}`")
            st.stop()

        df = load_csv(filename, from_date, to_date)
        if df is None or df.empty:
            st.warning("⚠️ No data returned. Check the file or date range.")
            st.stop()
            df = compute_indicators(df, ema_length=ema_period, rsi_length=rsi_period,
                        st_length=supertrend_period, st_multiplier=supertrend_multiplier)
        else:
            st.success("✅ Data loaded successfully.")
        
        df = compute_indicators(df, ema_length=ema_period, rsi_length=rsi_period,
                        st_length=supertrend_period, st_multiplier=supertrend_multiplier)

        st.write("Columns in data:", df.columns.tolist())
        df.columns = [col.strip().lower() for col in df.columns]
        print(df.columns)  # Should include 'ema20' and 'rsi14'
        print(df[['ema20', 'rsi14']].tail())


        with st.spinner("⏳ Running Strategy..."):
            trades_df, total_profit, win_rate = apply_strategy(df, strategy_rules)

            
            st.write("🧠 Available indicators:", df.columns.tolist())


        st.success("✅ Analysis Completed")
        # --- Show Raw Data ---
        # --- Optional: Show Raw CSV Data ---
        if st.checkbox("Show raw data"):
            if df is not None and not df.empty:
                st.subheader("📄 Raw CSV Data")
                st.dataframe(df.head(100))  # or st.write(df)
            else:
                st.warning("Data not loaded or empty.")


# Apply strategy (MUST return a DataFrame)
        trades_df, total_profit, win_rate = apply_strategy(df, strategy_rules)



        # --- Results ---
        st.subheader("📋 Trade Summary")
        if not trades_df.empty:
            st.subheader("📋 Trade Summary")
            st.dataframe(trades_df)
            st.metric("💰 Total Profit", f"₹{total_profit:.2f}")
            st.metric("🏆 Win Rate", f"{win_rate:.2f}%")
            total_profit = trades_df["P/L"].sum()
            win_rate = (trades_df["P/L"] > 0).mean() * 100

            st.write(f"💰 Total Profit: `{total_profit:.2f}`")
            st.write(f"🎯 Win Rate: `{win_rate:.2f}%`")
           
            import matplotlib.pyplot as plt
            # Suppose this is how you get your trades DataFrame:
           

            # Then check before using it
            if trades_df is not None and not trades_df.empty:
                st.write(trades_df)
            else:
                st.write("No trades found.")

            st.subheader("📈 Equity Curve")

            equity = trades_df["P/L"].cumsum()
            fig, ax = plt.subplots()
            ax.plot(equity, label="Equity Curve", color="green")
            ax.set_title("Equity Growth Over Time")
            ax.set_xlabel("Trade #")
            ax.set_ylabel("Cumulative Profit")
            ax.legend()
            ax.grid(True)

            st.pyplot(fig)
        else:
            st.info("No trades found for the selected strategy conditions.")
            
        # --- Chart ---
        st.subheader("📈 Closing Price Chart")
        st.write("Current columns:", df.columns.tolist())
        st.line_chart(df.set_index("time")[["close", "ema20", "rsi14"]])

        # 🧠 Optional: Detailed Price + EMA + Supertrend Chart
      
            # 📈 Equity Curve Plot (Optional)
        
        # Choose correct EMA column name
        ema_col = f"ema{ema_period}"

        base = alt.Chart(df.reset_index()).encode(x='time:T')

        price_line = base.mark_line(color='blue').encode(
            y='close:Q',
            tooltip=['time:T', 'close:Q']
        ).properties(title="Price with EMA & Supertrend")

        ema_line = base.mark_line(color='orange').encode(
            y=ema_col + ':Q'
        )

        # Optional: add Supertrend line if available
        supertrend_cols = [col for col in df.columns if col.lower().startswith("supertl")]
        if supertrend_cols:
            st_col = supertrend_cols[0]
            supertrend_line = base.mark_line(color='green').encode(
                y=st_col + ':Q'
            )
            chart = price_line + ema_line + supertrend_line
        else:
            chart = price_line + ema_line

        st.altair_chart(chart.interactive(), use_container_width=True)

        st.write("📅 Data range available:", df['time'].min(), "→", df['time'].max())
        st.subheader("📈 Price + EMA + Supertrend")
        columns_to_plot = ["close", "ema20"]

# Detect and add Supertrend line dynamically
        for col in df.columns:
            if "supertrend" in col.lower() and not col.lower().endswith("d"):  # Exclude direction column
                columns_to_plot.append(col)

                st.line_chart(df.set_index("time")[columns_to_plot])

                st.subheader("📊 RSI Indicator")
                st.line_chart(df.set_index("time")[["rsi14"]])



else:
    from flask import Flask, render_template, request

    app = Flask(__name__)
    DATA_FOLDER = "stock_data"

    @app.route("/", methods=["GET", "POST"])
    def index():
        stock_list = get_stock_list(DATA_FOLDER)
        results = None
        error = None

        if request.method == "POST":
            stock = request.form.get("stock")
            timeframe = request.form.get("timeframe")
            from_date = request.form.get("from_date")
            to_date = request.form.get("to_date")

            filename = f"NSE_{stock}_{timeframe}.csv"
            filepath = os.path.join(DATA_FOLDER, filename)

            if not os.path.exists(filepath):
                error = f"File {filename} not found!"
                return render_template("index.html", stock_list=stock_list, error=error)

            df = load_csv(filepath, from_date, to_date)
            trades, profit, win_rate = apply_strategy(df)

            return render_template("results.html", trades=trades.to_dict(orient="records"),
                                   profit=profit, win_rate=win_rate)

        return render_template("index.html", stock_list=stock_list, error=error)

    if __name__ == "__main__":
        app.run(debug=True)

