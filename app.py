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
# LOAD STYLE (ASLI)
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
# PATH DATA (ASLI)
# =====================================================
DATA_PATH = "processed/daily_clean.parquet"

ML_DAILY_PATH   = "processed/ml_confidence_label_daily.parquet"
ML_WEEKLY_PATH  = "processed/ml_confidence_label_weekly.parquet"
ML_MONTHLY_PATH = "processed/ml_confidence_label_monthly.parquet"

# =====================================================
# TAMBAHAN (BARU, TIDAK MENGGANGGU)
# WALK-FORWARD RESULT (UNTUK OPTIMAL THRESHOLD)
# =====================================================
WF_PATH = "processed/walk_forward_result_weekly.parquet"

# =====================================================
# LOAD DATA UTAMA (ASLI)
# =====================================================
@st.cache_data(show_spinner=False)
def load_data():
    if not os.path.exists(DATA_PATH):
        st.error("❌ Data utama tidak ditemukan")
        st.stop()
    return pd.read_parquet(DATA_PATH)

df = load_data()

# =====================================================
# MERGE ML CONFIDENCE (ASLI, TIDAK DIUBAH)
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
# LATEST SYMBOL LIST (ASLI)
# =====================================================
LATEST_SYMBOLS = (
    df.sort_values("Tanggal Perdagangan Terakhir")
      .groupby("Symbol")
      .tail(1)["Symbol"]
      .tolist()
)

# =====================================================
# SYMBOL MAP (ASLI)
# =====================================================
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

# =====================================================
# 🔥 TAMBAHAN BARU (OPTIMAL, TIDAK MENGGANTI APA PUN)
# LOAD ML THRESHOLD HASIL WALK-FORWARD
# =====================================================
@st.cache_data(show_spinner=False)
def load_ml_threshold():
    """
    Ambil threshold optimal dari hasil walk-forward.
    Kalau file belum ada → fallback aman.
    """
    default = {
        "daily": 0.60,
        "weekly": 0.65,
        "monthly": 0.70
    }

    if not os.path.exists(WF_PATH):
        return default

    try:
        wf = pd.read_parquet(WF_PATH)
        if wf.empty:
            return default

        last = wf.sort_values("test_end").iloc[-1]
        default["weekly"] = float(last["threshold"])
        return default

    except Exception:
        return default

ML_THRESHOLD = load_ml_threshold()
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
# LOAD STYLE (ASLI)
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
# PATH DATA (ASLI)
# =====================================================
DATA_PATH = "processed/daily_clean.parquet"

ML_DAILY_PATH   = "processed/ml_confidence_label_daily.parquet"
ML_WEEKLY_PATH  = "processed/ml_confidence_label_weekly.parquet"
ML_MONTHLY_PATH = "processed/ml_confidence_label_monthly.parquet"

# =====================================================
# TAMBAHAN (BARU, TIDAK MENGGANGGU)
# WALK-FORWARD RESULT (UNTUK OPTIMAL THRESHOLD)
# =====================================================
WF_PATH = "processed/walk_forward_result_weekly.parquet"

# =====================================================
# LOAD DATA UTAMA (ASLI)
# =====================================================
@st.cache_data(show_spinner=False)
def load_data():
    if not os.path.exists(DATA_PATH):
        st.error("❌ Data utama tidak ditemukan")
        st.stop()
    return pd.read_parquet(DATA_PATH)

df = load_data()

# =====================================================
# MERGE ML CONFIDENCE (ASLI, TIDAK DIUBAH)
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
# LATEST SYMBOL LIST (ASLI)
# =====================================================
LATEST_SYMBOLS = (
    df.sort_values("Tanggal Perdagangan Terakhir")
      .groupby("Symbol")
      .tail(1)["Symbol"]
      .tolist()
)

# =====================================================
# SYMBOL MAP (ASLI)
# =====================================================
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

# =====================================================
# 🔥 TAMBAHAN BARU (OPTIMAL, TIDAK MENGGANTI APA PUN)
# LOAD ML THRESHOLD HASIL WALK-FORWARD
# =====================================================
@st.cache_data(show_spinner=False)
def load_ml_threshold():
    """
    Ambil threshold optimal dari hasil walk-forward.
    Kalau file belum ada → fallback aman.
    """
    default = {
        "daily": 0.60,
        "weekly": 0.65,
        "monthly": 0.70
    }

    if not os.path.exists(WF_PATH):
        return default

    try:
        wf = pd.read_parquet(WF_PATH)
        if wf.empty:
            return default

        last = wf.sort_values("test_end").iloc[-1]
        default["weekly"] = float(last["threshold"])
        return default

    except Exception:
        return default

ML_THRESHOLD = load_ml_threshold()
# =====================================================
# STRATEGY DAILY — ASLI (TIDAK DIUBAH)
# =====================================================
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

# =====================================================
# STRATEGY WEEKLY — ASLI (TIDAK DIUBAH)
# =====================================================
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

# =====================================================
# STRATEGY MONTHLY — ASLI (TIDAK DIUBAH)
# =====================================================
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

# =====================================================
# 🔥 STRATEGY DAILY V2 — OPTIMAL (BARU, TIDAK MENGGANTI)
# =====================================================
def strategy_daily_v2():
    rows = []

    for symbol in LATEST_SYMBOLS:
        d = SYMBOL_MAP.get(symbol)
        if d is None or len(d) < 40:
            continue

        latest = d.iloc[-1]
        ai = AI_SCORE_MAP.get(symbol, 0)
        ml_conf = latest.get("ml_confidence_label_daily", np.nan)
        ml_sig = ml_decision_v2(ml_conf, mode="daily")

        decision = final_decision_engine(
            ai_score=ai,
            ml_signal=ml_sig,
            bandar=latest["Bandar"]
        )

        if decision == "WAIT":
            continue

        rows.append({
            "Mode": "HARIAN_V2",
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
# 🔥 STRATEGY WEEKLY V2 — OPTIMAL (BARU)
# =====================================================
def strategy_weekly_v2():
    rows = []

    for symbol in LATEST_SYMBOLS:
        d = SYMBOL_MAP.get(symbol)
        if d is None or len(d) < 150:
            continue

        latest = d.iloc[-1]
        ai = AI_SCORE_MAP.get(symbol, 0)
        ml_conf = latest.get("ml_confidence_label_weekly", np.nan)
        ml_sig = ml_decision_v2(ml_conf, mode="weekly")

        decision = final_decision_engine(
            ai_score=ai,
            ml_signal=ml_sig,
            bandar=latest["Bandar"]
        )

        if decision == "WAIT":
            continue

        rows.append({
            "Mode": "MINGGUAN_V2",
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
# 🔥 STRATEGY MONTHLY V2 — OPTIMAL (BARU)
# =====================================================
def strategy_monthly_v2():
    rows = []

    for symbol in LATEST_SYMBOLS:
        d = SYMBOL_MAP.get(symbol)
        if d is None or len(d) < 300:
            continue

        latest = d.iloc[-1]
        ai = AI_SCORE_MAP.get(symbol, 0)
        ml_conf = latest.get("ml_confidence_label_monthly", np.nan)
        ml_sig = ml_decision_v2(ml_conf, mode="monthly")

        decision = final_decision_engine(
            ai_score=ai,
            ml_signal=ml_sig,
            bandar=latest["Bandar"]
        )

        if decision == "WAIT":
            continue

        rows.append({
            "Mode": "BULANAN_V2",
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
# WATCHLIST — ASLI (TIDAK DIUBAH)
# =====================================================
def generate_watchlist():
    rows = []

    for symbol in LATEST_SYMBOLS:
        d_all = SYMBOL_MAP.get(symbol)
        if d_all is None or len(d_all) < 120:
            continue

        latest = d_all.iloc[-1]
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

# =====================================================
# 🔥 WATCHLIST V2 — DECISION BASED
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
# HEATMAP MATRIX — ASLI
# =====================================================
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

    return pd.crosstab(dfh["Decision"], pd.qcut(dfh["Volume"], 3))

# =====================================================
# RANKING — ASLI
# =====================================================
def auto_ranking(top_n=10):
    rows = []

    for symbol in LATEST_SYMBOLS:
        d_all = SYMBOL_MAP.get(symbol)
        if d_all is None:
            continue

        latest = d_all.iloc[-1]
        ai_score = AI_SCORE_MAP.get(symbol, 0)

        if latest["Bandar"] == "AKUMULASI" and ai_score >= 60:
            rows.append({
                "Saham": symbol,
                "AI Score": ai_score,
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
# CACHE — TAMBAHAN V2 (TIDAK GANGGU ASLI)
# =====================================================
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
# 🔧 MODE SWITCH (CLASSIC vs AI PRO)
# =====================================================
st.sidebar.markdown("### 🤖 Mode Analisa")

analysis_mode = st.sidebar.radio(
    "Pilih Mode Engine",
    ["CLASSIC", "AI PRO"],
    index=1
)

# =====================================================
# HELPER — PILIH ENGINE BERDASARKAN MODE
# =====================================================
def get_daily_result():
    if analysis_mode == "AI PRO":
        return cached_watchlist_v2()
    return cached_daily()

def get_weekly_result():
    if analysis_mode == "AI PRO":
        return cached_ranking_v2(20)
    return cached_weekly()

def get_monthly_result():
    if analysis_mode == "AI PRO":
        return cached_ranking_v2(20)
    return cached_monthly()

def get_heatmap_result():
    if analysis_mode == "AI PRO":
        return cached_heatmap_v2()
    return cached_heatmap_matrix()

# =====================================================
# DASHBOARD OVERRIDE (TANPA HAPUS YANG LAMA)
# =====================================================
if menu == "🏠 Dashboard":

    st.markdown("<div class='section-box'>", unsafe_allow_html=True)
    st.markdown("### 📊 Market Overview")

    st.markdown(
        f"<div class='info-bar'>{market_countdown_text()}</div>",
        unsafe_allow_html=True
    )

    latest_all = df.groupby("Symbol").tail(1)

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Total Saham", len(latest_all))
    c2.metric("Akumulasi", (latest_all["Bandar"] == "AKUMULASI").sum())
    c3.metric("Distribusi", (latest_all["Bandar"] == "DISTRIBUSI").sum())
    c4.metric("Mode Aktif", analysis_mode)

    st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("<div class='section-box'>", unsafe_allow_html=True)
    st.markdown("### 🔥 Heatmap Decision Engine")

    heatmap_df = get_heatmap_result()
    st.dataframe(heatmap_df, use_container_width=True)

    st.markdown("</div>", unsafe_allow_html=True)

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
# WATCHLIST (V2 AUTO)
# =====================================================
elif menu == "⭐ Watchlist":
    st.subheader("⭐ Watchlist Decision Engine")
    wl = cached_watchlist_v2() if analysis_mode == "AI PRO" else cached_watchlist()
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
    rank = cached_ranking_v2(selected_limit) if analysis_mode == "AI PRO" else cached_ranking(selected_limit)
    st.dataframe(rank, use_container_width=True)

# =====================================================
# ANALISA 1 SAHAM — TAMBAHAN DECISION
# =====================================================
elif menu == "🔍 Analisa 1 Saham":

    symbol = st.selectbox("Pilih Saham", sorted(SYMBOL_MAP.keys()))
    d = SYMBOL_MAP[symbol].tail(250)

    ai = AI_SCORE_MAP.get(symbol, 0)
    latest = d.iloc[-1]

    ml_conf = (
        latest.get("ml_confidence_label_daily")
        if not pd.isna(latest.get("ml_confidence_label_daily"))
        else latest.get("ml_confidence_label_weekly")
        if not pd.isna(latest.get("ml_confidence_label_weekly"))
        else latest.get("ml_confidence_label_monthly")
    )

    ml_sig = ml_decision_v2(ml_conf)

    final_dec = final_decision_engine(
        ai_score=ai,
        ml_signal=ml_sig,
        bandar=latest["Bandar"]
    )

    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("Harga", f"{latest['Close']:.0f}")
    c2.metric("Bandar", latest["Bandar"])
    c3.metric("AI Score", ai)
    c4.metric("ML Signal", ml_sig)
    c5.metric("Decision", final_dec)

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
