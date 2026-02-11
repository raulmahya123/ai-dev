import pandas as pd
import numpy as np
import os

# =====================================================
# PATH
# =====================================================
DATA_PATH = "processed/daily_clean.parquet"
OUTPUT_PATH = "ml/dataset_features.parquet"
os.makedirs("ml", exist_ok=True)

# =====================================================
# LOAD DATA
# =====================================================
df = pd.read_parquet(DATA_PATH)

# konsistensi kolom
df = df.rename(columns={
    "Symbol": "Saham",
    "Tanggal": "Tanggal"
})

df = df.sort_values(["Saham", "Tanggal"]).reset_index(drop=True)

# =====================================================
# HELPER (VECTORIZED)
# =====================================================
def compute_rsi(series, period=14):
    delta = series.diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)
    avg_gain = gain.rolling(period).mean()
    avg_loss = loss.rolling(period).mean()
    rs = avg_gain / avg_loss
    return 100 - (100 / (1 + rs))

# =====================================================
# FEATURE ENGINEERING (GROUPBY TRANSFORM)
# =====================================================
grp = df.groupby("Saham")

# === EMA ===
df["EMA10"] = grp["Close"].transform(lambda x: x.ewm(span=10, adjust=False).mean())
df["EMA20"] = grp["Close"].transform(lambda x: x.ewm(span=20, adjust=False).mean())
df["EMA50"] = grp["Close"].transform(lambda x: x.ewm(span=50, adjust=False).mean())

# === RSI ===
df["RSI14"] = grp["Close"].transform(compute_rsi)

# === VOLUME FEATURE ===
df["VOL_MED20"] = grp["Volume"].transform(lambda x: x.rolling(20).median())
df["VOL_RATIO"] = df["Volume"] / df["VOL_MED20"]

# === DISTANCE TO SR ===
df["DIST_SUPPORT"] = (df["Close"] - df["Support"]) / df["Close"]
df["DIST_RESISTANCE"] = (df["Resistance"] - df["Close"]) / df["Close"]

# === BANDAR ENCODING ===
df["BANDAR_ENC"] = df["Bandar"].map({
    "AKUMULASI": 1,
    "NETRAL": 0,
    "DISTRIBUSI": -1
})

# =====================================================
# FINAL FEATURE SET (ML-READY)
# =====================================================
FEATURE_COLS = [
    "Saham",
    "Tanggal",
    "Open", "High", "Low", "Close", "Volume",
    "EMA10", "EMA20", "EMA50",
    "RSI14",
    "VOL_RATIO",
    "DIST_SUPPORT", "DIST_RESISTANCE",
    "BANDAR_ENC"
]

df_feat = df[FEATURE_COLS].copy()

# =====================================================
# CLEANING (ANTI ML NGEGAS)
# =====================================================
df_feat = df_feat.replace([np.inf, -np.inf], np.nan)

df_feat = df_feat.dropna(subset=[
    "EMA10", "EMA20", "EMA50",
    "RSI14", "VOL_RATIO",
    "DIST_SUPPORT", "DIST_RESISTANCE"
])

# =====================================================
# SAVE
# =====================================================
df_feat.to_parquet(OUTPUT_PATH, index=False)

# =====================================================
# LOG
# =====================================================
print("✅ FEATURE ENGINEERING SELESAI")
print("📦 Output :", OUTPUT_PATH)
print("📊 Baris :", f"{len(df_feat):,}")
print("📈 Saham :", df_feat["Saham"].nunique())
print("🧠 Feature :", [c for c in df_feat.columns if c not in ["Saham", "Tanggal"]])
