import pandas as pd
import numpy as np
import os

DATA_PATH = "ml/dataset_features.parquet"
OUTPUT_PATH = "ml/dataset_ml_ready.parquet"

os.makedirs("ml", exist_ok=True)

# =====================================================
# LOAD
# =====================================================
df = pd.read_parquet(DATA_PATH)

if "Close" not in df.columns:
    raise ValueError("❌ Column 'Close' not found in dataset_features.parquet")

df["Tanggal"] = pd.to_datetime(df["Tanggal"])
df = df.sort_values(["Symbol","Tanggal"]).reset_index(drop=True)

grp = df.groupby("Symbol", group_keys=False)

# =====================================================
# DAILY
# =====================================================
df["RET_1D_FWD"] = grp["Close"].shift(-1) / df["Close"] - 1
df["label_daily"] = (df["RET_1D_FWD"] > 0).astype(int)

# =====================================================
# WEEKLY
# =====================================================
df["FWD_MAX_5"] = grp["Close"].transform(
    lambda x: x.shift(-1).rolling(5, min_periods=5).max()
)

df["FWD_MIN_5"] = grp["Close"].transform(
    lambda x: x.shift(-1).rolling(5, min_periods=5).min()
)

df["label_weekly"] = (
    (df["FWD_MAX_5"] >= df["Close"] * 1.05) &
    (df["FWD_MIN_5"] > df["Close"] * 0.90)
).astype(int)

# =====================================================
# MONTHLY
# =====================================================
df["FWD_MAX_20"] = grp["Close"].transform(
    lambda x: x.shift(-1).rolling(20, min_periods=20).max()
)

df["label_monthly"] = (
    df["FWD_MAX_20"] >= df["Close"] * 1.20
).astype(int)

# =====================================================
# CLEAN (REMOVE TAIL ROWS WITHOUT HORIZON)
# =====================================================
df = df.dropna(subset=[
    "RET_1D_FWD",
    "FWD_MAX_5",
    "FWD_MAX_20"
])

df = df.drop(columns=[
    "RET_1D_FWD",
    "FWD_MAX_5",
    "FWD_MIN_5",
    "FWD_MAX_20"
])

df.to_parquet(OUTPUT_PATH, index=False)

print("✅ LABEL BUILD COMPLETE")
print("Rows:", len(df))
print(df[["label_daily","label_weekly","label_monthly"]].mean())
