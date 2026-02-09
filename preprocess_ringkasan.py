import pandas as pd
import glob
import os

# =====================================================
# 1. LOAD FILE EXCEL RINGKASAN SAHAM
# =====================================================
PATH = "data/ringkasan_saham/*.xlsx"
files = glob.glob(PATH)

print("📂 File ditemukan:")
for f in files:
    print(" -", f)

if len(files) == 0:
    raise Exception("❌ Tidak ada file Excel di data/ringkasan_saham")

dfs = []

# =====================================================
# 2. MAP BULAN INDONESIA → INGGRIS
# =====================================================
bulan_map = {
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
    "Desember": "December"
}

def parse_tanggal_indo(x):
    if isinstance(x, str):
        for indo, eng in bulan_map.items():
            x = x.replace(indo, eng)
    return pd.to_datetime(x, errors="coerce")

# =====================================================
# 3. LOAD & CLEAN SETIAP FILE
# =====================================================
for file in files:
    df = pd.read_excel(file)

    # --- Parsing tanggal Indonesia ---
    df['Tanggal Perdagangan Terakhir'] = df[
        'Tanggal Perdagangan Terakhir'
    ].apply(parse_tanggal_indo)

    # Drop kalau tanggal invalid
    df = df.dropna(subset=['Tanggal Perdagangan Terakhir'])

    # --- Rename kolom agar konsisten ---
    df.rename(columns={
        "Nama Perusahaan": "Symbol",
        "Open Price": "Open",
        "Tertinggi": "High",
        "Terendah": "Low",
        "Penutupan": "Close",
        "Volume": "Volume"
    }, inplace=True)

    dfs.append(df)

# =====================================================
# 4. GABUNG SEMUA DATA
# =====================================================
data = pd.concat(dfs, ignore_index=True)

data.sort_values(
    ["Symbol", "Tanggal Perdagangan Terakhir"],
    inplace=True
)

# =====================================================
# 5. DETEKSI BANDAR (FOREIGN FLOW)
# =====================================================
def bandar(row):
    if row['Foreign Buy'] > row['Foreign Sell']:
        return "AKUMULASI"
    elif row['Foreign Sell'] > row['Foreign Buy']:
        return "DISTRIBUSI"
    else:
        return "NETRAL"

data['Bandar'] = data.apply(bandar, axis=1)

# =====================================================
# 6. SUPPORT & RESISTANCE (20 HARI)
# =====================================================
data['Support'] = (
    data.groupby("Symbol")['Low']
    .rolling(20)
    .min()
    .reset_index(0, drop=True)
)

data['Resistance'] = (
    data.groupby("Symbol")['High']
    .rolling(20)
    .max()
    .reset_index(0, drop=True)
)

# =====================================================
# 7. SIGNAL BUY + TP SL (SWING)
# =====================================================
data['BUY'] = (
    (data['Close'] <= data['Support'] * 1.02) &
    (data['Bandar'] == "AKUMULASI")
)

data['TP'] = data['Close'] * 1.07   # Take Profit 7%
data['SL'] = data['Close'] * 0.95   # Stop Loss 5%

# =====================================================
# 8. SIMPAN DATA CEPAT (PARQUET)
# =====================================================
os.makedirs("processed", exist_ok=True)
data.to_parquet("processed/daily_clean.parquet", index=False)

print("\n✅ PREPROCESS SELESAI")
print("📦 File tersimpan : processed/daily_clean.parquet")
print("📊 Total baris    :", len(data))
print("📈 Total saham    :", data['Symbol'].nunique())
print("🏦 Akumulasi rows :", (data['Bandar'] == 'AKUMULASI').sum())
print("🔴 Distribusi rows:", (data['Bandar'] == 'DISTRIBUSI').sum())
