import pandas as pd
import numpy as np
import os

# ============================================================
# CONFIG
# ============================================================

INITIAL_CAPITAL = 100_000_000   # 100 juta
RISK_PER_TRADE = 0.02           # 2% per trade
TP_PCT = 0.07                   # TP 7%
SL_PCT = 0.05                   # SL 5%
HOLDING_DAYS = 10

DATA_PATH = "processed/daily_clean.parquet"
ML_DAILY_PATH = "processed/ml_confidence_label_daily.parquet"
ML_WEEKLY_PATH = "processed/ml_confidence_label_weekly.parquet"
ML_MONTHLY_PATH = "processed/ml_confidence_label_monthly.parquet"

# ============================================================
# UTIL
# ============================================================

def merge_ml(df, path, col):
    if not os.path.exists(path):
        df[col] = np.nan
        return df

    ml = pd.read_parquet(path)
    ml["Tanggal Perdagangan Terakhir"] = pd.to_datetime(
        ml["Tanggal Perdagangan Terakhir"]
    )

    return df.merge(
        ml,
        on=["Symbol", "Tanggal Perdagangan Terakhir"],
        how="left"
    )

# ============================================================
# SIMPLE DAILY STRATEGY (INLINE, BIAR 1 FILE)
# ============================================================

def compute_ema(series, span):
    return series.ewm(span=span, adjust=False).mean()

def compute_rsi(series, period=14):
    delta = series.diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)
    avg_gain = gain.rolling(period).mean()
    avg_loss = loss.rolling(period).mean()
    rs = avg_gain / avg_loss
    return 100 - (100 / (1 + rs))

def strategy_daily(df):
    rows = []

    for symbol in df["Symbol"].unique():
        d = (
            df[df["Symbol"] == symbol]
            .sort_values("Tanggal Perdagangan Terakhir")
            .tail(30)
        )

        if len(d) < 15:
            continue

        d = d.copy()
        d["EMA10"] = compute_ema(d["Close"], 10)
        d["EMA20"] = compute_ema(d["Close"], 20)
        d["RSI"] = compute_rsi(d["Close"])
        d["VOL_MED20"] = d["Volume"].rolling(20).median()

        latest = d.iloc[-1]

        trend_ok = latest["EMA10"] > latest["EMA20"]
        momentum_ok = 45 <= latest["RSI"] <= 70
        volume_ok = latest["Volume"] > latest["VOL_MED20"]

        score = trend_ok * 40 + momentum_ok * 30 + volume_ok * 30

        # ===== ML FILTER =====
        ml_d = latest.get("ml_confidence_label_daily", np.nan)
        ml_w = latest.get("ml_confidence_label_weekly", np.nan)
        ml_m = latest.get("ml_confidence_label_monthly", np.nan)

        ml_ok = (
            (not pd.isna(ml_d) and ml_d >= 0.60) or
            (not pd.isna(ml_w) and ml_w >= 0.60) or
            (not pd.isna(ml_m) and ml_m >= 0.65)
        )

        if score >= 60 and ml_ok:
            rows.append({
                "Symbol": symbol,
                "Signal_Date": latest["Tanggal Perdagangan Terakhir"]
            })

    return pd.DataFrame(rows)

# ============================================================
# EQUITY CURVE BACKTEST
# ============================================================

def backtest_equity_curve(df_price, df_signal):
    capital = INITIAL_CAPITAL
    equity_curve = []
    trade_log = []

    for row in df_signal.itertuples():
        symbol = row.Symbol

        d = (
            df_price[df_price["Symbol"] == symbol]
            .sort_values("Tanggal Perdagangan Terakhir")
            .reset_index(drop=True)
        )

        if len(d) < HOLDING_DAYS + 1:
            continue

        entry_price = d.iloc[-HOLDING_DAYS - 1]["Close"]
        future = d.tail(HOLDING_DAYS)

        tp = entry_price * (1 + TP_PCT)
        sl = entry_price * (1 - SL_PCT)

        hit_tp = future["High"].max() >= tp
        hit_sl = future["Low"].min() <= sl

        risk_amount = capital * RISK_PER_TRADE
        position_size = risk_amount / SL_PCT

        pnl = 0
        result = "LOSS"

        if hit_tp and not hit_sl:
            pnl = position_size * TP_PCT
            result = "WIN"
        else:
            pnl = -risk_amount

        capital += pnl
        equity_curve.append(capital)

        trade_log.append({
            "Symbol": symbol,
            "Result": result,
            "PNL": round(pnl, 0),
            "Equity": round(capital, 0)
        })

    return {
        "final_equity": round(capital, 0),
        "return_pct": round((capital / INITIAL_CAPITAL - 1) * 100, 2),
        "equity_curve": pd.Series(equity_curve),
        "trade_log": pd.DataFrame(trade_log)
    }

# ============================================================
# RUNNER
# ============================================================

if __name__ == "__main__":

    print("🚀 RUNNING ML EQUITY CURVE BACKTEST")

    df_price = pd.read_parquet(DATA_PATH)
    df_price["Tanggal Perdagangan Terakhir"] = pd.to_datetime(
        df_price["Tanggal Perdagangan Terakhir"]
    )

    # MERGE ML
    df_price = merge_ml(df_price, ML_DAILY_PATH, "ml_confidence_label_daily")
    df_price = merge_ml(df_price, ML_WEEKLY_PATH, "ml_confidence_label_weekly")
    df_price = merge_ml(df_price, ML_MONTHLY_PATH, "ml_confidence_label_monthly")

    # SIGNAL
    df_signal = strategy_daily(df_price)

    print("Total Signal:", len(df_signal))

    if df_signal.empty:
        print("❌ NO SIGNAL")
        exit()

    result = backtest_equity_curve(df_price, df_signal)

    print("\n===== RESULT =====")
    print("Modal Awal :", INITIAL_CAPITAL)
    print("Final Equity :", result["final_equity"])
    print("Return (%) :", result["return_pct"])
    print("Total Trade :", len(result["trade_log"]))

    print("\nSample Trade:")
    print(result["trade_log"].head())
