import pandas as pd
import os
from datetime import datetime
import uuid

# =====================================================
# 1. KONFIGURASI
# =====================================================
PATH = "processed/recommendation_history.parquet"
os.makedirs("processed", exist_ok=True)

# =====================================================
# 2. SCHEMA DEFINITIF (STABIL & CLEAN)
# =====================================================
COLUMNS = {
    "RecID": "string",
    "Tanggal": "datetime64[ns]",
    "Mode": "string",        # SWING / DAY / ML / MANUAL
    "Symbol": "string",      # Kode saham
    "Status": "string",      # OPEN / TP / SL / CANCEL
    "Entry": "float",
    "TP": "float",
    "SL": "float",
    "RR": "float",           # Risk Reward
    "Catatan": "string"
}

# =====================================================
# 3. BUAT FILE JIKA BELUM ADA
# =====================================================
if not os.path.exists(PATH):
    df = pd.DataFrame({
        col: pd.Series(dtype=dtype)
        for col, dtype in COLUMNS.items()
    })
    df.to_parquet(PATH, index=False)
    print("🆕 recommendation_history.parquet dibuat")
else:
    print("📦 recommendation_history.parquet sudah ada")

# =====================================================
# 4. CORE FUNCTION
# =====================================================
def add_recommendation(
    mode: str,
    symbol: str,
    entry: float,
    tp: float,
    sl: float,
    status: str = "OPEN",
    catatan: str = ""
):
    df = pd.read_parquet(PATH)

    # =========================
    # VALIDASI INPUT
    # =========================
    if entry is None or tp is None or sl is None:
        raise ValueError("Entry, TP, dan SL wajib diisi")

    entry = float(entry)
    tp = float(tp)
    sl = float(sl)

    # =========================
    # HITUNG RISK REWARD
    # =========================
    risk = entry - sl
    reward = tp - entry

    rr = round(reward / risk, 2) if risk > 0 else None

    # =========================
    # BUAT ROW BARU
    # =========================
    new_row = {
        "RecID": f"REC-{uuid.uuid4().hex[:10].upper()}",
        "Tanggal": pd.Timestamp.now(),
        "Mode": mode.upper(),
        "Symbol": symbol.upper(),
        "Status": status.upper(),
        "Entry": entry,
        "TP": tp,
        "SL": sl,
        "RR": rr,
        "Catatan": catatan
    }

    # =========================
    # APPEND & SAVE
    # =========================
    df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
    df.to_parquet(PATH, index=False)

    print(f"✅ REKOMENDASI DISIMPAN → {symbol} | {mode} | RR={rr}")

# =====================================================
# 5. CONTOH (OPSIONAL)
# =====================================================
# add_recommendation(
#     mode="SWING",
#     symbol="BBRI",
#     entry=5200,
#     tp=5560,
#     sl=4940,
#     catatan="Dekat support + bandar akumulasi"
# )
