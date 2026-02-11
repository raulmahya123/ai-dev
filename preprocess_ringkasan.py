import pandas as pd
import glob
import os

# =====================================================
# 1. KONFIGURASI PATH
# =====================================================
RAW_PATH = "data/ringkasan_saham/*.xlsx"
OUT_PATH = "processed/daily_clean.parquet"

files = glob.glob(RAW_PATH)

print("📂 File ditemukan:")
for f in files:
    print(" -", os.path.basename(f))

if not files:
    raise RuntimeError("❌ Tidak ada file Excel di data/ringkasan_saham")

# =====================================================
# 2. MAP BULAN INDONESIA → INGGRIS
# =====================================================
BULAN_MAP = {
    "Januari": "January",
    "Februari": "February",
    "Maret": "March",
    "April": "April",
    "Mei": "May",
    "Juni": "June",
    "Juli": "July",
    "Agustus": "August",
    "September": "September",
    "Oktober": "October",
    "November": "November",
    "Desember": "December",
}

def parse_tanggal_indo(x):
    if isinstance(x, str):
        for indo, eng in BULAN_MAP.items():
            x = x.replace(indo, eng)
    return pd.to_datetime(x, errors="coerce")

# =====================================================
# 3. LOAD + CLEAN SETIAP FILE
# =====================================================
dfs = []

for file in files:
    print(f"\n📥 Load {os.path.basename(file)}")
    df = pd.read_excel(file)

    # --- VALIDASI KOLOM WAJIB ---
    required_cols = [
        "Tanggal Perdagangan Terakhir",
        "Nama Perusahaan",
        "Open Price",
        "Tertinggi",
        "Terendah",
        "Penutupan",
        "Volume",
        "Foreign Buy",
        "Foreign Sell",
    ]

    missing = [c for c in required_cols if c not in df.columns]
    if missing:
        raise ValueError(f"❌ Kolom wajib tidak ada di {file}: {missing}")

    # --- PARSE TANGGAL ---
    df["Tanggal"] = df["Tanggal Perdagangan Terakhir"].apply(parse_tanggal_indo)
    df = df.dropna(subset=["Tanggal"])

    # --- RENAME KOLOM ---
    df = df.rename(
        columns={
            "Nama Perusahaan": "Symbol",
            "Open Price": "Open",
            "Tertinggi": "High",
            "Terendah": "Low",
            "Penutupan": "Close",
        }
    )

    # --- CAST NUMERIC ---
    numeric_cols = [
        "Open",
        "High",
        "Low",
        "Close",
        "Volume",
        "Foreign Buy",
        "Foreign Sell",
    ]
    df[numeric_cols] = df[numeric_cols].apply(
        pd.to_numeric, errors="coerce"
    )

    df = df.dropna(subset=["Close", "Low", "High"])

    dfs.append(df)

# =====================================================
# 4. GABUNG SEMUA DATA
# =====================================================
data = pd.concat(dfs, ignore_index=True)

data = data.sort_values(
    ["Symbol", "Tanggal"]
).reset_index(drop=True)

# =====================================================
# 5. DETEKSI BANDAR (FOREIGN FLOW)
# =====================================================
def classify_bandar(row):
    if row["Foreign Buy"] > row["Foreign Sell"]:
        return "AKUMULASI"
    elif row["Foreign Sell"] > row["Foreign Buy"]:
        return "DISTRIBUSI"
    else:
        return "NETRAL"

data["Bandar"] = data.apply(classify_bandar, axis=1)

# =====================================================
# 6. SUPPORT & RESISTANCE (ROLLING 20 HARI)
# =====================================================
data["Support"] = (
    data.groupby("Symbol")["Low"]
    .rolling(window=20, min_periods=5)
    .min()
    .reset_index(level=0, drop=True)
)

data["Resistance"] = (
    data.groupby("Symbol")["High"]
    .rolling(window=20, min_periods=5)
    .max()
    .reset_index(level=0, drop=True)
)

# =====================================================
# 7. SIGNAL BUY + TP / SL (SWING TRADING)
# =====================================================
data["BUY"] = (
    (data["Close"] <= data["Support"] * 1.02)
    & (data["Bandar"] == "AKUMULASI")
)

data["TP"] = (data["Close"] * 1.07).round(2)
data["SL"] = (data["Close"] * 0.95).round(2)

# =====================================================
# 8. SIMPAN KE PARQUET
# =====================================================
os.makedirs("processed", exist_ok=True)
data.to_parquet(OUT_PATH, index=False)

# =====================================================
# 9. RINGKASAN OUTPUT
# =====================================================
print("\n✅ PREPROCESS SELESAI")
print(f"📦 File      : {OUT_PATH}")
print(f"📊 Baris     : {len(data):,}")
print(f"📈 Saham     : {data['Symbol'].nunique():,}")
print(f"🏦 Akumulasi : {(data['Bandar'] == 'AKUMULASI').sum():,}")
print(f"🔴 Distribusi: {(data['Bandar'] == 'DISTRIBUSI').sum():,}")
print(f"🟢 BUY Signal: {data['BUY'].sum():,}")
