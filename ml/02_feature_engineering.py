import pandas as pd
import numpy as np
import os

# =====================================================
# CONFIG
# =====================================================
DATA_PATH = "processed/daily_clean_strict.parquet"
OUTPUT_PATH = "ml/dataset_features.parquet"

os.makedirs("ml", exist_ok=True)

# =====================================================
# LOAD
# =====================================================
df = pd.read_parquet(DATA_PATH)

required_cols = [
    "Symbol","Tanggal","Open","High","Low",
    "Close","Volume","Support","Resistance","Bandar"
]

missing = [c for c in required_cols if c not in df.columns]
if missing:
    raise ValueError(f"Kolom wajib tidak ada: {missing}")

df["Tanggal"] = pd.to_datetime(df["Tanggal"])
df = df.sort_values(["Symbol","Tanggal"]).reset_index(drop=True)

grp = df.groupby("Symbol", group_keys=False)

# =====================================================
# RETURNS
# =====================================================
df["RET_1D"] = grp["Close"].pct_change()
df["RET_5D"] = grp["Close"].pct_change(5)
df["RET_20D"] = grp["Close"].pct_change(20)
df["LOG_RET"] = grp["Close"].transform(lambda x: np.log(x).diff())

# =====================================================
# VOLATILITY
# =====================================================
df["VOL_20"] = grp["RET_1D"].transform(lambda x: x.rolling(20).std())
df["VOL_60"] = grp["RET_1D"].transform(lambda x: x.rolling(60).std())
df["VOL_REGIME"] = df["VOL_20"] / (df["VOL_60"] + 1e-9)

# =====================================================
# EMA RELATIVE
# =====================================================
for span in [10,20,50]:
    ema = grp["Close"].transform(lambda x: x.ewm(span=span, adjust=False).mean())
    df[f"EMA{span}_RATIO"] = (df["Close"] - ema) / df["Close"]

df["EMA_SPREAD"] = df["EMA10_RATIO"] - df["EMA50_RATIO"]

# =====================================================
# RSI
# =====================================================
def compute_rsi(series, period=14):
    delta = series.diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)
    avg_gain = gain.rolling(period).mean()
    avg_loss = loss.rolling(period).mean()
    rs = avg_gain / (avg_loss + 1e-9)
    return 100 - (100 / (1 + rs))

df["RSI14"] = grp["Close"].transform(compute_rsi)
df["RSI_NORM"] = (df["RSI14"] - 50) / 50

# =====================================================
# ATR
# =====================================================
prev_close = grp["Close"].shift(1)

tr1 = df["High"] - df["Low"]
tr2 = (df["High"] - prev_close).abs()
tr3 = (df["Low"] - prev_close).abs()

df["TR"] = pd.concat([tr1,tr2,tr3],axis=1).max(axis=1)
df["ATR14"] = grp["TR"].transform(lambda x: x.rolling(14).mean())
df["ATR_RATIO"] = df["ATR14"] / df["Close"]

df.drop(columns=["TR"], inplace=True)

# =====================================================
# VOLUME
# =====================================================
df["VOL_MED20"] = grp["Volume"].transform(lambda x: x.rolling(20).median())
df["VOL_RATIO"] = df["Volume"] / (df["VOL_MED20"] + 1e-9)
df["VOL_MOM"] = grp["Volume"].pct_change(5)

# =====================================================
# BREAKOUT
# =====================================================
df["HIGH_20"] = grp["High"].transform(lambda x: x.rolling(20).max())
df["LOW_20"] = grp["Low"].transform(lambda x: x.rolling(20).min())

df["BREAKOUT_UP"] = (df["Close"] - df["HIGH_20"].shift(1)) / df["Close"]
df["BREAKOUT_DOWN"] = (df["LOW_20"].shift(1) - df["Close"]) / df["Close"]

# =====================================================
# SUPPORT / RESISTANCE SAFE
# =====================================================
df["Support_LAG"] = grp["Support"].shift(1)
df["Resistance_LAG"] = grp["Resistance"].shift(1)

df["DIST_SUPPORT"] = (df["Close"] - df["Support_LAG"]) / df["Close"]
df["DIST_RESISTANCE"] = (df["Resistance_LAG"] - df["Close"]) / df["Close"]

# =====================================================
# BANDAR
# =====================================================
df["BANDAR_ENC"] = df["Bandar"].map({
    "AKUMULASI": 1,
    "NETRAL": 0,
    "DISTRIBUSI": -1
}).fillna(0)

# =====================================================
# CLEAN (NO AGGRESSIVE DROP)
# =====================================================
df = df.replace([np.inf,-np.inf], np.nan)

feature_cols = [
    # IDENTIFIER
    "Symbol","Tanggal",

    # RAW PRICE (WAJIB UNTUK LABEL)
    "Close","Volume",

    # RETURNS
    "RET_1D","RET_5D","RET_20D","LOG_RET",

    # VOLATILITY
    "VOL_20","VOL_REGIME",

    # TREND
    "EMA10_RATIO","EMA20_RATIO","EMA50_RATIO","EMA_SPREAD",

    # OSCILLATOR
    "RSI_NORM",

    # VOL
    "ATR_RATIO",

    # FLOW
    "VOL_RATIO","VOL_MOM",

    # STRUCTURE
    "BREAKOUT_UP","BREAKOUT_DOWN",
    "DIST_SUPPORT","DIST_RESISTANCE",

    # SMART MONEY
    "BANDAR_ENC"
]

df_feat = df[feature_cols].copy()

# Jangan drop semua NA → hanya drop baris tanpa Close
df_feat = df_feat[df_feat["Close"].notna()]

df_feat.to_parquet(OUTPUT_PATH, index=False)

print("✅ FEATURE ENGINEERING PRO SELESAI")
print("📦 Output :", OUTPUT_PATH)
print("📊 Rows :", f"{len(df_feat):,}")
print("📈 Saham :", df_feat["Symbol"].nunique())
print("🧠 Feature count :", len(feature_cols)-2)
