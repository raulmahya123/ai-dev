import pandas as pd
import numpy as np
import os

# =====================================================
# PATH
# =====================================================
DATA_PATH = "ml/dataset_features.parquet"
OUTPUT_PATH = "ml/dataset_ml_ready.parquet"
os.makedirs("ml", exist_ok=True)

# =====================================================
# LOAD DATA
# =====================================================
df = pd.read_parquet(DATA_PATH)

# konsistensi & sorting
df = df.sort_values(["Saham", "Tanggal"]).reset_index(drop=True)

# =====================================================
# GROUP
# =====================================================
grp = df.groupby("Saham")

# =====================================================
# 1️⃣ DAILY LABEL (next-day up)
# =====================================================
df["close_next"] = grp["Close"].shift(-1)

df["label_daily"] = (
    df["close_next"] > df["Close"]
).astype(int)

# =====================================================
# 2️⃣ WEEKLY LABEL (Swing ±5 hari, +5%)
# =====================================================
df["future_max_5"] = grp["Close"].shift(-1).rolling(
    window=5, min_periods=5
).max()

df["label_weekly"] = (
    df["future_max_5"] >= df["Close"] * 1.05
).astype(int)

# =====================================================
# 3️⃣ MONTHLY LABEL (Position ±20 hari, +20%)
# =====================================================
df["future_max_20"] = grp["Close"].shift(-1).rolling(
    window=20, min_periods=20
).max()

df["label_monthly"] = (
    df["future_max_20"] >= df["Close"] * 1.20
).astype(int)

# =====================================================
# OPTIONAL: DOWNSIDE FILTER (ANTI FAKE BREAKOUT)
# Max drawdown 10% dalam horizon
# =====================================================
df["future_min_5"] = grp["Close"].shift(-1).rolling(
    window=5, min_periods=5
).min()

df.loc[
    df["future_min_5"] <= df["Close"] * 0.90,
    "label_weekly"
] = 0

# =====================================================
# CLEANING (BUANG ROW AKHIR TIAP SAHAM)
# =====================================================
df = df.dropna(subset=[
    "label_daily",
    "label_weekly",
    "label_monthly"
])

# =====================================================
# DROP HELPER COLUMNS
# =====================================================
df = df.drop(columns=[
    "close_next",
    "future_max_5",
    "future_max_20",
    "future_min_5"
])

# =====================================================
# SAVE
# =====================================================
df.to_parquet(OUTPUT_PATH, index=False)

# =====================================================
# LOG
# =====================================================
print("✅ ML LABELING SELESAI")
print("📦 Output :", OUTPUT_PATH)
print("📊 Baris :", f"{len(df):,}")
print("\n📈 Label Mean (positif ratio)")
print(df[["label_daily", "label_weekly", "label_monthly"]].mean().round(3))
