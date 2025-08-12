import os
import pandas as pd
from datetime import timedelta

def get_stock_list(data_folder):
    """
    Scan the folder for CSV files named like 'NSE_<STOCK>_<TIMEFRAME>.csv'
    Return a sorted list of unique stock names.
    """
    if not os.path.exists(data_folder):
        print(f"[ERROR] Folder not found: {data_folder}")
        return []

    stock_files = [f for f in os.listdir(data_folder) if f.endswith(".csv") and f.startswith("NSE_")]
    stock_names = set()

    for file in stock_files:
        parts = file.replace(".csv", "").split("_")
        if len(parts) >= 3:
            stock_names.add(parts[1])  # Stock name is the 2nd part

    return sorted(stock_names)


def load_csv(filepath, from_date, to_date):
    import pytz
    try:
        df = pd.read_csv(filepath, parse_dates=["time"])

        datetime_col = None
        for col in ['Time', 'Datetime', 'Date', 'Timestamp', 'time']:
            if col in df.columns:
                datetime_col = col
                break

        if datetime_col is None:
            raise ValueError("No valid datetime column found in CSV.")

        df['time'] = pd.to_datetime(df[datetime_col])

        # Get timezone info from the 'time' column
        tz = df['time'].dt.tz

        # Convert from_date and to_date to datetime and add timezone info
        start = pd.to_datetime(from_date)
        end = pd.to_datetime(to_date) + timedelta(days=1) - timedelta(seconds=1)

        # Make start and end timezone-aware if tz exists
        if tz is not None:
            start = start.tz_localize(tz)
            end = end.tz_localize(tz)

        # Filter rows based on date range
        df = df[(df["time"] >= start) & (df["time"] <= end)]

        print("Earliest time in file:", df['time'].min())
        print("Latest time in file:", df['time'].max())
        print("Filtering from", start, "to", end)

        return df.reset_index(drop=True)

    except Exception as e:
        print(f"[ERROR] load_csv: {e}")
        return None


