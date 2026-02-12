import streamlit as st
import pandas as pd
import numpy as np
import joblib

# =========================================================
# PAGE CONFIG
# =========================================================
st.set_page_config(
    page_title="SahamAI Quant Institutional",
    page_icon="📊",
    layout="wide"
)

# =========================================================
# WHITE + GREEN STYLE
# =========================================================
st.markdown("""
<style>
.stApp { background-color:#f8f9fa; color:#212529; }

[data-testid="stSidebar"] { background-color:#198754; }
[data-testid="stSidebar"] * { color:white !important; }

[data-testid="metric-container"] {
    background:white;
    border:1px solid #dee2e6;
    border-radius:12px;
    padding:15px;
}

.ai-box {
    background:white;
    padding:20px;
    border-radius:12px;
    border:1px solid #dee2e6;
    line-height:1.8;
    font-size:16px;
}

thead tr th {
    background-color:#198754 !important;
    color:white !important;
}

tbody tr:nth-child(even) {
    background-color:#f1fdf6 !important;
}

h1,h2,h3 { color:#198754; }
</style>
""", unsafe_allow_html=True)

# =========================================================
# LOAD DATA
# =========================================================
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

weekly_model = joblib.load("ml/models/label_weekly.pkl")
monthly_model = joblib.load("ml/models/label_monthly.pkl")

weekly_th = weekly_model["threshold"]
monthly_th = monthly_model["threshold"]

# =========================================================
# SIDEBAR
# =========================================================
st.sidebar.image("assets/logo.png", width=200)
st.sidebar.title("SahamAI Quant Institutional")

selected_date = st.sidebar.date_input(
    "Tanggal",
    value=df["Tanggal"].max()
)

mode = st.sidebar.radio("Mode", ["Harian","1 Bulan","Tahunan"])
capital = st.sidebar.number_input("Total Capital", 100_000_000)
risk_pct = st.sidebar.slider("Risk per Trade (%)",0.5,5.0,2.0)
reward_ratio = st.sidebar.slider("Risk Reward Ratio",1.0,5.0,2.0)
max_positions = st.sidebar.slider("Max Positions",1,15,5)
vol_filter = st.sidebar.slider("Max Vol Regime",0.5,3.0,1.8)

selected_date = pd.to_datetime(selected_date)

# =========================================================
# FILTER BASE
# =========================================================
if mode == "Harian":
    base_df = df[df["Tanggal"] == selected_date]
elif mode == "1 Bulan":
    base_df = df[df["Tanggal"] >= selected_date - pd.Timedelta(days=30)]
else:
    base_df = df[df["Tanggal"] >= selected_date - pd.Timedelta(days=365)]

eligible = base_df[
    (base_df["ml_confidence_label_weekly"] > weekly_th) &
    (base_df["ml_confidence_label_monthly"] > monthly_th) &
    (base_df["VOL_REGIME"] < vol_filter)
].copy()

if mode != "Harian":
    eligible = eligible.sort_values("Tanggal").groupby("Symbol").tail(1)

eligible["Score"] = (
    eligible["ml_confidence_label_weekly"] +
    eligible["ml_confidence_label_monthly"] -
    eligible["VOL_REGIME"]
)

eligible = eligible.sort_values("Score",ascending=False)

# =========================================================
# ENTRY STOP TARGET + REKOMENDASI
# =========================================================
eligible["Entry"] = eligible["Close"]
eligible["Stop_Loss"] = eligible["Close"] - (eligible["ATR_RATIO"] * eligible["Close"])
eligible["Target"] = eligible["Close"] + (
    (eligible["Close"] - eligible["Stop_Loss"]) * reward_ratio
)

eligible["Risk"] = eligible["Entry"] - eligible["Stop_Loss"]
eligible["Reward"] = eligible["Target"] - eligible["Entry"]
eligible["RR"] = eligible["Reward"] / eligible["Risk"]

def recommendation(row):
    if row["Score"] > 1.5 and row["RR"] >= 2:
        return "STRONG BUY"
    elif row["Score"] > 1.2:
        return "BUY"
    elif row["Score"] > 1.0:
        return "HOLD"
    else:
        return "WAIT"

eligible["Recommendation"] = eligible.apply(recommendation,axis=1)

# =========================================================
# WATCHLIST
# =========================================================
st.title("🟢 Eligible Watchlist")

watch_display = eligible[[
    "Symbol","Entry","Stop_Loss","Target",
    "RR","Score","Recommendation"
]]

st.dataframe(watch_display, use_container_width=True)

# =========================================================
# PORTFOLIO
# =========================================================
signals = eligible.head(max_positions).copy()
risk_amount = capital * (risk_pct / 100)

signals["Position_Size"] = np.floor(risk_amount / signals["Risk"])
signals["Capital_Used"] = signals["Position_Size"] * signals["Entry"]

total_used = signals["Capital_Used"].sum()
remaining_cash = capital - total_used

st.divider()

col1,col2,col3,col4 = st.columns(4)
col1.metric("Total Capital",f"{capital:,.0f}")
col2.metric("Used Capital",f"{total_used:,.0f}")
col3.metric("Remaining Cash",f"{remaining_cash:,.0f}")
col4.metric("Positions",len(signals))

st.subheader("🏦 Portfolio Allocation")

st.dataframe(signals[[
    "Symbol","Entry","Stop_Loss","Target",
    "Position_Size","Capital_Used","Recommendation"
]], use_container_width=True)

# =========================================================
# ALLOCATION CHART
# =========================================================
st.subheader("📊 Allocation Breakdown")
if len(signals)>0:
    st.bar_chart(signals.set_index("Symbol")["Capital_Used"])

# =========================================================
# EQUITY PREVIEW
# =========================================================
st.subheader("📈 Equity Simulation (Preview)")
equity = capital
curve=[]
for i in range(30):
    equity *= (1 + np.random.normal(0.0015,0.01))
    curve.append(equity)
st.line_chart(pd.DataFrame({"Equity":curve}))

# =========================================================
# DEEP ANALYSIS + AI PANEL
# =========================================================
st.divider()
st.title("📊 Deep Stock Analysis")

selected_symbol = st.selectbox("Select Stock", df["Symbol"].unique())
stock_df = df[df["Symbol"]==selected_symbol].sort_values("Tanggal")

if len(stock_df)>0:
    latest = stock_df.iloc[-1]

    entry = latest["Close"]
    stop = entry - (latest["ATR_RATIO"] * entry)
    target = entry + ((entry - stop) * reward_ratio)
    rr = (target-entry)/(entry-stop)

    weekly_conf = latest["ml_confidence_label_weekly"]
    monthly_conf = latest["ml_confidence_label_monthly"]

    if weekly_conf > weekly_th and monthly_conf > monthly_th and rr >= 2:
        status="STRONG BUY"; color="green"
    elif weekly_conf > weekly_th and monthly_conf > monthly_th:
        status="BUY"; color="green"
    elif weekly_conf > weekly_th:
        status="HOLD"; color="orange"
    else:
        status="WAIT"; color="red"

    trend = "BULLISH" if weekly_conf > monthly_conf else "NEUTRAL"

    if latest["VOL_REGIME"] < 1:
        vol_status="LOW"
    elif latest["VOL_REGIME"] < 2:
        vol_status="MEDIUM"
    else:
        vol_status="HIGH"

    st.markdown(f"""
    <div class="ai-box">
    <b>AI STATUS:</b> <span style="color:{color}; font-size:20px;"><b>{status}</b></span><br>
    <b>Trend:</b> {trend}<br>
    <b>Vol Regime:</b> {vol_status}<br>
    <b>Risk/Reward:</b> {rr:.2f}<br>
    <b>Entry:</b> {entry:.0f}<br>
    <b>Stop:</b> {stop:.0f}<br>
    <b>Target:</b> {target:.0f}
    </div>
    """, unsafe_allow_html=True)

    st.subheader("📈 Price Chart")
    st.line_chart(stock_df.set_index("Tanggal")["Close"])

    st.subheader("🤖 Confidence Trend")
    st.line_chart(
        stock_df.set_index("Tanggal")[
            ["ml_confidence_label_weekly","ml_confidence_label_monthly"]
        ]
    )

st.divider()
st.caption("SahamAI Quant Institutional – Full System © 2026")
