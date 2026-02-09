# ============================================================
# SAHAMAI ENTERPRISE EDITION
# 1 FILE • VERBOSE • 900+ LINES
# DAILY • WEEKLY • MONTHLY • WATCHLIST • AI • BACKTEST
# ============================================================

# ============================================================
# IMPORTS
# ============================================================

import streamlit as st
import pandas as pd
import numpy as np
import mplfinance as mpf
import os
import requests

from datetime import (
    datetime,
    date,
    time,
    timedelta
)

# ============================================================
# PAGE CONFIGURATION
# ============================================================

st.set_page_config(
    page_title="SahamAI Enterprise | IDX Trading System",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ============================================================
# GLOBAL THEME – ELEGANT GREEN TERMINAL
# ============================================================

st.markdown("""
<style>

/* =====================================================
   SIDENAVBAR (HIJAU GRADIENT - FIX)
===================================================== */
section[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #0b3d2e, #1b5e20);
}

section[data-testid="stSidebar"] * {
    color: #ffffff !important;
}

/* Divider sidebar */
section[data-testid="stSidebar"] hr {
    border-color: rgba(255,255,255,0.25);
}

/* Sidebar info box */
section[data-testid="stSidebar"] .stAlert {
    background: rgba(255,255,255,0.12);
    border: 1px solid rgba(255,255,255,0.25);
}

/* Hover menu sidebar */
section[data-testid="stSidebar"] div[role="radiogroup"] > label:hover {
    background: rgba(255,255,255,0.12);
    border-radius: 8px;
    padding-left: 6px;
}

/* =====================================================
   DASHBOARD SECTION (TIDAK KENA SIDEBAR)
===================================================== */
.section-box {
    background: #ffffff;
    padding: 22px;
    border-radius: 14px;
    border: 1px solid #e5e7eb;
    box-shadow: 0 6px 18px rgba(0,0,0,0.04);
    margin-bottom: 26px;
}

/* KPI BOX */
.kpi-box {
    background: #ffffff;
    padding: 18px;
    border-radius: 12px;
    border: 1px solid #e5e7eb;
    box-shadow: 0 4px 12px rgba(0,0,0,0.04);
}

.kpi-title {
    font-size: 14px;
    color: #6b7280;
    margin-bottom: 6px;
}

.kpi-value {
    font-size: 32px;
    font-weight: 700;
    color: #111827;
}

/* INFO BAR */
.info-bar {
    background: #eef6ff;
    padding: 12px 16px;
    border-radius: 10px;
    font-weight: 500;
    color: #1d4ed8;
    margin-bottom: 18px;
}

/* =====================================================
   HEATMAP CARD
===================================================== */
.card {
    padding: 14px 16px;
    margin-bottom: 10px;
    border-radius: 10px;
    font-weight: 600;
    font-size: 14px;
    transition: all 0.25s ease;
}

/* STRONG BUY */
.card-strong {
    color: #0f5132;
    background: rgba(25, 135, 84, 0.22);
    border: 1px solid rgba(25, 135, 84, 0.45);
}
.card-strong:hover {
    box-shadow: 0 0 14px rgba(25, 135, 84, 0.45);
    transform: translateY(-2px);
}

/* BUY / WATCH */
.card-mid {
    color: #146c43;
    background: rgba(25, 135, 84, 0.14);
    border: 1px solid rgba(25, 135, 84, 0.28);
}
.card-mid:hover {
    box-shadow: 0 0 12px rgba(25, 135, 84, 0.30);
    transform: translateY(-2px);
}

/* WAIT */
.card-low {
    color: #495057;
    background: rgba(108, 117, 125, 0.15);
    border: 1px solid rgba(108, 117, 125, 0.35);
}
.card-low:hover {
    box-shadow: 0 0 10px rgba(108, 117, 125, 0.35);
    transform: translateY(-2px);
}

.card span {
    font-size: 12px;
    font-weight: 500;
}

</style>
""", unsafe_allow_html=True)


# ============================================================
# HEADER
# ============================================================

st.markdown("""
<style>
.enterprise-title {
    font-size: 28px;
    font-weight: 700;
    color: #000000;
    margin-bottom: 2px;
}

.enterprise-subtitle {
    font-size: 14px;
    font-weight: 400;
    color: #000000;
    letter-spacing: 0.5px;
    margin-bottom: 12px;
}
</style>

<div class="enterprise-title">
    📊 SahamAI Enterprise
</div>
<div class="enterprise-subtitle">
    Daily • Weekly • Monthly • Score • Backtest • Heatmap
</div>
<hr>
""", unsafe_allow_html=True)

# ============================================================
# PATH CONFIGURATION
# ============================================================

DATA_PATH = "processed/daily_clean.parquet"
HISTORY_PATH = "processed/recommendation_history.parquet"

# ============================================================
# DATA LOADER
# ============================================================

@st.cache_data
def load_data():
    """
    Load cleaned daily IDX data.
    Must contain:
    Symbol, Close, High, Low, Volume,
    Support, Resistance, Bandar,
    Tanggal Perdagangan Terakhir
    """
    if not os.path.exists(DATA_PATH):
        st.error("❌ Data tidak ditemukan")
        st.stop()
    return pd.read_parquet(DATA_PATH)

df = load_data()

# ============================================================
# TIME & MARKET SESSION ENGINE
# ============================================================

def market_open_status():
    now = datetime.now()
    open_time = datetime.combine(date.today(), time(9, 0))
    close_time = datetime.combine(date.today(), time(15, 0))

    if now < open_time:
        return "PREOPEN", open_time - now
    elif open_time <= now <= close_time:
        return "OPEN", None
    else:
        return "CLOSED", None

def market_countdown_text():
    status, delta = market_open_status()
    if status == "PREOPEN":
        return f"⏰ Market Open dalam {str(delta).split('.')[0]}"
    elif status == "OPEN":
        return "🟢 Market Sedang Buka"
    else:
        return "🔴 Market Tutup"

# ============================================================
# INDICATOR ENGINE
# ============================================================

def compute_rsi(series, period=14):
    delta = series.diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)

    avg_gain = gain.rolling(period).mean()
    avg_loss = loss.rolling(period).mean()

    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))
    return rsi

def compute_ema(series, span):
    return series.ewm(span=span, adjust=False).mean()

def compute_volume_spike(volume, window=20):
    median_vol = volume.rolling(window).median()
    return volume / median_vol

# ============================================================
# BANDAR ANALYSIS ENGINE
# ============================================================

def bandar_score(bandar_status):
    if bandar_status == "AKUMULASI":
        return 40
    elif bandar_status == "DISTRIBUSI":
        return -20
    return 0

# ============================================================
# AI SCORE ENGINE (VERBOSE)
# ============================================================

def compute_ai_score(df_s):
    """
    Composite AI score:
    - Bandar
    - EMA Trend
    - RSI
    - Volume
    """

    df_s = df_s.copy()

    # EMA
    df_s["EMA20"] = compute_ema(df_s["Close"], 20)
    df_s["EMA50"] = compute_ema(df_s["Close"], 50)

    # RSI
    df_s["RSI"] = compute_rsi(df_s["Close"])

    # Volume Spike
    df_s["VOL_SPIKE"] = compute_volume_spike(df_s["Volume"])

    latest = df_s.iloc[-1]

    score = 0

    # Bandar
    score += bandar_score(latest["Bandar"])

    # Trend
    if latest["EMA20"] > latest["EMA50"]:
        score += 25

    # RSI
    if latest["RSI"] < 70:
        score += 20
    elif latest["RSI"] > 80:
        score -= 10

    # Volume
    if latest["VOL_SPIKE"] > 1.2:
        score += 15

    return min(max(score, 0), 100)

# ============================================================
# STRATEGY BASE ENGINE
# ============================================================

def generate_strategy(
    df,
    window,
    mode_name
):
    rows = []

    for symbol in df["Symbol"].unique():
        d = df[df["Symbol"] == symbol].tail(window)

        if len(d) < window * 0.7:
            continue

        score = compute_ai_score(d)
        latest = d.iloc[-1]

        if score >= 60:
            rows.append({
                "Mode": mode_name,
                "Saham": symbol,
                "Harga": round(latest["Close"], 0),
                "Support": round(latest["Support"], 0),
                "Resistance": round(latest["Resistance"], 0),
                "AI Score": score,
                "Bandar": latest["Bandar"],
                "Status": "BUY" if score >= 75 else "WATCH"
            })

    if not rows:
        return pd.DataFrame()

    return (
        pd.DataFrame(rows)
        .sort_values("AI Score", ascending=False)
        .reset_index(drop=True)
    )

# ============================================================
# ====== STOP PART 1 ======
# NEXT: STRATEGY DAILY/WEEKLY/MONTHLY, HEATMAP, BACKTEST
# ============================================================
# ============================================================
# STRATEGY ENGINE – DAILY / WEEKLY / MONTHLY
# ============================================================

def strategy_daily(df):
    """
    Daily trading strategy (momentum & volume driven)
    """
    rows = []

    for symbol in df["Symbol"].unique():
        d_all = df[df["Symbol"] == symbol].sort_values("Tanggal Perdagangan Terakhir")

        # Adaptive window (daily)
        window = min(30, len(d_all))
        d = d_all.tail(window)

        if len(d) < 15:
            continue

        # =========================
        # INDICATORS
        # =========================
        d = d.copy()
        d["EMA10"] = compute_ema(d["Close"], 10)
        d["EMA20"] = compute_ema(d["Close"], 20)
        d["RSI"] = compute_rsi(d["Close"])
        d["VOL_MED20"] = d["Volume"].rolling(20).median()

        latest = d.iloc[-1]

        # =========================
        # DAILY LOGIC
        # =========================
        trend_ok = latest["EMA10"] > latest["EMA20"]
        momentum_ok = 45 <= latest["RSI"] <= 70
        volume_ok = latest["Volume"] > latest["VOL_MED20"]
        price_ok = latest["Close"] > latest["EMA10"]

        daily_score = sum([
            trend_ok * 30,
            momentum_ok * 25,
            volume_ok * 25,
            price_ok * 20
        ])  # max 100

        # =========================
        # AI SCORE (MASTER FILTER)
        # =========================
        ai_score = compute_ai_score(d)

        final_score = int(0.6 * ai_score + 0.4 * daily_score)

        # =========================
        # ENTRY FILTER
        # =========================
        if final_score >= 60 and latest["Bandar"] != "DISTRIBUSI":
            rows.append({
                "Mode": "HARIAN",
                "Saham": symbol,
                "Harga": round(latest["Close"], 0),
                "Support": round(latest["Support"], 0),
                "Resistance": round(latest["Resistance"], 0),
                "AI Score": ai_score,
                "Daily Score": daily_score,
                "Final Score": final_score,
                "Bandar": latest["Bandar"],
                "Status": "BUY" if final_score >= 75 else "WATCH"
            })

    return (
        pd.DataFrame(rows)
        .sort_values("Final Score", ascending=False)
        .reset_index(drop=True)
        if rows else pd.DataFrame()
    )


def strategy_weekly(df):
    """
    Swing weekly strategy (adaptive)
    """
    rows = []

    for symbol in df["Symbol"].unique():
        d_all = df[df["Symbol"] == symbol]
        window = min(120, len(d_all))  # adaptif
        d = d_all.tail(window)

        if len(d) < 50:
            continue

        score = compute_ai_score(d)
        latest = d.iloc[-1]

        if score >= 60:
            rows.append({
                "Mode": "MINGGUAN",
                "Saham": symbol,
                "Harga": round(latest["Close"], 0),
                "Support": round(latest["Support"], 0),
                "Resistance": round(latest["Resistance"], 0),
                "AI Score": score,
                "Bandar": latest["Bandar"],
                "Status": "BUY" if score >= 75 else "WATCH"
            })

    return (
        pd.DataFrame(rows)
        .sort_values("AI Score", ascending=False)
        .reset_index(drop=True)
        if rows else pd.DataFrame()
    )


def strategy_monthly(df):
    """
    Position trading (long term / investor grade) – stable version
    """
    rows = []

    for symbol in df["Symbol"].unique():
        d_all = df[df["Symbol"] == symbol].sort_values("Tanggal Perdagangan Terakhir")

        # Adaptive window
        window = min(250, len(d_all))
        d = d_all.tail(window)

        if len(d) < 100:   # relax: ±5 bulan data
            continue

        # =========================
        # INDICATORS
        # =========================
        d = d.copy()
        d["EMA50"] = compute_ema(d["Close"], 50)
        d["EMA200"] = compute_ema(d["Close"], 200)
        d["RSI"] = compute_rsi(d["Close"])
        d["VOL_MED50"] = d["Volume"].rolling(50).median()

        latest = d.iloc[-1]

        # =========================
        # MONTHLY LOGIC (RELAXED)
        # =========================
        trend_ok = latest["EMA50"] >= latest["EMA200"] * 0.98
        price_ok = latest["Close"] >= latest["EMA50"] * 0.98
        momentum_ok = 40 <= latest["RSI"] <= 70
        volume_ok = latest["Volume"] >= latest["VOL_MED50"] * 0.8
        bandar_ok = latest["Bandar"] != "DISTRIBUSI"

        monthly_score = sum([
            trend_ok * 30,
            price_ok * 20,
            momentum_ok * 20,
            volume_ok * 15,
            bandar_ok * 15
        ])  # max 100

        # =========================
        # AI SCORE (MASTER FILTER)
        # =========================
        ai_score = compute_ai_score(d)

        final_score = int(0.65 * ai_score + 0.35 * monthly_score)

        # =========================
        # ENTRY FILTER
        # =========================
        if final_score >= 60 and bandar_ok:
            rows.append({
                "Mode": "BULANAN",
                "Saham": symbol,
                "Harga": round(latest["Close"], 0),
                "Support": round(latest["Support"], 0),
                "Resistance": round(latest["Resistance"], 0),
                "AI Score": ai_score,
                "Monthly Score": monthly_score,
                "Final Score": final_score,
                "Bandar": latest["Bandar"],
                "Status": "BUY" if final_score >= 75 else "WATCH"
            })

    return (
        pd.DataFrame(rows)
        .sort_values("Final Score", ascending=False)
        .reset_index(drop=True)
        if rows else pd.DataFrame()
    )

# ============================================================
# WATCHLIST ENGINE
# ============================================================

def generate_watchlist(df):
    """
    Watchlist berbasis:
    - Bandar AKUMULASI
    - AI Score >= 50
    """
    rows = []

    for symbol in df["Symbol"].unique():
        d = df[df["Symbol"] == symbol].tail(120)
        score = compute_ai_score(d)
        latest = d.iloc[-1]

        if latest["Bandar"] == "AKUMULASI" and score >= 50:
            rows.append({
                "Saham": symbol,
                "Harga": round(latest["Close"], 0),
                "Support": round(latest["Support"], 0),
                "Resistance": round(latest["Resistance"], 0),
                "AI Score": score
            })

    if not rows:
        return pd.DataFrame()

    return (
        pd.DataFrame(rows)
        .sort_values("AI Score", ascending=False)
        .reset_index(drop=True)
    )

# ============================================================
# HEATMAP CARD ENGINE
# ============================================================

def heatmap_cards(df):
    """
    Card heatmap:
    STRONG BUY | BUY / WATCH | WAIT
    """
    cards = {
        "STRONG BUY": [],
        "BUY / WATCH": [],
        "WAIT": []
    }

    for symbol in df["Symbol"].unique():
        d = df[df["Symbol"] == symbol].tail(120)
        score = compute_ai_score(d)
        latest = d.iloc[-1]

        if latest["Bandar"] == "AKUMULASI" and score >= 75:
            cards["STRONG BUY"].append((symbol, score))
        elif latest["Bandar"] == "AKUMULASI" and score >= 60:
            cards["BUY / WATCH"].append((symbol, score))
        else:
            cards["WAIT"].append((symbol, score))

    return cards

# ============================================================
# HEATMAP MATRIX ENGINE (CONFIDENCE × VOLUME)
# ============================================================

def heatmap_matrix_engine(df):
    """
    Heatmap matrix:
    - X: Confidence (Low / Mid / High)
    - Y: Volume (Low / Mid / High)
    """
    rows = []

    for symbol in df["Symbol"].unique():
        d = df[df["Symbol"] == symbol].tail(120)
        score = compute_ai_score(d)
        latest = d.iloc[-1]

        rows.append({
            "Symbol": symbol,
            "Confidence": score,
            "Volume": latest["Volume"]
        })

    matrix_df = pd.DataFrame(rows)

    if matrix_df.empty:
        return pd.DataFrame()

    matrix_df["Conf_Level"] = pd.qcut(
        matrix_df["Confidence"],
        3,
        labels=["Low", "Mid", "High"]
    )

    matrix_df["Vol_Level"] = pd.qcut(
        matrix_df["Volume"],
        3,
        labels=["Low", "Mid", "High"]
    )

    matrix = pd.crosstab(
        matrix_df["Vol_Level"],
        matrix_df["Conf_Level"]
    )

    return matrix

# ============================================================
# AUTO RANKING ENGINE
# ============================================================

def auto_ranking(df, top_n=5):
    """
    Ranking saham terbaik harian
    """
    rows = []

    for symbol in df["Symbol"].unique():
        d = df[df["Symbol"] == symbol].tail(200)
        score = compute_ai_score(d)
        latest = d.iloc[-1]

        rows.append({
            "Saham": symbol,
            "AI Score": score,
            "Harga": round(latest["Close"], 0),
            "Bandar": latest["Bandar"]
        })

    rank_df = pd.DataFrame(rows)

    rank_df = rank_df[
        (rank_df["Bandar"] == "AKUMULASI") &
        (rank_df["AI Score"] >= 60)
    ]

    return (
        rank_df
        .sort_values("AI Score", ascending=False)
        .head(top_n)
        .reset_index(drop=True)
    )

# ============================================================
# SIDEBAR NAVIGATION (FULL)
# ============================================================

# =========================
# SIDEBAR
# =========================
# =========================
# SIDEBAR
# =========================
st.sidebar.image(
    "assets/logo.png",
    width=200
)

st.sidebar.markdown("## 🧭 Navigasi Sistem")

menu = st.sidebar.radio(
    "Pilih Menu",
    [
        "🏠 Dashboard",
        "📅 Rekomendasi Harian",
        "📊 Swing Mingguan",
        "🗓️ Rekomendasi Bulanan",
        "⭐ Watchlist",
        "📊 Heatmap Matrix",
        "📈 Ranking Harian",
        "🔍 Analisa 1 Saham"
    ]
)

st.sidebar.markdown("---")

st.sidebar.markdown("""
### 📌 SahamAI Enterprise

Platform analisis saham terintegrasi  
untuk **trader & investor aktif**

**Fitur Utama:**
- 📅 Rekomendasi harian, mingguan & bulanan
- 📊 Skoring saham berbasis performa
- 🔥 Heatmap sektor & momentum
- 📈 Ranking saham paling prospektif
- 🔔 Monitoring & evaluasi strategi

> **Keputusan lebih cepat.  
> Risiko lebih terukur.**
""")

# ============================================================
# DASHBOARD UI
# ============================================================

if menu == "🏠 Dashboard":

    # ===============================
    # MARKET OVERVIEW
    # ===============================
    st.markdown("""
    <div class="section-box">
        <h3>📊 Market Overview</h3>
    """, unsafe_allow_html=True)

    st.markdown(
        f"<div class='info-bar'>{market_countdown_text()}</div>",
        unsafe_allow_html=True
    )

    latest_all = df.groupby("Symbol").tail(1)

    c1, c2, c3 = st.columns(3)

    with c1:
        st.markdown(f"""
        <div class="kpi-box">
            <div class="kpi-title">Total Saham</div>
            <div class="kpi-value">{latest_all.shape[0]}</div>
        </div>
        """, unsafe_allow_html=True)

    with c2:
        st.markdown(f"""
        <div class="kpi-box">
            <div class="kpi-title">Akumulasi</div>
            <div class="kpi-value">{(latest_all["Bandar"] == "AKUMULASI").sum()}</div>
        </div>
        """, unsafe_allow_html=True)

    with c3:
        st.markdown(f"""
        <div class="kpi-box">
            <div class="kpi-title">Distribusi</div>
            <div class="kpi-value">{(latest_all["Bandar"] == "DISTRIBUSI").sum()}</div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("</div>", unsafe_allow_html=True)

    # ===============================
    # HEATMAP REKOMENDASI
    # ===============================
    st.markdown("""
    <div class="section-box">
        <h3>🔥 Heatmap Rekomendasi</h3>
    """, unsafe_allow_html=True)

    cards = heatmap_cards(df)

    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown("#### 🟢 STRONG BUY")
        for s, sc in cards["STRONG BUY"][:8]:
            st.markdown(
                f"""
                <div class="card card-strong">
                    {s}<br>
                    <span>Score: {sc}</span>
                </div>
                """,
                unsafe_allow_html=True
            )

    with col2:
        st.markdown("#### 🟩 BUY / WATCH")
        for s, sc in cards["BUY / WATCH"][:8]:
            st.markdown(
                f"""
                <div class="card card-mid">
                    {s}<br>
                    <span>Score: {sc}</span>
                </div>
                """,
                unsafe_allow_html=True
            )

    with col3:
        st.markdown("#### ⚪ WAIT")
        for s, sc in cards["WAIT"][:8]:
            st.markdown(
                f"""
                <div class="card card-low">
                    {s}<br>
                    <span>Score: {sc}</span>
                </div>
                """,
                unsafe_allow_html=True
            )

    st.markdown("</div>", unsafe_allow_html=True)

# ============================================================
# REKOMENDASI HARIAN
# ============================================================

elif menu == "📅 Rekomendasi Harian":

    st.subheader("📅 Rekomendasi Harian (Daily Trading)")

    st.caption("""
    📌 Strategi berbasis **momentum harian**, **volume**, dan **AI Score**  
    Cocok untuk holding **1–5 hari**
    """)

    daily_df = strategy_daily(df)

    # =========================
    # EMPTY STATE (WAJIB)
    # =========================
    if daily_df.empty:
        st.warning("⚠️ Tidak ada saham yang memenuhi kriteria hari ini.")
        st.info("""
        **Kemungkinan penyebab:**
        - Market sedang sideways
        - Volume belum masuk
        - RSI overbought / oversold
        - Bandar distribusi

        👉 Gunakan **Watchlist** atau **Ranking Harian** untuk alternatif.
        """)
    else:
        # =========================
        # KPI RINGKAS
        # =========================
        c1, c2, c3 = st.columns(3)

        c1.metric("Total Kandidat", len(daily_df))
        c2.metric("Rata-rata AI Score", int(daily_df["AI Score"].mean()))
        c3.metric("Rata-rata Final Score", int(daily_df["Final Score"].mean()))

        st.markdown("---")

        # =========================
        # DATAFRAME
        # =========================
        st.dataframe(
            daily_df,
            use_container_width=True,
            hide_index=True
        )

        # =========================
        # KETERANGAN STATUS
        # =========================
        st.caption("""
        **Keterangan Status:**
        - 🟢 **BUY** → momentum kuat + konfirmasi AI
        - 🟡 **WATCH** → momentum ada, tunggu pullback
        """)

# ============================================================
# SWING MINGGUAN
# ============================================================

elif menu == "📊 Swing Mingguan":
    st.subheader("📊 Swing Mingguan")

    weekly_df = strategy_weekly(df)

    if weekly_df.empty:
        st.warning("⚠️ Belum ada saham yang memenuhi kriteria Swing Mingguan.")
        st.info("""
        **Kemungkinan penyebab:**
        - Data historis belum cukup panjang
        - AI Score belum mencapai threshold
        - Bandar belum terdeteksi AKUMULASI

        👉 Coba:
        - Turunkan threshold AI
        - Gunakan Watchlist / Ranking Harian
        """)
    else:
        st.dataframe(weekly_df, use_container_width=True)


# ============================================================
# BULANAN
# ============================================================

elif menu == "🗓️ Rekomendasi Bulanan":

    st.subheader("🗓️ Rekomendasi Bulanan (Position Trading)")

    st.caption("""
    📌 Strategi **position trading** berbasis **trend jangka panjang**,  
    **akumulasi bandar**, dan **AI Score tinggi**  
    Cocok untuk holding **1–6 bulan**
    """)

    monthly_df = strategy_monthly(df)

    # =========================
    # EMPTY STATE
    # =========================
    if monthly_df.empty:
        st.warning("⚠️ Belum ada saham dengan setup bulanan ideal.")
        st.info("""
        **Penyebab umum:**
        - Trend besar belum terbentuk
        - Bandar masih distribusi
        - Harga masih di area konsolidasi

        👉 Gunakan **Watchlist** untuk observasi lebih awal.
        """)
    else:
        # =========================
        # KPI RINGKAS
        # =========================
        c1, c2, c3 = st.columns(3)

        c1.metric("Total Kandidat", len(monthly_df))
        c2.metric("AI Score Tertinggi", monthly_df["AI Score"].max())
        c3.metric("Rata-rata AI Score", int(monthly_df["AI Score"].mean()))

        st.markdown("---")

        # =========================
        # DATA UTAMA
        # =========================
        st.dataframe(
            monthly_df,
            use_container_width=True,
            hide_index=True
        )

        # =========================
        # PRIORITAS HOLD
        # =========================
        strong_df = monthly_df[monthly_df["Status"] == "BUY"]

        if not strong_df.empty:
            st.markdown("### 🟢 Prioritas Hold Bulanan")
            st.dataframe(strong_df, use_container_width=True)

        # =========================
        # CATATAN STRATEGI
        # =========================
        st.caption("""
        **Catatan:**
        - 🟢 **BUY** → trend mayor + akumulasi kuat
        - 🟡 **WATCH** → valid tapi tunggu konfirmasi breakout
        - Disarankan **evaluasi ulang setiap akhir bulan**
        """)

# ============================================================
# WATCHLIST
# ============================================================

elif menu == "⭐ Watchlist":
    st.subheader("⭐ Watchlist Akumulasi")
    wl = generate_watchlist(df)
    st.dataframe(wl, use_container_width=True)

# ============================================================
# HEATMAP MATRIX UI
# ============================================================

elif menu == "📊 Heatmap Matrix":
    st.subheader("📊 Heatmap Matrix (Confidence × Volume)")
    matrix = heatmap_matrix_engine(df)
    st.dataframe(matrix, use_container_width=True)

# ============================================================
# RANKING UI
# ============================================================

elif menu == "🤖 Ranking Harian":
    st.subheader("🤖 Top Saham Hari Ini")
    rank = auto_ranking(df, top_n=10)
    st.dataframe(rank, use_container_width=True)

# ============================================================
# ===== STOP PART 2 ======
# NEXT: BACKTEST • ALERT • ANALISA DETAIL • FOOTER
# ============================================================
# ============================================================
# BACKTEST ENGINE (TP / SL REAL)
# ============================================================

def backtest_tp_sl(
    df,
    tp_pct=0.07,
    sl_pct=0.05,
    holding_days=10
):
    """
    Backtest sederhana:
    - Entry di close
    - Cek TP / SL dalam N hari ke depan
    """
    results = []

    for symbol in df["Symbol"].unique():
        d = (
            df[df["Symbol"] == symbol]
            .sort_values("Tanggal Perdagangan Terakhir")
            .reset_index(drop=True)
        )

        for i in range(len(d) - holding_days - 1):
            entry_price = d.loc[i, "Close"]
            future = d.loc[i+1:i+holding_days]

            hit_tp = future["High"].max() >= entry_price * (1 + tp_pct)
            hit_sl = future["Low"].min() <= entry_price * (1 - sl_pct)

            if hit_tp and not hit_sl:
                results.append(1)
            elif hit_sl and not hit_tp:
                results.append(0)
            elif hit_tp and hit_sl:
                # konservatif: SL dianggap kena dulu
                results.append(0)

    if not results:
        return {
            "total_trade": 0,
            "winrate": 0
        }

    return {
        "total_trade": len(results),
        "winrate": round(sum(results) / len(results) * 100, 2)
    }

# ============================================================
# ALERT ENGINE (TELEGRAM – SAFE MODE)
# ============================================================

def send_telegram_alert(message):
    """
    Telegram alert (tidak crash jika token kosong)
    """
    TOKEN = os.getenv("TELEGRAM_TOKEN")
    CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

    if not TOKEN or not CHAT_ID:
        return

    try:
        url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
        requests.get(
            url,
            params={
                "chat_id": CHAT_ID,
                "text": message
            },
            timeout=5
        )
    except Exception:
        pass

def auto_alert_scheduler(df):
    """
    Auto alert jam 08:45
    """
    now = datetime.now().time()

    if time(8, 45) <= now <= time(8, 46):
        rank = auto_ranking(df, top_n=5)
        if rank.empty:
            return

        msg = (
            f"SahamAI Enterprise Alert\n"
            f"Tanggal: {date.today()}\n\n"
        )

        for i, r in enumerate(rank.itertuples(), 1):
            msg += f"{i}. {r.Saham} | AI Score {r._2}\n"

        send_telegram_alert(msg)

# ============================================================
# ANALISA 1 SAHAM (DETAIL VIEW)
# ============================================================

    elif menu == "🔍 Analisa 1 Saham":

        st.subheader("🔍 Analisa Detail Saham")

    symbol = st.selectbox(
        "Pilih Saham",
        sorted(df["Symbol"].unique())
    )

    df_s = (
        df[df["Symbol"] == symbol]
        .sort_values("Tanggal Perdagangan Terakhir")
        .tail(250)
    )

    # =====================
    # METRICS
    # =====================
    ai = compute_ai_score(df_s)
    latest = df_s.iloc[-1]

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Harga", f"{latest['Close']:.0f}")
    c2.metric("Bandar", latest["Bandar"])
    c3.metric("AI Score", ai)
    c4.metric("Volume", f"{latest['Volume']:,}")

    # =====================
    # SIGNAL BOX
    # =====================
    if ai >= 75 and latest["Bandar"] == "AKUMULASI":
        st.markdown(
            f"<div class='card card-strong'>"
            f"🟢 STRONG BUY<br>"
            f"Entry: {latest['Close']:.0f}<br>"
            f"Target: {(latest['Close']*1.07):.0f}<br>"
            f"Stoploss: {(latest['Close']*0.95):.0f}"
            f"</div>",
            unsafe_allow_html=True
        )
    elif ai >= 60:
        st.markdown(
            f"<div class='card card-mid'>🟩 BUY / WATCH</div>",
            unsafe_allow_html=True
        )
    else:
        st.markdown(
            f"<div class='card card-low'>⚪ WAIT</div>",
            unsafe_allow_html=True
        )

    # =====================
    # CANDLESTICK CHART
    # =====================
    st.markdown("### 📈 Grafik Candlestick")

    df_chart = df_s.set_index("Tanggal Perdagangan Terakhir")

    fig, _ = mpf.plot(
        df_chart,
        type="candle",
        style="yahoo",
        volume=True,
        mav=(20, 50),
        returnfig=True,
        figsize=(16, 8),
        title=symbol
    )
    st.pyplot(fig)

# ============================================================
# AUTO BACKTEST & ALERT EXECUTION
# ============================================================

    if menu == "🏠 Dashboard":
        # Auto alert only from dashboard
        auto_alert_scheduler(df)

# ============================================================
# BACKTEST UI (APPENDED TO DASHBOARD)
# ============================================================

    if menu == "🏠 Dashboard":

        st.markdown("---")
        st.subheader("📈 Backtest Statistik Sistem")

        result = backtest_tp_sl(
            df,
            tp_pct=0.07,
            sl_pct=0.05,
            holding_days=10
        )

        c1, c2 = st.columns(2)
        c1.metric("Total Trade", result["total_trade"])
        c2.metric("Winrate (%)", result["winrate"])

# ============================================================
# FOOTER
# ============================================================

    st.markdown("""
    ---
    © 2026 **SahamAI Enterprise**  
    Green • Quant • IDX • AI Powered
    """)