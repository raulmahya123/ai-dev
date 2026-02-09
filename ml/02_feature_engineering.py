import pandas as pd
import numpy as np

DATA_PATH = "processed/daily_clean.parquet"
OUTPUT_PATH = "ml/dataset_features.parquet"

# =========================
# LOAD DATA
# =========================
df = pd.read_parquet(DATA_PATH)

# Pastikan urut waktu per saham
df = df.sort_values(
    ["Kode Saham", "Tanggal Perdagangan Terakhir"]
).reset_index(drop=True)

# =========================
# HELPER FUNCTIONS
# =========================
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

# =========================
# FEATURE ENGINEERING
# =========================
features = []

for kode in df["Kode Saham"].unique():
    d = df[df["Kode Saham"] == kode].copy()

    # EMA
    d["EMA10"] = compute_ema(d["Close"], 10)
    d["EMA20"] = compute_ema(d["Close"], 20)
    d["EMA50"] = compute_ema(d["Close"], 50)

    # RSI
    d["RSI14"] = compute_rsi(d["Close"])

    # Volume ratio
    d["VOL_MED20"] = d["Volume"].rolling(20).median()
    d["VOL_RATIO"] = d["Volume"] / d["VOL_MED20"]

    # Distance to support / resistance
    d["DIST_SUPPORT"] = (d["Close"] - d["Support"]) / d["Close"]
    d["DIST_RESISTANCE"] = (d["Resistance"] - d["Close"]) / d["Close"]

    # Encode bandar
    d["BANDAR_ENC"] = d["Bandar"].map({
        "AKUMULASI": 1,
        "NETRAL": 0,
        "DISTRIBUSI": -1
    })

    features.append(d)

# Gabung semua saham
df_feat = pd.concat(features)

# =========================
# CLEANING
# =========================
df_feat = df_feat.replace([np.inf, -np.inf], np.nan)
df_feat = df_feat.dropna(subset=[
    "EMA10", "EMA20", "EMA50",
    "RSI14", "VOL_RATIO"
])

# =========================
# SAVE
# =========================
df_feat.to_parquet(OUTPUT_PATH)

print("Feature engineering selesai.")
print("Jumlah baris akhir:", len(df_feat))
print("Kolom feature:")
print(df_feat.columns)
