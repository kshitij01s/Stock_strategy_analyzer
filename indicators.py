import pandas as pd
import pandas_ta as ta

def load_data(stock: str, timeframe: str, start: str, end: str) -> pd.DataFrame:
    path = f"stock_data/NSE_{stock}_{timeframe}.csv"
    df = pd.read_csv(path, parse_dates=["Time"])
    df = df.set_index("Time")
    df = df.loc[start:end]
    return df

def compute_indicators(df: pd.DataFrame, ema_length=20, rsi_length=14,
                       st_length=7, st_multiplier=3.0) -> pd.DataFrame:
    df.columns = [col.strip().lower() for col in df.columns]
    df["ema" + str(ema_length)] = df["close"].ewm(span=ema_length, adjust=False).mean()
    df["rsi" + str(rsi_length)] = ta.rsi(df["close"], length=rsi_length)
    st = ta.supertrend(df["high"], df["low"], df["close"],
                       length=st_length, multiplier=st_multiplier)
    df = df.join(st)
    print("✅ Indicator columns added:", df.columns.tolist())
    print(df.tail(2))  # Just show a few rows to confirm

    return df
