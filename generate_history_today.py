import pandas as pd
import os
from datetime import date, datetime

# =====================================================
# 1. KONFIGURASI
# =====================================================
DATA_PATH = "processed/daily_clean.parquet"
HIST_PATH = "processed/recommendation_history.parquet"

os.makedirs("processed", exist_ok=True)
today = pd.to_datetime(date.today())

# =====================================================
# 2. LOAD DATA UTAMA
# =====================================================
df = pd.read_parquet(DATA_PATH)

# pastikan kolom tanggal konsisten
if "Tanggal" not in df.columns:
    df["Tanggal"] = pd.to_datetime(df["Tanggal Perdagangan Terakhir"])

# =====================================================
# 3. AMBIL DATA TERAKHIR PER SAHAM (EFISIEN)
# =====================================================
df = df.sort_values(["Symbol", "Tanggal"])

latest = (
    df.groupby("Symbol")
    .tail(1)
    .reset_index(drop=True)
)

# =====================================================
# 4. FILTER SETUP IDEAL
# =====================================================
candidates = latest[
    (latest["Bandar"] == "AKUMULASI") &
    (latest["Close"] <= latest["Support"] * 1.02)
].copy()

# =====================================================
# 5. BANGUN REKOMENDASI
# =====================================================
if not candidates.empty:
    candidates["Tanggal"] = today
    candidates["Mode"] = "Harian (BPJS / BSJP)"
    candidates["Status"] = "OPEN"
    candidates["Entry"] = candidates["Close"].round(0)
    candidates["TP"] = (candidates["Close"] * 1.03).round(0)
    candidates["SL"] = (candidates["Close"] * 0.97).round(0)
    candidates["RR"] = (
        (candidates["TP"] - candidates["Entry"]) /
        (candidates["Entry"] - candidates["SL"])
    ).round(2)
    candidates["Catatan"] = "Akumulasi bandar & dekat support"

    rec_today = candidates[[
        "Tanggal", "Mode", "Symbol", "Status",
        "Entry", "TP", "SL", "RR", "Catatan"
    ]].rename(columns={"Symbol": "Saham"})

else:
    # =================================================
    # 6. JIKA TIDAK ADA SETUP
    # =================================================
    rec_today = pd.DataFrame([{
        "Tanggal": today,
        "Mode": "Harian (BPJS / BSJP)",
        "Saham": "-",
        "Status": "NO TRADE",
        "Entry": None,
        "TP": None,
        "SL": None,
        "RR": None,
        "Catatan": "Tidak ada setup ideal hari ini"
    }])

# =====================================================
# 7. LOAD HISTORY & APPEND (ANTI OVERWRITE)
# =====================================================
if os.path.exists(HIST_PATH):
    hist = pd.read_parquet(HIST_PATH)

    # hapus rekomendasi hari ini (anti dobel)
    hist = hist[hist["Tanggal"] != today]

    final = pd.concat([hist, rec_today], ignore_index=True)
else:
    final = rec_today

# =====================================================
# 8. SIMPAN
# =====================================================
final.to_parquet(HIST_PATH, index=False)

# =====================================================
# 9. LOG
# =====================================================
print("✅ recommendation_history.parquet UPDATE BERHASIL")
print(f"📅 Tanggal      : {today.date()}")
print(f"📈 Total setup  : {(final['Status'] == 'OPEN').sum()}")
print(f"🟡 NO TRADE row : {(final['Status'] == 'NO TRADE').sum()}")
