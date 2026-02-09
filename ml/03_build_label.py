import pandas as pd
import numpy as np

DATA_PATH = "ml/dataset_features.parquet"
OUTPUT_PATH = "ml/dataset_ml_ready.parquet"

df = pd.read_parquet(DATA_PATH)

# Pastikan urut waktu per saham
df = df.sort_values(
    ["Kode Saham", "Tanggal Perdagangan Terakhir"]
).reset_index(drop=True)

# =========================
# LABEL DAILY (BSJP - proxy)
# Close hari ini > Close kemarin
# =========================
df["prev_close"] = df.groupby("Kode Saham")["Close"].shift(1)

df["label_daily"] = (
    df["Close"] > df["prev_close"]
).astype(int)


# =========================
# LABEL WEEKLY (Swing ±5 hari)
# Max close 5 hari ke depan >= +5%
# =========================
df["future_max_5"] = (
    df.groupby("Kode Saham")["Close"]
      .shift(-1)
      .rolling(5)
      .max()
)

df["label_weekly"] = (
    df["future_max_5"] >= df["Close"] * 1.05
).astype(int)

# =========================
# LABEL MONTHLY (Long term ±20 hari)
# Max close 20 hari ke depan >= +20%
# =========================
df["future_max_20"] = (
    df.groupby("Kode Saham")["Close"]
      .shift(-1)
      .rolling(20)
      .max()
)

df["label_monthly"] = (
    df["future_max_20"] >= df["Close"] * 1.20
).astype(int)

# =========================
# CLEANING
# =========================
df = df.dropna(subset=[
    "label_daily",
    "label_weekly",
    "label_monthly"
])

# =========================
# SAVE
# =========================
df.to_parquet(OUTPUT_PATH)

print("Labeling selesai.")
print("Jumlah baris akhir:", len(df))
print(df[["label_daily", "label_weekly", "label_monthly"]].mean())
