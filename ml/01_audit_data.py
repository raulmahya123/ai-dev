import pandas as pd
import numpy as np
import os

# =====================================================
# CONFIG
# =====================================================
INPUT_PATH = "processed/daily_clean.parquet"
OUTPUT_PATH = "processed/daily_clean_strict.parquet"

os.makedirs("processed", exist_ok=True)

print("="*70)
print("📦 DATA AUDIT & CLEAN PIPELINE (PRO VERSION)")
print("="*70)

# =====================================================
# LOAD
# =====================================================
df = pd.read_parquet(INPUT_PATH)

print("📊 RAW ROWS:", f"{len(df):,}")
print("📈 TOTAL SAHAM:", df["Symbol"].nunique())

# =====================================================
# STANDARDIZE DATA TYPES
# =====================================================
df["Tanggal"] = pd.to_datetime(df["Tanggal"], errors="coerce")
df = df.dropna(subset=["Symbol","Tanggal","Close"])

df = df.sort_values(["Symbol","Tanggal"]).reset_index(drop=True)

# =====================================================
# 1️⃣ REMOVE DUPLICATE SYMBOL-DATE
# =====================================================
before = len(df)
df = df.drop_duplicates(subset=["Symbol","Tanggal"], keep="last")
print("🧹 Removed duplicate Symbol-Date:", before - len(df))

# =====================================================
# 2️⃣ REMOVE INVALID PRICE
# =====================================================
valid_price = (
    (df["Close"] > 0) &
    (df["Open"] > 0) &
    (df["High"] > 0) &
    (df["Low"] > 0) &
    (df["High"] >= df["Low"])
)

before = len(df)
df = df[valid_price]
print("💣 Removed invalid price rows:", before - len(df))

# =====================================================
# 3️⃣ REMOVE ZERO VOLUME
# =====================================================
before = len(df)
df = df[df["Volume"] > 0]
print("📦 Removed zero volume rows:", before - len(df))

# =====================================================
# 4️⃣ EXTREME RETURN FILTER (> ±50%)
# =====================================================
df["ret_1d"] = df.groupby("Symbol")["Close"].pct_change()

before = len(df)
df = df[np.abs(df["ret_1d"]) <= 0.5]
print("📉 Removed extreme return rows:", before - len(df))

# =====================================================
# 5️⃣ LOG-BASED OUTLIER FILTER (ROBUST)
# =====================================================
df["log_close"] = np.log(df["Close"])
z = (df["log_close"] - df["log_close"].mean()) / df["log_close"].std()

before = len(df)
df = df[np.abs(z) <= 6]
print("📊 Removed extreme price outliers:", before - len(df))

df = df.drop(columns=["log_close"], errors="ignore")

# =====================================================
# 6️⃣ SUPPORT / RESISTANCE VALIDATION
# =====================================================
if "Support" in df.columns and "Resistance" in df.columns:

    valid_sr = (
        df["Support"].isna() |
        df["Resistance"].isna() |
        (
            (df["Support"] <= df["Low"]) &
            (df["Resistance"] >= df["High"])
        )
    )

    before = len(df)
    df = df[valid_sr]
    print("📐 Removed SR logic issue rows:", before - len(df))

# =====================================================
# 7️⃣ FINAL CLEAN
# =====================================================
df = df.drop(columns=["ret_1d"], errors="ignore")
df = df.sort_values(["Symbol","Tanggal"]).reset_index(drop=True)

# =====================================================
# FINAL SUMMARY
# =====================================================
print("\n" + "="*70)
print("📊 FINAL CLEAN SUMMARY")
print("="*70)

print("Rows:", f"{len(df):,}")
print("Stocks:", df["Symbol"].nunique())
print("Date range:", df["Tanggal"].min(), "→", df["Tanggal"].max())

print("\n🏦 Bandar Distribution")
if "Bandar" in df.columns:
    print(df["Bandar"].value_counts(normalize=True).round(3))

print("\n📊 CLOSE STATS")
print(df["Close"].describe())

print("\n📊 VOLUME STATS")
print(df["Volume"].describe())

print("\n🔥 TOP 10 AKTIF")
print(df["Symbol"].value_counts().head(10))

print("\n🔍 RANDOM SAMPLE")
print(df.sample(min(5, len(df)), random_state=42))

print("\n" + "="*70)
print("✅ CLEAN DATA READY FOR FEATURE ENGINEERING")
print("="*70)

# =====================================================
# SAVE CLEAN DATA
# =====================================================
df.to_parquet(OUTPUT_PATH, index=False)

print("\n💾 Saved to:", OUTPUT_PATH)
