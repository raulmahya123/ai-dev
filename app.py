# =====================================================
# SAHAMAI ENTERPRISE
# PART 1 — FOUNDATION & DATA PIPELINE
# =====================================================

import streamlit as st
import pandas as pd
import numpy as np
import mplfinance as mpf
import os
import requests

from datetime import datetime, date, time

# =====================================================
# PAGE CONFIG
# =====================================================
st.set_page_config(
    page_title="SahamAI Enterprise | IDX Trading System",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# =====================================================
# LOAD STYLE
# =====================================================
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

# =====================================================
# PATH CONFIG
# =====================================================
DATA_PATH = "processed/daily_clean.parquet"

ML_DAILY_PATH   = "processed/ml_confidence_label_daily.parquet"
ML_WEEKLY_PATH  = "processed/ml_confidence_label_weekly.parquet"
ML_MONTHLY_PATH = "processed/ml_confidence_label_monthly.parquet"

# WALK-FORWARD RESULT (LIGHTGBM)
WF_PATH = "processed/walk_forward_result_weekly.parquet"

# =====================================================
# LOAD MAIN DATA
# =====================================================
@st.cache_data(show_spinner=False)
def load_data():
    if not os.path.exists(DATA_PATH):
        st.error("❌ daily_clean.parquet tidak ditemukan")
        st.stop()
    return pd.read_parquet(DATA_PATH)

df = load_data()

# =====================================================
# MERGE ML CONFIDENCE
# =====================================================
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

# =====================================================
# SYMBOL LIST
# =====================================================
LATEST_SYMBOLS = (
    df.sort_values("Tanggal Perdagangan Terakhir")
      .groupby("Symbol")
      .tail(1)["Symbol"]
      .tolist()
)

# =====================================================
# SYMBOL MAP (O(1) ACCESS)
# =====================================================
@st.cache_data(show_spinner=False)
def build_symbol_map(df):
    return {
        symbol: g.sort_values("Tanggal Perdagangan Terakhir")
        for symbol, g in df.groupby("Symbol")
    }

SYMBOL_MAP = build_symbol_map(df)

# =====================================================
# LOAD WALK-FORWARD META (PnL AWARE)
# =====================================================
@st.cache_data(show_spinner=False)
def load_wf_meta():
    default = {
        "threshold": 0.65,
        "precision": 0.0,
        "winrate": 0.0,
        "avg_pnl": 0.0,
        "trades": 0
    }

    if not os.path.exists(WF_PATH):
        return default

    wf = pd.read_parquet(WF_PATH)
    if wf.empty:
        return default

    last = wf.sort_values("test_end").iloc[-1]

    return {
        "threshold": float(last["threshold"]),
        "precision": float(last["precision"]),
        "winrate": float(last["winrate"]),
        "avg_pnl": float(last["avg_pnl"]),
        "trades": int(last["trades"])
    }

WF_META = load_wf_meta()
# =====================================================
# SAHAMAI ENTERPRISE
# PART 1 — FOUNDATION & DATA PIPELINE
# =====================================================

import streamlit as st
import pandas as pd
import numpy as np
import mplfinance as mpf
import os
import requests

from datetime import datetime, date, time

# =====================================================
# PAGE CONFIG
# =====================================================
st.set_page_config(
    page_title="SahamAI Enterprise | IDX Trading System",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# =====================================================
# LOAD STYLE
# =====================================================
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

# =====================================================
# PATH CONFIG
# =====================================================
DATA_PATH = "processed/daily_clean.parquet"

ML_DAILY_PATH   = "processed/ml_confidence_label_daily.parquet"
ML_WEEKLY_PATH  = "processed/ml_confidence_label_weekly.parquet"
ML_MONTHLY_PATH = "processed/ml_confidence_label_monthly.parquet"

# WALK-FORWARD RESULT (LIGHTGBM)
WF_PATH = "processed/walk_forward_result_weekly.parquet"

# =====================================================
# LOAD MAIN DATA
# =====================================================
@st.cache_data(show_spinner=False)
def load_data():
    if not os.path.exists(DATA_PATH):
        st.error("❌ daily_clean.parquet tidak ditemukan")
        st.stop()
    return pd.read_parquet(DATA_PATH)

df = load_data()

# =====================================================
# MERGE ML CONFIDENCE
# =====================================================
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

# =====================================================
# SYMBOL LIST
# =====================================================
LATEST_SYMBOLS = (
    df.sort_values("Tanggal Perdagangan Terakhir")
      .groupby("Symbol")
      .tail(1)["Symbol"]
      .tolist()
)

# =====================================================
# SYMBOL MAP (O(1) ACCESS)
# =====================================================
@st.cache_data(show_spinner=False)
def build_symbol_map(df):
    return {
        symbol: g.sort_values("Tanggal Perdagangan Terakhir")
        for symbol, g in df.groupby("Symbol")
    }

SYMBOL_MAP = build_symbol_map(df)

# =====================================================
# LOAD WALK-FORWARD META (PnL AWARE)
# =====================================================
@st.cache_data(show_spinner=False)
def load_wf_meta():
    default = {
        "threshold": 0.65,
        "precision": 0.0,
        "winrate": 0.0,
        "avg_pnl": 0.0,
        "trades": 0
    }

    if not os.path.exists(WF_PATH):
        return default

    wf = pd.read_parquet(WF_PATH)
    if wf.empty:
        return default

    last = wf.sort_values("test_end").iloc[-1]

    return {
        "threshold": float(last["threshold"]),
        "precision": float(last["precision"]),
        "winrate": float(last["winrate"]),
        "avg_pnl": float(last["avg_pnl"]),
        "trades": int(last["trades"])
    }

WF_META = load_wf_meta()
# =====================================================
# PART 3 — STRATEGY ENGINE
# =====================================================

# =====================================================
# STRATEGY DAILY — CLASSIC (ASLI)
# =====================================================
def strategy_daily():
    rows = []

    for symbol in LATEST_SYMBOLS:
        d_all = SYMBOL_MAP.get(symbol)
        if d_all is None or len(d_all) < 30:
            continue

        d = d_all.tail(30).copy()
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


# =====================================================
# STRATEGY WEEKLY — CLASSIC
# =====================================================
def strategy_weekly():
    rows = []

    for symbol in LATEST_SYMBOLS:
        d_all = SYMBOL_MAP.get(symbol)
        if d_all is None or len(d_all) < 120:
            continue

        latest = d_all.iloc[-1]
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


# =====================================================
# STRATEGY MONTHLY — CLASSIC
# =====================================================
def strategy_monthly():
    rows = []

    for symbol in LATEST_SYMBOLS:
        d_all = SYMBOL_MAP.get(symbol)
        if d_all is None or len(d_all) < 250:
            continue

        d = d_all.tail(250).copy()
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


# =====================================================
# 🔥 STRATEGY V2 — AI PRO (WALK-FORWARD AWARE)
# =====================================================
def strategy_v2(mode="daily"):
    rows = []

    for symbol in LATEST_SYMBOLS:
        d = SYMBOL_MAP.get(symbol)
        if d is None:
            continue

        # data sufficiency
        if mode == "daily" and len(d) < 40:
            continue
        if mode == "weekly" and len(d) < 150:
            continue
        if mode == "monthly" and len(d) < 300:
            continue

        latest = d.iloc[-1]
        ai = AI_SCORE_MAP.get(symbol, 0)

        ml_conf = latest.get(
            f"ml_confidence_label_{mode}",
            np.nan
        )

        ml_sig = ml_decision_v2(ml_conf, mode)
        decision = final_decision_engine(
            ai_score=ai,
            ml_signal=ml_sig,
            bandar=latest["Bandar"]
        )

        if decision == "WAIT":
            continue

        rows.append({
            "Mode": mode.upper() + "_V2",
            "Saham": symbol,
            "Harga": round(latest["Close"], 0),
            "Support": round(latest["Support"], 0),
            "Resistance": round(latest["Resistance"], 0),
            "AI Score": ai,
            "ML Confidence": round(ml_conf, 3) if not pd.isna(ml_conf) else None,
            "ML Signal": ml_sig,
            "Bandar": latest["Bandar"],
            "Decision": decision
        })

    return (
        pd.DataFrame(rows)
        .sort_values(["Decision", "AI Score"], ascending=False)
        .reset_index(drop=True)
        if rows else pd.DataFrame()
    )
# =====================================================
# PART 4 — WATCHLIST, HEATMAP, RANKING
# =====================================================

# =====================================================
# WATCHLIST — CLASSIC (ASLI)
# =====================================================
def generate_watchlist():
    rows = []

    for symbol in LATEST_SYMBOLS:
        d = SYMBOL_MAP.get(symbol)
        if d is None or len(d) < 120:
            continue

        latest = d.iloc[-1]
        ai = AI_SCORE_MAP.get(symbol, 0)

        if latest["Bandar"] == "AKUMULASI" and ai >= 50:
            rows.append({
                "Saham": symbol,
                "Harga": round(latest["Close"], 0),
                "Support": round(latest["Support"], 0),
                "Resistance": round(latest["Resistance"], 0),
                "AI Score": ai
            })

    return (
        pd.DataFrame(rows)
        .sort_values("AI Score", ascending=False)
        .reset_index(drop=True)
        if rows else pd.DataFrame()
    )


# =====================================================
# 🔥 WATCHLIST V2 — AI PRO (DECISION BASED)
# =====================================================
def generate_watchlist_v2():
    rows = []

    for symbol in LATEST_SYMBOLS:
        d = SYMBOL_MAP.get(symbol)
        if d is None or len(d) < 120:
            continue

        latest = d.iloc[-1]
        ai = AI_SCORE_MAP.get(symbol, 0)

        ml_conf = (
            latest.get("ml_confidence_label_daily")
            if not pd.isna(latest.get("ml_confidence_label_daily"))
            else latest.get("ml_confidence_label_weekly")
        )

        ml_sig = ml_decision_v2(ml_conf, mode="daily")
        decision = final_decision_engine(
            ai_score=ai,
            ml_signal=ml_sig,
            bandar=latest["Bandar"]
        )

        if decision in ["BUY", "STRONG_BUY"]:
            rows.append({
                "Saham": symbol,
                "Harga": round(latest["Close"], 0),
                "AI Score": ai,
                "ML Signal": ml_sig,
                "Bandar": latest["Bandar"],
                "Decision": decision
            })

    return (
        pd.DataFrame(rows)
        .sort_values(["Decision", "AI Score"], ascending=False)
        .reset_index(drop=True)
        if rows else pd.DataFrame()
    )


# =====================================================
# HEATMAP MATRIX — CLASSIC
# =====================================================
def heatmap_matrix_engine():
    rows = []

    for symbol in LATEST_SYMBOLS:
        d = SYMBOL_MAP.get(symbol)
        if d is None:
            continue

        latest = d.iloc[-1]

        rows.append({
            "Symbol": symbol,
            "Confidence": AI_SCORE_MAP.get(symbol, 0),
            "Volume": latest["Volume"]
        })

    dfm = pd.DataFrame(rows)
    if dfm.empty:
        return pd.DataFrame()

    dfm["Conf_Level"] = pd.qcut(
        dfm["Confidence"], 3, labels=["Low", "Mid", "High"]
    )
    dfm["Vol_Level"] = pd.qcut(
        dfm["Volume"], 3, labels=["Low", "Mid", "High"]
    )

    return pd.crosstab(dfm["Vol_Level"], dfm["Conf_Level"])


# =====================================================
# 🔥 HEATMAP MATRIX V2 — DECISION BASED
# =====================================================
def heatmap_matrix_v2():
    rows = []

    for symbol in LATEST_SYMBOLS:
        d = SYMBOL_MAP.get(symbol)
        if d is None:
            continue

        latest = d.iloc[-1]
        ai = AI_SCORE_MAP.get(symbol, 0)

        ml_conf = (
            latest.get("ml_confidence_label_daily")
            if not pd.isna(latest.get("ml_confidence_label_daily"))
            else latest.get("ml_confidence_label_weekly")
        )

        ml_sig = ml_decision_v2(ml_conf)
        decision = final_decision_engine(
            ai_score=ai,
            ml_signal=ml_sig,
            bandar=latest["Bandar"]
        )

        rows.append({
            "Decision": decision,
            "Volume": latest["Volume"]
        })

    dfh = pd.DataFrame(rows)
    if dfh.empty:
        return pd.DataFrame()

    return pd.crosstab(
        dfh["Decision"],
        pd.qcut(dfh["Volume"], 3)
    )


# =====================================================
# RANKING — CLASSIC
# =====================================================
def auto_ranking(top_n=10):
    rows = []

    for symbol in LATEST_SYMBOLS:
        d = SYMBOL_MAP.get(symbol)
        if d is None:
            continue

        latest = d.iloc[-1]
        ai = AI_SCORE_MAP.get(symbol, 0)

        if latest["Bandar"] == "AKUMULASI" and ai >= 60:
            rows.append({
                "Saham": symbol,
                "AI Score": ai,
                "Harga": round(latest["Close"], 0),
                "Bandar": latest["Bandar"]
            })

    return (
        pd.DataFrame(rows)
        .sort_values("AI Score", ascending=False)
        .head(top_n)
        .reset_index(drop=True)
        if rows else pd.DataFrame()
    )


# =====================================================
# 🔥 RANKING V2 — FULL DECISION ENGINE
# =====================================================
def auto_ranking_v2(top_n=15):
    rows = []

    for symbol in LATEST_SYMBOLS:
        d = SYMBOL_MAP.get(symbol)
        if d is None:
            continue

        latest = d.iloc[-1]
        ai = AI_SCORE_MAP.get(symbol, 0)

        ml_conf = (
            latest.get("ml_confidence_label_daily")
            if not pd.isna(latest.get("ml_confidence_label_daily"))
            else latest.get("ml_confidence_label_weekly")
        )

        ml_sig = ml_decision_v2(ml_conf)
        decision = final_decision_engine(
            ai_score=ai,
            ml_signal=ml_sig,
            bandar=latest["Bandar"]
        )

        if decision in ["BUY", "STRONG_BUY"]:
            rows.append({
                "Saham": symbol,
                "AI Score": ai,
                "ML Signal": ml_sig,
                "Bandar": latest["Bandar"],
                "Decision": decision
            })

    return (
        pd.DataFrame(rows)
        .sort_values(["Decision", "AI Score"], ascending=False)
        .head(top_n)
        .reset_index(drop=True)
        if rows else pd.DataFrame()
    )


# =====================================================
# CACHE WRAPPER — CLASSIC & AI PRO
# =====================================================
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


# =====================================================
# CACHE — AI PRO (V2)
# =====================================================
@st.cache_data(show_spinner=False)
def cached_daily_v2():
    return strategy_v2("daily")

@st.cache_data(show_spinner=False)
def cached_weekly_v2():
    return strategy_v2("weekly")

@st.cache_data(show_spinner=False)
def cached_monthly_v2():
    return strategy_v2("monthly")

@st.cache_data(show_spinner=False)
def cached_watchlist_v2():
    return generate_watchlist_v2()

@st.cache_data(show_spinner=False)
def cached_heatmap_v2():
    return heatmap_matrix_v2()

@st.cache_data(show_spinner=False)
def cached_ranking_v2(top_n=15):
    return auto_ranking_v2(top_n)
# =====================================================
# PART 5 — MODE SWITCH & UI ROUTING
# =====================================================

# =====================================================
# SIDEBAR — MODE ENGINE
# =====================================================
st.sidebar.markdown("### 🤖 Mode Analisa")

analysis_mode = st.sidebar.radio(
    "Pilih Engine",
    ["CLASSIC", "AI PRO"],
    index=1
)

st.sidebar.markdown("---")

# =====================================================
# SIDEBAR — NAVIGATION
# =====================================================
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

st.sidebar.markdown("---")

selected_limit = st.sidebar.slider(
    "🔢 Jumlah Saham",
    min_value=5,
    max_value=50,
    value=15,
    step=5
)

# =====================================================
# ENGINE SELECTOR (TANPA IF BERANTAKAN)
# =====================================================
def get_daily_result():
    if analysis_mode == "AI PRO":
        return cached_daily_v2()
    return cached_daily()

def get_weekly_result():
    if analysis_mode == "AI PRO":
        return cached_weekly_v2()
    return cached_weekly()

def get_monthly_result():
    if analysis_mode == "AI PRO":
        return cached_monthly_v2()
    return cached_monthly()

def get_watchlist_result():
    if analysis_mode == "AI PRO":
        return cached_watchlist_v2()
    return cached_watchlist()

def get_heatmap_result():
    if analysis_mode == "AI PRO":
        return cached_heatmap_v2()
    return cached_heatmap_matrix()

def get_ranking_result():
    if analysis_mode == "AI PRO":
        return cached_ranking_v2(selected_limit)
    return cached_ranking(selected_limit)

# =====================================================
# DASHBOARD
# =====================================================
if menu == "🏠 Dashboard":

    st.markdown("## 📊 Market Overview")

    latest_all = df.groupby("Symbol").tail(1)

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Total Saham", len(latest_all))
    c2.metric("Akumulasi", (latest_all["Bandar"] == "AKUMULASI").sum())
    c3.metric("Distribusi", (latest_all["Bandar"] == "DISTRIBUSI").sum())
    c4.metric("Mode Aktif", analysis_mode)

    st.markdown("### 🔥 Heatmap Decision Engine")
    heatmap_df = get_heatmap_result()
    st.dataframe(heatmap_df, use_container_width=True)

# =====================================================
# DAILY
# =====================================================
elif menu == "📅 Rekomendasi Harian":
    st.subheader("📅 Rekomendasi Harian")
    st.caption(f"Mode: {analysis_mode}")
    df_daily = get_daily_result()
    st.dataframe(df_daily.head(selected_limit), use_container_width=True)

# =====================================================
# WEEKLY
# =====================================================
elif menu == "📊 Swing Mingguan":
    st.subheader("📊 Swing Mingguan")
    st.caption(f"Mode: {analysis_mode}")
    df_weekly = get_weekly_result()
    st.dataframe(df_weekly.head(selected_limit), use_container_width=True)

# =====================================================
# MONTHLY
# =====================================================
elif menu == "🗓️ Rekomendasi Bulanan":
    st.subheader("🗓️ Rekomendasi Bulanan")
    st.caption(f"Mode: {analysis_mode}")
    df_monthly = get_monthly_result()
    st.dataframe(df_monthly.head(selected_limit), use_container_width=True)

# =====================================================
# WATCHLIST
# =====================================================
elif menu == "⭐ Watchlist":
    st.subheader("⭐ Watchlist Saham Potensial")
    wl = get_watchlist_result()
    st.dataframe(wl.head(selected_limit), use_container_width=True)

# =====================================================
# HEATMAP MATRIX
# =====================================================
elif menu == "📊 Heatmap Matrix":
    st.subheader("📊 Heatmap Matrix")
    matrix = get_heatmap_result()
    st.dataframe(matrix, use_container_width=True)

# =====================================================
# RANKING
# =====================================================
elif menu == "🤖 Ranking Harian":
    st.subheader("🤖 Ranking Saham Terkuat")
    rank = get_ranking_result()
    st.dataframe(rank, use_container_width=True)

# =====================================================
# ANALISA 1 SAHAM
# =====================================================
elif menu == "🔍 Analisa 1 Saham":

    symbol = st.selectbox("Pilih Saham", sorted(SYMBOL_MAP.keys()))
    d = SYMBOL_MAP[symbol].tail(300)

    latest = d.iloc[-1]
    ai = AI_SCORE_MAP.get(symbol, 0)

    ml_conf = (
        latest.get("ml_confidence_label_daily")
        if not pd.isna(latest.get("ml_confidence_label_daily"))
        else latest.get("ml_confidence_label_weekly")
        if not pd.isna(latest.get("ml_confidence_label_weekly"))
        else latest.get("ml_confidence_label_monthly")
    )

    ml_sig = ml_decision_v2(ml_conf)
    decision = final_decision_engine(
        ai_score=ai,
        ml_signal=ml_sig,
        bandar=latest["Bandar"]
    )

    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("Harga", f"{latest['Close']:.0f}")
    c2.metric("Bandar", latest["Bandar"])
    c3.metric("AI Score", ai)
    c4.metric("ML Signal", ml_sig)
    c5.metric("Decision", decision)

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

# =====================================================
# FOOTER
# =====================================================
st.markdown("""
---
© 2026 **SahamAI Enterprise**  
Green • Quant • IDX • AI Powered  
Mode Engine: **CLASSIC / AI PRO**
""")

# =====================================================
# PART 6 — BACKTEST ENGINE (PnL BASED)
# =====================================================

# =====================================================
# CONFIG BACKTEST
# =====================================================
TAKE_PROFIT = 0.05     # +5%
STOP_LOSS   = 0.03     # -3%
MAX_HOLD    = 10       # max 10 hari

# =====================================================
# CORE BACKTEST FUNCTION
# =====================================================
def backtest_single_symbol(
    df,
    decision_col="Decision",
    price_col="Close"
):
    """
    Backtest sederhana & jujur:
    - Entry saat BUY / STRONG_BUY
    - Exit via TP / SL / Max Hold
    """
    trades = []

    df = df.copy().reset_index(drop=True)

    for i in range(len(df) - MAX_HOLD - 1):

        row = df.iloc[i]
        decision = row.get(decision_col)

        if decision not in ["BUY", "STRONG_BUY"]:
            continue

        entry_price = row[price_col]
        entry_date  = row["Tanggal Perdagangan Terakhir"]

        exit_price = entry_price
        exit_date  = entry_date
        result     = 0

        for j in range(1, MAX_HOLD + 1):
            future = df.iloc[i + j]
            ret = (future[price_col] - entry_price) / entry_price

            if ret >= TAKE_PROFIT:
                exit_price = future[price_col]
                exit_date  = future["Tanggal Perdagangan Terakhir"]
                result     = TAKE_PROFIT
                break

            if ret <= -STOP_LOSS:
                exit_price = future[price_col]
                exit_date  = future["Tanggal Perdagangan Terakhir"]
                result     = -STOP_LOSS
                break

        trades.append({
            "entry_date": entry_date,
            "exit_date": exit_date,
            "entry": entry_price,
            "exit": exit_price,
            "return": result
        })

    if not trades:
        return None

    return pd.DataFrame(trades)

# =====================================================
# BACKTEST ALL SYMBOLS (AI PRO)
# =====================================================
@st.cache_data(show_spinner=True)
def run_backtest_ai_pro():
    all_trades = []

    for symbol in LATEST_SYMBOLS:
        d = SYMBOL_MAP.get(symbol)
        if d is None or len(d) < 300:
            continue

        d = d.copy()

        # build decision per bar
        d["ML_CONF"] = (
            d["ml_confidence_label_daily"]
            .fillna(d["ml_confidence_label_weekly"])
            .fillna(d["ml_confidence_label_monthly"])
        )

        d["ML_SIGNAL"] = d["ML_CONF"].apply(ml_decision_v2)

        d["Decision"] = d.apply(
            lambda r: final_decision_engine(
                ai_score=AI_SCORE_MAP.get(symbol, 0),
                ml_signal=r["ML_SIGNAL"],
                bandar=r["Bandar"]
            ),
            axis=1
        )

        trades = backtest_single_symbol(d)

        if trades is None or trades.empty:
            continue

        trades["Symbol"] = symbol
        all_trades.append(trades)

    if not all_trades:
        return pd.DataFrame()

    return pd.concat(all_trades).reset_index(drop=True)

# =====================================================
# METRICS
# =====================================================
def backtest_metrics(trades):
    total_trades = len(trades)
    wins = trades[trades["return"] > 0]
    losses = trades[trades["return"] < 0]

    winrate = len(wins) / total_trades if total_trades else 0
    avg_pnl = trades["return"].mean() if total_trades else 0

    equity = trades["return"].cumsum()
    max_dd = (equity.cummax() - equity).max()

    return {
        "Trades": total_trades,
        "Winrate": round(winrate, 3),
        "Avg PnL": round(avg_pnl, 4),
        "Max Drawdown": round(max_dd, 4),
        "Total Return": round(equity.iloc[-1], 4) if total_trades else 0
    }

# =====================================================
# UI — BACKTEST PAGE
# =====================================================
if menu == "🧪 Backtest AI PRO":

    st.subheader("🧪 Backtest AI PRO — PnL Based")

    trades = run_backtest_ai_pro()

    if trades.empty:
        st.warning("❌ Tidak ada trade terdeteksi.")
    else:
        metrics = backtest_metrics(trades)

        c1, c2, c3, c4, c5 = st.columns(5)
        c1.metric("Trades", metrics["Trades"])
        c2.metric("Winrate", f"{metrics['Winrate']*100:.1f}%")
        c3.metric("Avg PnL", f"{metrics['Avg PnL']*100:.2f}%")
        c4.metric("Max DD", f"{metrics['Max Drawdown']*100:.2f}%")
        c5.metric("Total Return", f"{metrics['Total Return']*100:.2f}%")

        st.markdown("### 📈 Equity Curve")
        trades["equity"] = trades["return"].cumsum()
        st.line_chart(trades["equity"])

        st.markdown("### 📋 Trade Log")
        st.dataframe(trades.tail(200), use_container_width=True)
