import pandas as pd
import os
from datetime import date

# load data utama
df = pd.read_parquet("processed/daily_clean.parquet")

today = date.today()

rows = []

for s in df['Symbol'].unique():
    d = df[df['Symbol'] == s].sort_values("Tanggal Perdagangan Terakhir").tail(30)

    if len(d) < 20:
        continue

    latest = d.iloc[-1]

    if latest['Bandar'] == "AKUMULASI" and latest['Close'] <= latest['Support'] * 1.02:
        rows.append({
            "Tanggal": today,
            "Mode": "Harian (BPJS / BSJP)",
            "Saham": s,
            "Status": "BUY",
            "Entry": round(latest['Close'], 0),
            "TP": round(latest['Close'] * 1.03, 0),
            "SL": round(latest['Close'] * 0.97, 0),
            "Catatan": "Akumulasi bandar & dekat support"
        })

# kalau kosong → tetap bikin 1 baris
if not rows:
    rows.append({
        "Tanggal": today,
        "Mode": "Harian (BPJS / BSJP)",
        "Saham": "-",
        "Status": "NO TRADE",
        "Entry": None,
        "TP": None,
        "SL": None,
        "Catatan": "Tidak ada setup ideal hari ini"
    })

df_hist = pd.DataFrame(rows)

os.makedirs("processed", exist_ok=True)
df_hist.to_parquet("processed/recommendation_history.parquet", index=False)

print("✅ recommendation_history.parquet TERBUAT + TERISI")
