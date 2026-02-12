import pandas as pd
import numpy as np
import joblib

# ==========================================================
# CONFIG
# ==========================================================
CAPITAL = 100_000_000
RISK_PER_TRADE = 0.01
MAX_POSITIONS = 5

FEE = 0.001
SLIPPAGE = 0.001
LIQ_LIMIT = 0.1

CONF_D = "processed/ml_confidence_label_daily.parquet"
CONF_W = "processed/ml_confidence_label_weekly.parquet"
CONF_M = "processed/ml_confidence_label_monthly.parquet"

PRICE_PATH = "processed/daily_clean_strict.parquet"
FEATURE_PATH = "ml/dataset_features.parquet"

MODEL_D = "ml/models/label_daily.pkl"
MODEL_W = "ml/models/label_weekly.pkl"
MODEL_M = "ml/models/label_monthly.pkl"

# ==========================================================
# LOAD DATA
# ==========================================================
df_d = pd.read_parquet(CONF_D)
df_w = pd.read_parquet(CONF_W)
df_m = pd.read_parquet(CONF_M)
df_price = pd.read_parquet(PRICE_PATH)
df_feat = pd.read_parquet(FEATURE_PATH)

for df in [df_d, df_w, df_m, df_price, df_feat]:
    df["Tanggal"] = pd.to_datetime(df["Tanggal"])

df = df_d.merge(df_w, on=["Symbol","Tanggal"]) \
         .merge(df_m, on=["Symbol","Tanggal"]) \
         .merge(df_price[["Symbol","Tanggal","Close","Volume"]], on=["Symbol","Tanggal"]) \
         .merge(df_feat[["Symbol","Tanggal","ATR_RATIO","VOL_REGIME"]], on=["Symbol","Tanggal"])

df = df.sort_values(["Symbol","Tanggal"])

df["RET_1D"]  = df.groupby("Symbol")["Close"].shift(-1)/df["Close"] - 1
df["RET_5D"]  = df.groupby("Symbol")["Close"].shift(-5)/df["Close"] - 1
df["RET_20D"] = df.groupby("Symbol")["Close"].shift(-20)/df["Close"] - 1

df = df.dropna()

# ==========================================================
# LOAD THRESHOLDS
# ==========================================================
th_d = joblib.load(MODEL_D)["threshold"]
th_w = joblib.load(MODEL_W)["threshold"]
th_m = joblib.load(MODEL_M)["threshold"]

# ==========================================================
# BACKTEST
# ==========================================================
equity = CAPITAL
equity_curve = []
trade_log = []

dates = sorted(df["Tanggal"].unique())

for date in dates:

    day = df[df["Tanggal"] == date]

    # ==============================
    # AUTO REGIME
    # ==============================
    if day["VOL_REGIME"].mean() > 1.5:
        strategy = "DAILY"
    elif day["ml_confidence_label_monthly"].mean() > 0.8:
        strategy = "MONTHLY"
    else:
        strategy = "WEEKLY"

    if strategy == "DAILY":
        candidates = day[day["ml_confidence_label_daily"] > th_d] \
            .sort_values("ml_confidence_label_daily", ascending=False)
        holding = "RET_1D"

    elif strategy == "WEEKLY":
        candidates = day[
            (day["ml_confidence_label_weekly"] > th_w) &
            (day["ml_confidence_label_monthly"] > th_m)
        ].sort_values("ml_confidence_label_weekly", ascending=False)
        holding = "RET_5D"

    else:
        candidates = day[day["ml_confidence_label_monthly"] > th_m] \
            .sort_values("ml_confidence_label_monthly", ascending=False)
        holding = "RET_20D"

    candidates = candidates.head(MAX_POSITIONS)

    if len(candidates) == 0:
        equity_curve.append([date, equity])
        continue

    daily_return = 0

    for _, row in candidates.iterrows():

        atr = row["ATR_RATIO"]
        stop_distance = 1.5 * atr

        risk_amount = equity * RISK_PER_TRADE
        position_size = risk_amount / stop_distance
        max_liq = row["Volume"] * LIQ_LIMIT
        position_size = min(position_size, max_liq)

        weight = position_size / equity

        ret = row[holding]

        if ret < -stop_distance:
            ret = -stop_distance

        ret = ret - FEE - SLIPPAGE

        pnl = equity * weight * ret

        trade_log.append({
            "Date": date,
            "Strategy": strategy,
            "Symbol": row["Symbol"],
            "Return_%": ret*100,
            "PnL": pnl
        })

        daily_return += weight * ret

    equity *= (1 + daily_return)
    equity_curve.append([date, equity])

# ==========================================================
# RESULTS
# ==========================================================
equity_df = pd.DataFrame(equity_curve, columns=["Tanggal","Equity"])
equity_df["Return"] = equity_df["Equity"].pct_change()

trade_df = pd.DataFrame(trade_log)

total_return = equity_df["Equity"].iloc[-1] / CAPITAL - 1
ret_series = equity_df["Return"].dropna()

sharpe = (ret_series.mean()/ret_series.std()) * np.sqrt(252) if ret_series.std() != 0 else 0
max_dd = (equity_df["Equity"]/equity_df["Equity"].cummax() - 1).min()

# ==========================================================
# DETAIL ANALYSIS
# ==========================================================
strategy_summary = trade_df.groupby("Strategy").agg(
    Trades=("PnL","count"),
    Total_PnL=("PnL","sum"),
    Winrate=("Return_%", lambda x: (x>0).mean()*100)
)

symbol_summary = trade_df.groupby("Symbol").agg(
    Trades=("PnL","count"),
    Total_PnL=("PnL","sum"),
    Winrate=("Return_%", lambda x: (x>0).mean()*100)
).sort_values("Total_PnL", ascending=False)

print("\n==========================================")
print("💰 MASTER STRATEGY PRO V2")
print("==========================================")
print(f"Final Equity    : {equity:,.0f}")
print(f"Total Return    : {total_return*100:.2f}%")
print(f"Sharpe Ratio    : {sharpe:.2f}")
print(f"Max Drawdown    : {max_dd*100:.2f}%")
print("------------------------------------------")
print("Total Trades    :", len(trade_df))
print("Winrate         :", round((trade_df['Return_%']>0).mean()*100,2),"%")
print("==========================================")

print("\n📊 STRATEGY BREAKDOWN")
print(strategy_summary)

print("\n🏆 TOP 10 PROFIT SAHAM")
print(symbol_summary.head(10)["Total_PnL"])

print("\n💣 TOP 10 LOSS SAHAM")
print(symbol_summary.tail(10)["Total_PnL"])

# SAVE
equity_df.to_parquet("processed/master_equity.parquet", index=False)
trade_df.to_parquet("processed/master_trade_log.parquet", index=False)
symbol_summary.to_parquet("processed/master_symbol_summary.parquet")

print("\n📦 Files saved:")
print(" - master_equity.parquet")
print(" - master_trade_log.parquet")
print(" - master_symbol_summary.parquet")
print("==========================================")
