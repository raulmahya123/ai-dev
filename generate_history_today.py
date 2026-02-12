import pandas as pd
import os
from datetime import date
import uuid

# =====================================================
# 1. KONFIGURASI
# =====================================================
DATA_PATH = "processed/daily_clean.parquet"
HIST_PATH = "processed/recommendation_history.parquet"

os.makedirs("processed", exist_ok=True)
today = pd.Timestamp(date.today())

# =====================================================
# 2. LOAD DATA UTAMA
# =====================================================
df = pd.read_parquet(DATA_PATH)

# Pastikan kolom tanggal konsisten
if "Tanggal" not in df.columns:
    if "Tanggal Perdagangan Terakhir" in df.columns:
        df["Tanggal"] = pd.to_datetime(
            df["Tanggal Perdagangan Terakhir"],
            errors="coerce"
        )

df["Tanggal"] = pd.to_datetime(df["Tanggal"], errors="coerce")

# =====================================================
# 3. AMBIL DATA TERAKHIR PER SAHAM
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
# 5. LOAD HISTORY (PASTIKAN ADA)
# =====================================================
if os.path.exists(HIST_PATH):
    hist = pd.read_parquet(HIST_PATH)
else:
    hist = pd.DataFrame(columns=[
        "RecID","Tanggal","Mode","Symbol","Status",
        "Entry","TP","SL","RR","Catatan"
    ])

# =====================================================
# 6. BANGUN REKOMENDASI
# =====================================================
rows = []

if not candidates.empty:

    for _, row in candidates.iterrows():

        entry = round(row["Close"], 0)
        tp = round(row["Close"] * 1.03, 0)
        sl = round(row["Close"] * 0.97, 0)

        risk = entry - sl
        reward = tp - entry
        rr = round(reward / risk, 2) if risk > 0 else None

        rows.append({
            "RecID": f"REC-{uuid.uuid4().hex[:8].upper()}",
            "Tanggal": today,
            "Mode": "DAY",
            "Symbol": row["Symbol"],
            "Status": "OPEN",
            "Entry": entry,
            "TP": tp,
            "SL": sl,
            "RR": rr,
            "Catatan": "Akumulasi bandar & dekat support"
        })

else:
    rows.append({
        "RecID": f"REC-{uuid.uuid4().hex[:8].upper()}",
        "Tanggal": today,
        "Mode": "DAY",
        "Symbol": "-",
        "Status": "NO TRADE",
        "Entry": None,
        "TP": None,
        "SL": None,
        "RR": None,
        "Catatan": "Tidak ada setup ideal hari ini"
    })

rec_today = pd.DataFrame(rows)

# =====================================================
# 7. HAPUS REKOMENDASI HARI INI (ANTI DOBEL)
# =====================================================
hist = hist[hist["Tanggal"] != today]

final = pd.concat([hist, rec_today], ignore_index=True)

# =====================================================
# 8. SIMPAN
# =====================================================
final.to_parquet(HIST_PATH, index=False)

# =====================================================
# 9. LOG
# =====================================================
print("✅ recommendation_history.parquet UPDATE BERHASIL")
print(f"📅 Tanggal      : {today.date()}")
print(f"📈 Total setup  : {(rec_today['Status'] == 'OPEN').sum()}")
print(f"🟡 NO TRADE row : {(rec_today['Status'] == 'NO TRADE').sum()}")
