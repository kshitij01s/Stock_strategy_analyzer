import tkinter as tk
from tkinter import ttk, messagebox
from tkcalendar import DateEntry
from datetime import datetime
from indicators import load_data, compute_indicators
from strategy import generate_trades, compute_stats
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

def run_analysis():
    stock = stock_var.get().strip().upper()
    timeframe = tf_var.get().strip()
    start = cal_from.get_date()
    end = cal_to.get_date()
    start_str = start.strftime("%Y-%m-%d")
    end_str = end.strftime("%Y-%m-%d")

    try:
        df = load_data(stock, timeframe, start_str, end_str)
    except FileNotFoundError:
        messagebox.showerror("Error", f"File not found: NSE_{stock}_{timeframe}.csv")
        return
    if df.empty:
        messagebox.showwarning("No Data", "No data in selected date range.")
        return

    df = compute_indicators(df)
    trades = generate_trades(df)
    total_pl, win_rate = compute_stats(trades)

    # Display stats
    result_var.set(f"Total P/L: ₹{total_pl:.2f}     Win Rate: {win_rate:.2f}%")

    # Display trade table
    for i in tree.get_children():
        tree.delete(i)
    for _, row in trades.iterrows():
        tree.insert("", "end", values=(
            row["entry_time"].strftime("%Y-%m-%d %H:%M"),
            row["exit_time"].strftime("%Y-%m-%d %H:%M"),
            f"{row['entry_price']:.2f}",
            f"{row['exit_price']:.2f}",
            f"{row['P/L']:.2f}"
        ))

    # Plot equity curve (cumulative P/L)
    fig.clear()
    ax = fig.add_subplot(111)
    df_tr = trades.copy()
    df_tr["cum_pl"] = df_tr["exit_price"] - df_tr["entry_price"]
    df_tr["cum_pl"].cumsum().plot(ax=ax, marker='o', title="Equity Curve")
    canvas.draw()

# Main window
root = tk.Tk()
root.title("Stock Strategy Analyzer")

frame = ttk.Frame(root, padding=10)
frame.grid(row=0, column=0, sticky="NSEW")

# Inputs
stock_var = tk.StringVar()
tf_var = tk.StringVar()
ttk.Label(frame, text="Stock:").grid(row=0, column=0)
ttk.Entry(frame, textvariable=stock_var).grid(row=0, column=1)
ttk.Label(frame, text="Timeframe (min):").grid(row=0, column=2)
ttk.Entry(frame, textvariable=tf_var).grid(row=0, column=3)

ttk.Label(frame, text="From:").grid(row=1, column=0)
cal_from = DateEntry(frame, date_pattern="yyyy-mm-dd")
cal_from.grid(row=1, column=1)
ttk.Label(frame, text="To:").grid(row=1, column=2)
cal_to = DateEntry(frame, date_pattern="yyyy-mm-dd")
cal_to.grid(row=1, column=3)

ttk.Button(frame, text="Run Analysis", command=run_analysis).grid(row=2, column=0, columnspan=4, pady=5)

result_var = tk.StringVar()
ttk.Label(frame, textvariable=result_var).grid(row=3, column=0, columnspan=4)

# Trade table
cols = ("Entry", "Exit", "Entry Price", "Exit Price", "P/L")
tree = ttk.Treeview(frame, columns=cols, show="headings", height=10)
for c in cols:
    tree.heading(c, text=c)
tree.grid(row=4, column=0, columnspan=4, pady=5)

# Equity plot
fig = plt.Figure(figsize=(6,3))
canvas = FigureCanvasTkAgg(fig, master=frame)
canvas.get_tk_widget().grid(row=5, column=0, columnspan=4)

root.mainloop()
