import streamlit as st
import pandas as pd
import numpy as np
import joblib
from datetime import datetime

# ==========================================
# PAGE CONFIG
# ==========================================
st.set_page_config(
    page_title="SahamAI Hybrid Quant",
    page_icon="🏦",
    layout="wide"
)

# ==========================================
# STYLE
# ==========================================
st.markdown("""
<style>
    .stApp {
        background-color: #0e1117;
        color: #e6ffe6;
    }
    h1, h2, h3 {
        color: #00ff88;
    }
</style>
""", unsafe_allow_html=True)

# ==========================================
# LOAD DATA
# ==========================================
@st.cache_data
def load_data():
    df_w = pd.read_parquet("processed/ml_confidence_label_weekly.parquet")
    df_m = pd.read_parquet("processed/ml_confidence_label_monthly.parquet")
    df_price = pd.read_parquet("processed/daily_clean_strict.parquet")
    df_feat = pd.read_parquet("ml/dataset_features.parquet")

    for d in [df_w, df_m, df_price, df_feat]:
        d["Tanggal"] = pd.to_datetime(d["Tanggal"])

    df = (
        df_w.merge(df_m, on=["Symbol","Tanggal"])
        .merge(df_price[["Symbol","Tanggal","Close"]], on=["Symbol","Tanggal"])
        .merge(df_feat[["Symbol","Tanggal","ATR_RATIO","VOL_REGIME"]], on=["Symbol","Tanggal"])
    )

    return df.sort_values("Tanggal")

df = load_data()

# ==========================================
# LOAD MODEL
# ==========================================
weekly_model = joblib.load("ml/models/label_weekly.pkl")
monthly_model = joblib.load("ml/models/label_monthly.pkl")

weekly_th = weekly_model["threshold"]
monthly_th = monthly_model["threshold"]

# ==========================================
# SIDEBAR SETTINGS
# ==========================================
st.sidebar.header("⚙ Portfolio Settings")

selected_date = st.sidebar.date_input(
    "Tanggal",
    value=df["Tanggal"].max()
)

mode = st.sidebar.radio(
    "Mode",
    ["Harian", "1 Bulan", "Tahunan"]
)

capital = st.sidebar.number_input("Total Capital", 100_000_000)
risk_pct = st.sidebar.slider("Risk per Trade (%)", 0.5, 5.0, 2.0)
max_positions = st.sidebar.slider("Max Positions", 1, 15, 5)
vol_filter = st.sidebar.slider("Max Vol Regime", 0.5, 3.0, 1.8)

selected_date = pd.to_datetime(selected_date)

# ==========================================
# BASE FILTER
# ==========================================
if mode == "Harian":
    base_df = df[df["Tanggal"] == selected_date]
elif mode == "1 Bulan":
    base_df = df[df["Tanggal"] >= selected_date - pd.Timedelta(days=30)]
else:
    base_df = df[df["Tanggal"] >= selected_date - pd.Timedelta(days=365)]

signals = base_df[
    (base_df["ml_confidence_label_weekly"] > weekly_th) &
    (base_df["ml_confidence_label_monthly"] > monthly_th) &
    (base_df["VOL_REGIME"] < vol_filter)
].copy()

if mode != "Harian":
    signals = signals.sort_values("Tanggal").groupby("Symbol").tail(1)

# ==========================================
# RANKING SYSTEM
# ==========================================
signals["Score"] = (
    signals["ml_confidence_label_weekly"] +
    signals["ml_confidence_label_monthly"] -
    signals["VOL_REGIME"]
)

signals = signals.sort_values("Score", ascending=False).head(max_positions)

# ==========================================
# RISK & POSITION SIZING
# ==========================================
risk_amount = capital * (risk_pct / 100)

signals["Stop_Loss"] = signals["Close"] - (signals["ATR_RATIO"] * signals["Close"])
signals["Risk_per_Share"] = signals["Close"] - signals["Stop_Loss"]

signals["Position_Size"] = np.floor(risk_amount / signals["Risk_per_Share"])
signals["Capital_Used"] = signals["Position_Size"] * signals["Close"]

# Prevent over allocation
total_used = signals["Capital_Used"].sum()

if total_used > capital:
    scaling_factor = capital / total_used
    signals["Position_Size"] = np.floor(signals["Position_Size"] * scaling_factor)
    signals["Capital_Used"] = signals["Position_Size"] * signals["Close"]
    total_used = signals["Capital_Used"].sum()

remaining_cash = capital - total_used

# ==========================================
# DASHBOARD METRICS
# ==========================================
col1, col2, col3, col4 = st.columns(4)

col1.metric("Total Capital", f"{capital:,.0f}")
col2.metric("Used Capital", f"{total_used:,.0f}")
col3.metric("Remaining Cash", f"{remaining_cash:,.0f}")
col4.metric("Open Positions", len(signals))

st.divider()

# ==========================================
# PORTFOLIO TABLE
# ==========================================
st.subheader("📊 Portfolio Allocation")

if len(signals) > 0:
    display = signals[[
        "Symbol",
        "Close",
        "Score",
        "Stop_Loss",
        "Position_Size",
        "Capital_Used"
    ]]
    st.dataframe(display, use_container_width=True)
else:
    st.warning("No valid signals.")

# ==========================================
# EQUITY SIMULATION (STRUCTURE READY)
# ==========================================
st.divider()
st.subheader("📈 Equity Simulation (Preview)")

equity = capital
equity_curve = []

for i in range(30):
    daily_return = np.random.normal(0.0015, 0.01)
    equity *= (1 + daily_return)
    equity_curve.append(equity)

equity_df = pd.DataFrame({
    "Day": range(1,31),
    "Equity": equity_curve
}).set_index("Day")

st.line_chart(equity_df)

# ==========================================
# SINGLE STOCK ANALYSIS
# ==========================================
st.divider()
st.subheader("🔍 Deep Stock Analysis")

selected_symbol = st.selectbox("Select Stock", df["Symbol"].unique())
stock_df = df[df["Symbol"] == selected_symbol].sort_values("Tanggal")

if len(stock_df) > 0:
    latest = stock_df.iloc[-1]

    col1, col2, col3 = st.columns(3)
    col1.metric("Last Price", round(latest["Close"],2))
    col2.metric("Weekly Conf", round(latest["ml_confidence_label_weekly"],3))
    col3.metric("Monthly Conf", round(latest["ml_confidence_label_monthly"],3))

    st.line_chart(
        stock_df.set_index("Tanggal")[[
            "ml_confidence_label_weekly",
            "ml_confidence_label_monthly"
        ]]
    )

    st.line_chart(
        stock_df.set_index("Tanggal")["Close"]
    )

    if (latest["ml_confidence_label_weekly"] > weekly_th and
        latest["ml_confidence_label_monthly"] > monthly_th):
        st.success("AI Recommendation: BUY")
    else:
        st.info("AI Recommendation: WAIT / HOLD")

# ==========================================
# FOOTER
# ==========================================
st.divider()
st.caption("SahamAI Hybrid Quant Edition © 2026")
