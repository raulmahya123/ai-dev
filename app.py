# ============================================================
# SAHAMAI - STOCK RECOMMENDATION PLATFORM (IDX)
# Full Stable Version (No Crash, Backward Compatible)
# ============================================================

import streamlit as st
import pandas as pd
import mplfinance as mpf
import numpy as np
import os
from datetime import datetime, date, time

# ============================================================
# PAGE CONFIG
# ============================================================
st.set_page_config(
    page_title="SahamAI | Intelligent Stock Recommendation",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ============================================================
# GLOBAL STYLE
# ============================================================
st.markdown("""
<style>
.buy-box {background:#e8f5e9;padding:16px;border-radius:12px;border-left:6px solid #2e7d32;}
.sell-box {background:#fdecea;padding:16px;border-radius:12px;border-left:6px solid #c62828;}
.wait-box {background:#f5f5f5;padding:16px;border-radius:12px;border-left:6px solid #9e9e9e;}
.small {font-size:14px;color:#6c757d;}
</style>
""", unsafe_allow_html=True)

# ============================================================
# HEADER
# ============================================================
st.markdown("## 📊 SahamAI")
st.markdown(
    "<div class='small'>Platform Rekomendasi Saham IDX berbasis "
    "Ringkasan Saham, Aktivitas Bandar, dan Analisa Teknis</div>",
    unsafe_allow_html=True
)
st.markdown("---")

# ============================================================
# PATH
# ============================================================
DATA_PATH = "processed/daily_clean.parquet"
HISTORY_PATH = "processed/recommendation_history.parquet"

# ============================================================
# LOAD DATA
# ============================================================
@st.cache_data
def load_data():
    return pd.read_parquet(DATA_PATH)

df = load_data()

# ============================================================
# SIDEBAR NAVIGATION
# ============================================================
st.sidebar.markdown("## 🧭 Navigasi")

menu = st.sidebar.radio(
    "Menu",
    [
        "🏠 Dashboard",
        "📅 Rekomendasi Harian",
        "📊 Rekomendasi Swing",
        "🔍 Analisa 1 Saham",
        "⭐ Watchlist",
        "📈 History & Winrate",
        "ℹ️ Tentang Sistem"
    ]
)

st.sidebar.markdown("---")
st.sidebar.info(
    "📌 SahamAI menyaring peluang terbaik.\n\n"
    "Tidak semua hari harus transaksi."
)

# ============================================================
# HELPER FUNCTIONS
# ============================================================
def confidence_score(latest, vol_median):
    score = 0
    if latest["Bandar"] == "AKUMULASI":
        score += 40
    if latest["Close"] <= latest["Support"] * 1.02:
        score += 30
    if latest["Volume"] >= vol_median:
        score += 20
    if latest["Close"] > latest["Support"]:
        score += 10
    return min(score, 100)

def scan_market(df, window, tp_mult, sl_mult, mode_label):
    rows = []

    for sym in df["Symbol"].unique():
        d = df[df["Symbol"] == sym].sort_values(
            "Tanggal Perdagangan Terakhir"
        ).tail(window)

        if len(d) < 20:
            continue

        latest = d.iloc[-1]
        vol_median = d["Volume"].median()
        conf = confidence_score(latest, vol_median)

        if conf >= 60:
            rows.append({
                "Tanggal": date.today(),
                "Mode": mode_label,
                "Saham": sym,
                "Harga": round(latest["Close"], 0),
                "Support": round(latest["Support"], 0),
                "Resistance": round(latest["Resistance"], 0),
                "TP": round(latest["Close"] * tp_mult, 0),
                "SL": round(latest["Close"] * sl_mult, 0),
                "Confidence": conf,
                "Status": "BUY" if conf >= 70 else "WATCH"
            })

    return pd.DataFrame(rows)

def auto_daily_snapshot(scan_df, mode_label):
    now = datetime.now().time()

    if now >= time(8,45) and now <= time(9,5):

        if scan_df.empty:
            df_save = pd.DataFrame([{
                "Tanggal": date.today(),
                "Mode": mode_label,
                "Saham": "-",
                "Harga": None,
                "TP": None,
                "SL": None,
                "Confidence": 0,
                "Status": "NO TRADE",
                "Catatan": "Market belum ideal"
            }])
        else:
            df_save = scan_df.copy()
            df_save["Catatan"] = "Auto snapshot 08:45"

        if os.path.exists(HISTORY_PATH):
            hist = pd.read_parquet(HISTORY_PATH)

            # ==== BACKWARD COMPATIBILITY ====
            if "Confidence" not in hist.columns:
                hist["Confidence"] = 0

            hist = hist[~(
                (hist["Tanggal"] == date.today()) &
                (hist["Mode"] == mode_label)
            )]

            hist = pd.concat([hist, df_save], ignore_index=True)
        else:
            hist = df_save

        hist.to_parquet(HISTORY_PATH, index=False)

# ============================================================
# 🏠 DASHBOARD
# ============================================================
if menu == "🏠 Dashboard":

    st.subheader("📊 Market Overview Hari Ini")

    latest_all = df.groupby("Symbol").tail(1)

    c1, c2, c3 = st.columns(3)
    c1.metric("Total Saham", latest_all.shape[0])
    c2.metric("Akumulasi", (latest_all["Bandar"] == "AKUMULASI").sum())
    c3.metric("Distribusi", (latest_all["Bandar"] == "DISTRIBUSI").sum())

    st.markdown("---")
    st.info("Gunakan menu kiri untuk rekomendasi & analisa detail.")

# ============================================================
# 📅 REKOMENDASI HARIAN
# ============================================================
elif menu == "📅 Rekomendasi Harian":

    st.subheader("📅 Rekomendasi Harian (BPJS / BSJP)")

    scan_df = scan_market(df, 30, 1.03, 0.97, "Harian")
    auto_daily_snapshot(scan_df, "Harian")

    if scan_df.empty:
        st.warning("Tidak ada setup ideal hari ini.")
    else:
        st.success(f"Ditemukan {len(scan_df)} saham potensial")
        st.dataframe(scan_df, width="stretch")

# ============================================================
# 📊 REKOMENDASI SWING
# ============================================================
elif menu == "📊 Rekomendasi Swing":

    st.subheader("📊 Rekomendasi Swing Mingguan")

    scan_df = scan_market(df, 120, 1.07, 0.95, "Swing")
    auto_daily_snapshot(scan_df, "Swing")

    if scan_df.empty:
        st.warning("Belum ada setup swing ideal.")
    else:
        st.success(f"Ditemukan {len(scan_df)} saham swing")
        st.dataframe(scan_df, width="stretch")

# ============================================================
# 🔍 ANALISA 1 SAHAM
# ============================================================
elif menu == "🔍 Analisa 1 Saham":

    st.subheader("🔍 Analisa Detail Saham")

    symbol = st.selectbox("Pilih Saham", sorted(df["Symbol"].unique()))
    df_s = df[df["Symbol"] == symbol].copy().tail(120)
    latest = df_s.iloc[-1]

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Harga", f"{latest['Close']:.0f}")
    c2.metric("Bandar", latest["Bandar"])
    c3.metric("Support", f"{latest['Support']:.0f}")
    c4.metric("Resistance", f"{latest['Resistance']:.0f}")

    st.markdown("---")

    if latest["Bandar"] == "AKUMULASI" and latest["Close"] <= latest["Support"] * 1.02:
        st.markdown(f"""
        <div class="buy-box">
        🟢 <b>REKOMENDASI BELI</b><br><br>
        Entry: {latest['Close']:.0f}<br>
        TP: {latest['Close']*1.07:.0f}<br>
        SL: {latest['Close']*0.95:.0f}
        </div>
        """, unsafe_allow_html=True)
    elif latest["Bandar"] == "DISTRIBUSI":
        st.markdown("<div class='sell-box'>🔴 DISTRIBUSI – Hindari entry</div>", unsafe_allow_html=True)
    else:
        st.markdown("<div class='wait-box'>⚪ WAIT & SEE</div>", unsafe_allow_html=True)

    st.markdown("### 📈 Grafik Candlestick")

    df_chart = df_s.set_index("Tanggal Perdagangan Terakhir")
    fig, _ = mpf.plot(
        df_chart,
        type="candle",
        style="yahoo",
        volume=True,
        mav=(5,20),
        returnfig=True,
        figsize=(16,8),
        title=symbol
    )
    st.pyplot(fig)

# ============================================================
# ⭐ WATCHLIST
# ============================================================
elif menu == "⭐ Watchlist":

    st.subheader("⭐ Watchlist (Akumulasi Bandar)")

    watch = df.groupby("Symbol").tail(1)
    watch = watch[watch["Bandar"] == "AKUMULASI"]

    if watch.empty:
        st.info("Belum ada saham fase akumulasi.")
    else:
        st.dataframe(
            watch[["Symbol", "Close", "Support", "Resistance"]],
            width="stretch"
        )

# ============================================================
# 📈 HISTORY & WINRATE (SAFE)
# ============================================================
elif menu == "📈 History & Winrate":

    st.subheader("📈 History & Winrate")

    if not os.path.exists(HISTORY_PATH):
        st.info("Belum ada history.")
    else:
        hist = pd.read_parquet(HISTORY_PATH)

        # ==== SAFETY FIX ====
        if "Confidence" not in hist.columns:
            hist["Confidence"] = 0

        st.dataframe(hist.sort_values("Tanggal", ascending=False), width="stretch")

        buy_hist = hist[hist["Status"] == "BUY"].copy()

        if len(buy_hist) >= 5:
            winrate = (buy_hist["Confidence"] >= 70).mean() * 100
            st.metric("Winrate (Confidence-based)", f"{winrate:.2f}%")
            st.line_chart(buy_hist.groupby("Tanggal")["Confidence"].mean())
        else:
            st.warning("Data BUY belum cukup untuk hitung winrate.")

# ============================================================
# ℹ️ ABOUT
# ============================================================
elif menu == "ℹ️ Tentang Sistem":

    st.subheader("ℹ️ Tentang SahamAI")

    st.markdown("""
    **SahamAI** adalah platform analisa saham berbasis data.

    ✔ Confidence score 0–100  
    ✔ History & winrate  
    ✔ Snapshot otomatis 08:45  
    ✔ Harian & swing  

    ⚠️ Edukasi, bukan rekomendasi resmi.
    """)

# ============================================================
# FOOTER
# ============================================================
st.markdown("""
---
© 2026 **SahamAI** | IDX Stock Analytics
""")
