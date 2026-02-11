import pandas as pd
import numpy as np

DATA_PATH = "processed/daily_clean.parquet"

# =====================================================
# 1. LOAD DATA
# =====================================================
df = pd.read_parquet(DATA_PATH)

print("📦 FILE :", DATA_PATH)
print("📊 TOTAL BARIS :", f"{len(df):,}")
print("📈 TOTAL SAHAM :", df["Symbol"].nunique())

# =====================================================
# 2. INFO STRUKTUR DATA
# =====================================================
print("\n🧱 STRUKTUR KOLOM")
print(df.dtypes)

# =====================================================
# 3. CEK DATA KOSONG & ANOMALI
# =====================================================
print("\n🧼 DATA QUALITY CHECK")

nulls = df.isnull().sum()
nulls = nulls[nulls > 0]

if nulls.empty:
    print("✅ Tidak ada nilai NULL penting")
else:
    print("⚠️ Kolom dengan NULL:")
    print(nulls)

# harga aneh
price_issues = df[
    (df["Close"] <= 0) |
    (df["High"] < df["Low"]) |
    (df["Open"] <= 0)
]

print("\n💣 ANOMALI HARGA :", len(price_issues))

# =====================================================
# 4. COVERAGE WAKTU
# =====================================================
print("\n🕒 RENTANG DATA")
print("Mulai :", df["Tanggal"].min())
print("Akhir :", df["Tanggal"].max())

# =====================================================
# 5. RINGKASAN BANDAR
# =====================================================
print("\n🏦 KOMPOSISI BANDAR")
print(df["Bandar"].value_counts(normalize=True).round(3))

# =====================================================
# 6. SIGNAL SUMMARY
# =====================================================
print("\n🟢 BUY SIGNAL SUMMARY")
print("Total BUY :", df["BUY"].sum())
print(
    "BUY Ratio :",
    round(df["BUY"].sum() / len(df) * 100, 2),
    "%"
)

# =====================================================
# 7. SUPPORT / RESISTANCE VALIDATION
# =====================================================
sr_issue = df[
    (df["Support"] > df["Close"]) |
    (df["Resistance"] < df["Close"])
]

print("\n📐 SR VALIDATION ISSUE :", len(sr_issue))

# =====================================================
# 8. STATISTIK CEPAT (BENERAN KEPAKAI)
# =====================================================
print("\n📊 STATISTIK HARGA (Close)")
print(df["Close"].describe())

print("\n📊 VOLUME")
print(df["Volume"].describe())

# =====================================================
# 9. TOP SAHAM PALING AKTIF
# =====================================================
print("\n🔥 TOP 10 SAHAM PALING SERING MUNCUL")
print(df["Symbol"].value_counts().head(10))

# =====================================================
# 10. SAMPLE DATA (AMAN)
# =====================================================
print("\n🔍 SAMPLE DATA RANDOM")
print(df.sample(5, random_state=42))
