import streamlit as st
import pandas as pd
import numpy as np
import mplfinance as mpf
import os
import requests

from datetime import datetime, date, time

st.set_page_config(
    page_title="SahamAI Enterprise | IDX Trading System",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

if os.path.exists("assets/style.css"):
    with open("assets/style.css") as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

st.markdown("""
<div class="app-header">
  <div class="app-header-left">
    <div class="app-badge">📊 AI SYSTEM</div>
    <div class="app-title">SahamAI Enterprise</div>
    <div class="app-subtitle">
      Daily • Weekly • Monthly • Heatmap • AI Score
    </div>
  </div>
</div>
<hr class="app-divider">
""", unsafe_allow_html=True)

DATA_PATH = "processed/daily_clean.parquet"

ML_DAILY_PATH   = "processed/ml_confidence_label_daily.parquet"
ML_WEEKLY_PATH  = "processed/ml_confidence_label_weekly.parquet"
ML_MONTHLY_PATH = "processed/ml_confidence_label_monthly.parquet"

@st.cache_data(show_spinner=False)
def load_data():
    if not os.path.exists(DATA_PATH):
        st.error("❌ Data utama tidak ditemukan")
        st.stop()
    return pd.read_parquet(DATA_PATH)

df = load_data()

def merge_ml(df, path, col):
    if os.path.exists(path):
        ml = pd.read_parquet(path)
        df = df.merge(
            ml,
            on=["Symbol", "Tanggal Perdagangan Terakhir"],
            how="left"
        )
    else:
        df[col] = np.nan
    return df

df = merge_ml(df, ML_DAILY_PATH,   "ml_confidence_label_daily")
df = merge_ml(df, ML_WEEKLY_PATH,  "ml_confidence_label_weekly")
df = merge_ml(df, ML_MONTHLY_PATH, "ml_confidence_label_monthly")

for c in [
    "ml_confidence_label_daily",
    "ml_confidence_label_weekly",
    "ml_confidence_label_monthly"
]:
    if c not in df.columns:
        df[c] = np.nan

LATEST_SYMBOLS = (
    df.sort_values("Tanggal Perdagangan Terakhir")
      .groupby("Symbol")
      .tail(1)["Symbol"]
      .tolist()
)

@st.cache_data(show_spinner=False)
def build_symbol_map(df):
    """
    Akses data saham O(1)
    Menghilangkan df[df['Symbol']==...] di loop
    """
    return {
        symbol: g.sort_values("Tanggal Perdagangan Terakhir")
        for symbol, g in df.groupby("Symbol")
    }

SYMBOL_MAP = build_symbol_map(df)

def market_open_status():
    now = datetime.now()
    open_t  = datetime.combine(date.today(), time(9, 0))
    close_t = datetime.combine(date.today(), time(15, 0))

    if now < open_t:
        return "PREOPEN", open_t - now
    elif open_t <= now <= close_t:
        return "OPEN", None
    else:
        return "CLOSED", None

def market_countdown_text():
    status, delta = market_open_status()
    if status == "PREOPEN":
        return f"⏰ Market Open dalam {str(delta).split('.')[0]}"
    if status == "OPEN":
        return "🟢 Market Sedang Buka"
    return "🔴 Market Tutup"

def compute_rsi(series, period=14):
    delta = series.diff()
    gain  = delta.clip(lower=0)
    loss  = -delta.clip(upper=0)
    avg_gain = gain.rolling(period).mean()
    avg_loss = loss.rolling(period).mean()
    rs = avg_gain / avg_loss
    return 100 - (100 / (1 + rs))

def compute_ema(series, span):
    return series.ewm(span=span, adjust=False).mean()

def compute_volume_spike(volume, window=20):
    med = volume.rolling(window).median()
    return volume / med

def bandar_score(status):
    if status == "AKUMULASI":
        return 40
    if status == "DISTRIBUSI":
        return -20
    return 0

def compute_ai_score(df_s):
    if df_s is None or df_s.empty:
        return 0

    d = df_s.copy()

    d["EMA20"] = compute_ema(d["Close"], 20)
    d["EMA50"] = compute_ema(d["Close"], 50)
    d["RSI"]   = compute_rsi(d["Close"])
    d["VOL_SPIKE"] = compute_volume_spike(d["Volume"])

    latest = d.iloc[-1]
    score = 0

    score += bandar_score(latest.get("Bandar"))

    if latest["EMA20"] > latest["EMA50"]:
        score += 25

    if latest["RSI"] < 70:
        score += 20
    elif latest["RSI"] > 80:
        score -= 10

    if latest["VOL_SPIKE"] > 1.2:
        score += 15

    return int(min(max(score, 0), 100))


@st.cache_data(show_spinner=False)
def build_ai_score_map(symbol_map):
    score_map = {}
    for symbol, d_all in symbol_map.items():
        d = d_all.tail(200)
        score_map[symbol] = compute_ai_score(d)
    return score_map

AI_SCORE_MAP = build_ai_score_map(SYMBOL_MAP)


def ml_decision(conf, high=0.70, mid=0.55):
    if pd.isna(conf):
        return "NO_ML"
    if conf >= high:
        return "BUY_ML"
    if conf >= mid:
        return "WATCH_ML"
    return "WAIT_ML"


def strategy_daily():
    rows = []

    for symbol in LATEST_SYMBOLS:
        d_all = SYMBOL_MAP.get(symbol)
        if d_all is None:
            continue

        d = d_all.tail(30)
        if len(d) < 15:
            continue

        d = d.copy()
        d["EMA10"] = compute_ema(d["Close"], 10)
        d["EMA20"] = compute_ema(d["Close"], 20)
        d["RSI"]   = compute_rsi(d["Close"])
        d["VOL_MED20"] = d["Volume"].rolling(20).median()

        latest = d.iloc[-1]

        daily_score = (
            (latest["EMA10"] > latest["EMA20"]) * 30 +
            (45 <= latest["RSI"] <= 70) * 25 +
            (latest["Volume"] > latest["VOL_MED20"]) * 25 +
            (latest["Close"] > latest["EMA10"]) * 20
        )

        ai_score = AI_SCORE_MAP.get(symbol, 0)
        final_score = int(0.6 * ai_score + 0.4 * daily_score)

        if final_score >= 60 and latest["Bandar"] != "DISTRIBUSI":
            ml_conf = latest.get("ml_confidence_label_daily", np.nan)
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
                "ML Confidence": round(ml_conf, 3) if not pd.isna(ml_conf) else None,
                "ML Signal": ml_decision(ml_conf),
                "Status": "BUY" if final_score >= 75 else "WATCH"
            })

    return (
        pd.DataFrame(rows)
        .sort_values("Final Score", ascending=False)
        .reset_index(drop=True)
        if rows else pd.DataFrame()
    )


def strategy_weekly():
    rows = []

    for symbol in LATEST_SYMBOLS:
        d_all = SYMBOL_MAP.get(symbol)
        if d_all is None:
            continue

        d = d_all.tail(120)
        if len(d) < 50:
            continue

        latest = d.iloc[-1]
        ai_score = AI_SCORE_MAP.get(symbol, 0)
        ml_conf = latest.get("ml_confidence_label_weekly", np.nan)

        if ai_score >= 60 and ml_decision(ml_conf) != "WAIT_ML":
            rows.append({
                "Mode": "MINGGUAN",
                "Saham": symbol,
                "Harga": round(latest["Close"], 0),
                "Support": round(latest["Support"], 0),
                "Resistance": round(latest["Resistance"], 0),
                "AI Score": ai_score,
                "Bandar": latest["Bandar"],
                "ML Confidence": round(ml_conf, 3) if not pd.isna(ml_conf) else None,
                "ML Signal": ml_decision(ml_conf),
                "Status": "BUY" if ai_score >= 75 else "WATCH"
            })

    return (
        pd.DataFrame(rows)
        .sort_values("AI Score", ascending=False)
        .reset_index(drop=True)
        if rows else pd.DataFrame()
    )


def strategy_monthly():
    rows = []

    for symbol in LATEST_SYMBOLS:
        d_all = SYMBOL_MAP.get(symbol)
        if d_all is None:
            continue

        d = d_all.tail(250)
        if len(d) < 100:
            continue

        d = d.copy()
        d["EMA50"]  = compute_ema(d["Close"], 50)
        d["EMA200"] = compute_ema(d["Close"], 200)
        d["RSI"]    = compute_rsi(d["Close"])
        d["VOL_MED50"] = d["Volume"].rolling(50).median()

        latest = d.iloc[-1]

        monthly_score = (
            (latest["EMA50"] >= latest["EMA200"] * 0.98) * 30 +
            (latest["Close"] >= latest["EMA50"] * 0.98) * 20 +
            (40 <= latest["RSI"] <= 70) * 20 +
            (latest["Volume"] >= latest["VOL_MED50"] * 0.8) * 15 +
            (latest["Bandar"] != "DISTRIBUSI") * 15
        )

        ai_score = AI_SCORE_MAP.get(symbol, 0)
        final_score = int(0.65 * ai_score + 0.35 * monthly_score)

        ml_conf = latest.get("ml_confidence_label_monthly", np.nan)

        if final_score >= 60 and ml_decision(ml_conf, 0.65, 0.50) != "WAIT_ML":
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
                "ML Confidence": round(ml_conf, 3) if not pd.isna(ml_conf) else None,
                "ML Signal": ml_decision(ml_conf, 0.65, 0.50),
                "Status": "BUY" if final_score >= 75 else "WATCH"
            })

    return (
        pd.DataFrame(rows)
        .sort_values("Final Score", ascending=False)
        .reset_index(drop=True)
        if rows else pd.DataFrame()
    )


def generate_watchlist():
    rows = []
    for symbol in LATEST_SYMBOLS:
        d_all = SYMBOL_MAP.get(symbol)
        if d_all is None:
            continue

        d = d_all.tail(120)
        if d.empty:
            continue

        latest = d.iloc[-1]
        ai_score = AI_SCORE_MAP.get(symbol, 0)

        if latest["Bandar"] == "AKUMULASI" and ai_score >= 50:
            rows.append({
                "Saham": symbol,
                "Harga": round(latest["Close"], 0),
                "Support": round(latest["Support"], 0),
                "Resistance": round(latest["Resistance"], 0),
                "AI Score": ai_score
            })

    return (
        pd.DataFrame(rows)
        .sort_values("AI Score", ascending=False)
        .reset_index(drop=True)
        if rows else pd.DataFrame()
    )


def heatmap_matrix_engine():
    rows = []
    for symbol in LATEST_SYMBOLS:
        d_all = SYMBOL_MAP.get(symbol)
        if d_all is None:
            continue

        latest = d_all.iloc[-1]
        rows.append({
            "Symbol": symbol,
            "Confidence": AI_SCORE_MAP.get(symbol, 0),
            "Volume": latest["Volume"]
        })

    dfm = pd.DataFrame(rows)
    if dfm.empty:
        return pd.DataFrame()

    dfm["Conf_Level"] = pd.qcut(dfm["Confidence"], 3, labels=["Low", "Mid", "High"])
    dfm["Vol_Level"]  = pd.qcut(dfm["Volume"], 3, labels=["Low", "Mid", "High"])

    return pd.crosstab(dfm["Vol_Level"], dfm["Conf_Level"])


def auto_ranking(top_n=10):
    rows = []
    for symbol in LATEST_SYMBOLS:
        d_all = SYMBOL_MAP.get(symbol)
        if d_all is None:
            continue

        latest = d_all.iloc[-1]
        ai_score = AI_SCORE_MAP.get(symbol, 0)

        rows.append({
            "Saham": symbol,
            "AI Score": ai_score,
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

@st.cache_data(show_spinner=False)
def cached_daily():
    return strategy_daily()

@st.cache_data(show_spinner=False)
def cached_weekly():
    return strategy_weekly()

@st.cache_data(show_spinner=False)
def cached_monthly():
    return strategy_monthly()

@st.cache_data(show_spinner=False)
def cached_watchlist():
    return generate_watchlist()

@st.cache_data(show_spinner=False)
def cached_heatmap_matrix():
    return heatmap_matrix_engine()

@st.cache_data(show_spinner=False)
def cached_ranking(top_n=10):
    return auto_ranking(top_n)

st.sidebar.markdown("<div class='sidebar-logo-wrapper'>", unsafe_allow_html=True)
if os.path.exists("assets/logo.png"):
    st.sidebar.image("assets/logo.png", width=290)
st.sidebar.markdown("</div>", unsafe_allow_html=True)
st.sidebar.markdown("<div class='sidebar-logo-divider'></div>", unsafe_allow_html=True)

st.sidebar.markdown("### 🧭 Navigasi")

menu = st.sidebar.radio(
    "Menu Utama",
    [
        "🏠 Dashboard",
        "📅 Rekomendasi Harian",
        "📊 Swing Mingguan",
        "🗓️ Rekomendasi Bulanan",
        "⭐ Watchlist",
        "📊 Heatmap Matrix",
        "🤖 Ranking Harian",
        "🔍 Analisa 1 Saham",
    ],
    index=0
)

st.sidebar.markdown(
    "<hr style='border:0;border-top:1px solid rgba(255,255,255,0.15);margin:14px 0;'>",
    unsafe_allow_html=True
)

st.sidebar.markdown("### 🎛️ Filter Tampilan")

selected_timeframe = st.sidebar.selectbox(
    "⏱ Timeframe",
    ["Daily", "Weekly", "Monthly"],
    index=0
)

selected_limit = st.sidebar.slider(
    "🔢 Jumlah Saham Ditampilkan",
    5, 50, 10, 5
)

st.sidebar.markdown(
    "<hr style='border:0;border-top:1px solid rgba(255,255,255,0.15);margin:14px 0;'>",
    unsafe_allow_html=True
)

st.sidebar.markdown("""
**SahamAI Enterprise**  
📊 *AI-powered IDX analytics*

⚠️ Bukan ajakan beli / jual  
Gunakan sebagai alat bantu analisis
""")

def heatmap_cards():
    cards = {"STRONG BUY": [], "BUY / WATCH": [], "WAIT": []}

    for symbol, d in SYMBOL_MAP.items():
        if len(d) < 30:
            continue

        latest = d.iloc[-1]
        ai = AI_SCORE_MAP.get(symbol, 0)

        ml_conf = (
            latest.get("ml_confidence_label_daily")
            if not pd.isna(latest.get("ml_confidence_label_daily"))
            else latest.get("ml_confidence_label_weekly")
            if not pd.isna(latest.get("ml_confidence_label_weekly"))
            else latest.get("ml_confidence_label_monthly")
        )

        if latest["Bandar"] == "AKUMULASI" and ai >= 75:
            cards["STRONG BUY"].append((symbol, ai, ml_conf))
        elif latest["Bandar"] == "AKUMULASI" and ai >= 60:
            cards["BUY / WATCH"].append((symbol, ai, ml_conf))
        else:
            cards["WAIT"].append((symbol, ai, ml_conf))

    return cards

if menu == "🏠 Dashboard":

    st.markdown("<div class='section-box'>", unsafe_allow_html=True)
    st.markdown("### 📊 Market Overview")

    st.markdown(
        f"<div class='info-bar'>{market_countdown_text()}</div>",
        unsafe_allow_html=True
    )

    latest_all = df.groupby("Symbol").tail(1)

    c1, c2, c3 = st.columns(3)
    c1.metric("Total Saham", len(latest_all))
    c2.metric("Akumulasi", (latest_all["Bandar"] == "AKUMULASI").sum())
    c3.metric("Distribusi", (latest_all["Bandar"] == "DISTRIBUSI").sum())

    st.markdown("</div>", unsafe_allow_html=True)

    # =========================
    # HEATMAP
    # =========================

    st.markdown("<div class='section-box'>", unsafe_allow_html=True)
    st.markdown("### 🔥 Heatmap Rekomendasi")

    cards = heatmap_cards()
    col1, col2, col3 = st.columns(3)

    def ml_txt(v): 
        return f"{v:.2f}" if isinstance(v, (int, float)) else "NA"

    with col1:
        st.markdown("### 🟢 STRONG BUY")
        for s, sc, ml in cards["STRONG BUY"][:8]:
            st.markdown(
                f"<div class='card card-strong'><b>{s}</b><br>AI: {sc} | ML: {ml_txt(ml)}</div>",
                unsafe_allow_html=True
            )

    with col2:
        st.markdown("### 🟩 BUY / WATCH")
        for s, sc, ml in cards["BUY / WATCH"][:8]:
            st.markdown(
                f"<div class='card card-mid'><b>{s}</b><br>AI: {sc} | ML: {ml_txt(ml)}</div>",
                unsafe_allow_html=True
            )

    with col3:
        st.markdown("### ⚪ WAIT")
        for s, sc, ml in cards["WAIT"][:8]:
            st.markdown(
                f"<div class='card card-low'><b>{s}</b><br>AI: {sc} | ML: {ml_txt(ml)}</div>",
                unsafe_allow_html=True
            )

    st.markdown("</div>", unsafe_allow_html=True)

elif menu == "📅 Rekomendasi Harian":
    st.subheader("📅 Rekomendasi Harian")
    df_daily = cached_daily()
    st.dataframe(df_daily.head(selected_limit), use_container_width=True)

elif menu == "📊 Swing Mingguan":
    st.subheader("📊 Swing Mingguan")
    df_weekly = cached_weekly()
    st.dataframe(df_weekly.head(selected_limit), use_container_width=True)

elif menu == "🗓️ Rekomendasi Bulanan":
    st.subheader("🗓️ Rekomendasi Bulanan")
    df_monthly = cached_monthly()
    st.dataframe(df_monthly.head(selected_limit), use_container_width=True)

elif menu == "⭐ Watchlist":
    st.subheader("⭐ Watchlist Akumulasi")
    wl = cached_watchlist()
    st.dataframe(wl.head(selected_limit), use_container_width=True)

elif menu == "📊 Heatmap Matrix":
    st.subheader("📊 Heatmap Matrix")
    matrix = cached_heatmap_matrix()
    st.dataframe(matrix, use_container_width=True)

elif menu == "🤖 Ranking Harian":
    st.subheader("🤖 Ranking Harian")
    rank = cached_ranking(selected_limit)
    st.dataframe(rank, use_container_width=True)

elif menu == "🔍 Analisa 1 Saham":

    symbol = st.selectbox("Pilih Saham", sorted(SYMBOL_MAP.keys()))
    d = SYMBOL_MAP[symbol].tail(250)

    ai = AI_SCORE_MAP.get(symbol, 0)
    latest = d.iloc[-1]

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Harga", f"{latest['Close']:.0f}")
    c2.metric("Bandar", latest["Bandar"])
    c3.metric("AI Score", ai)
    c4.metric("Volume", f"{latest['Volume']:,}")

    st.markdown("### 📈 Grafik Candlestick")

    chart_df = d.set_index("Tanggal Perdagangan Terakhir")
    fig, _ = mpf.plot(
        chart_df,
        type="candle",
        volume=True,
        mav=(20, 50),
        returnfig=True,
        figsize=(16, 8)
    )
    st.pyplot(fig)

st.markdown("""
---
© 2026 **SahamAI Enterprise**  
Green • Quant • IDX • AI Powered
""")