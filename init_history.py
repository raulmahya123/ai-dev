import pandas as pd
import os
from datetime import datetime

# =====================================================
# 1. KONFIGURASI
# =====================================================
PATH = "processed/recommendation_history.parquet"
os.makedirs("processed", exist_ok=True)

# =====================================================
# 2. SCHEMA DEFINITIF (ANTI BERANTAKAN)
# =====================================================
COLUMNS = {
    "RecID": "string",
    "Tanggal": "datetime64[ns]",
    "Mode": "string",       # SWING / DAY / ML / MANUAL
    "Saham": "string",      # Kode saham
    "Status": "string",     # OPEN / TP / SL / CANCEL
    "Entry": "float",
    "TP": "float",
    "SL": "float",
    "RR": "float",          # Risk Reward
    "Catatan": "string"
}

# =====================================================
# 3. BUAT FILE JIKA BELUM ADA
# =====================================================
if not os.path.exists(PATH):
    df = pd.DataFrame({col: pd.Series(dtype=dtype) for col, dtype in COLUMNS.items()})
    df.to_parquet(PATH, index=False)
    print("🆕 recommendation_history.parquet dibuat")
else:
    print("📦 recommendation_history.parquet sudah ada")

# =====================================================
# 4. FUNGSI APPEND REKOMENDASI (CORE VALUE)
# =====================================================
def add_recommendation(
    mode,
    saham,
    entry,
    tp,
    sl,
    status="OPEN",
    catatan=""
):
    df = pd.read_parquet(PATH)

    rr = None
    if entry and tp and sl:
        risk = entry - sl
        reward = tp - entry
        rr = round(reward / risk, 2) if risk > 0 else None

    new_row = {
        "RecID": f"REC-{datetime.now().strftime('%Y%m%d%H%M%S')}",
        "Tanggal": datetime.now(),
        "Mode": mode,
        "Saham": saham,
        "Status": status,
        "Entry": float(entry),
        "TP": float(tp),
        "SL": float(sl),
        "RR": rr,
        "Catatan": catatan
    }

    df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
    df.to_parquet(PATH, index=False)

    print(f"✅ REKOMENDASI DISIMPAN → {saham} | {mode} | RR={rr}")

# =====================================================
# 5. CONTOH PEMAKAIAN (BOLEH DIHAPUS)
# =====================================================
# add_recommendation(
#     mode="SWING",
#     saham="BBRI",
#     entry=5200,
#     tp=5560,
#     sl=4940,
#     catatan="Dekat support + bandar akumulasi"
# )
