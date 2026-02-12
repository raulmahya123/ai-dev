import streamlit as st
import pandas as pd
import numpy as np
import joblib
import altair as alt
from ui.styles import load_css


# =========================================================
# PAGE CONFIG
# =========================================================
st.set_page_config(
    page_title="SahamAI Quant Institutional",
    page_icon="📊",
    layout="wide"
)

# =========================
# CUSTOM LAYOUT
# =========================
sidebar, main = st.columns([1.2, 5], gap="small")

# =========================================================
# LOAD CSS STYLES
# =========================================================
load_css()

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
# SIDEBAR (CLEAN VERSION)
# =========================================================

with st.sidebar:

    st.image("assets/logo.png", width=150)

    st.markdown("## SahamAI Quant")
    st.markdown(
        "<p style='opacity:0.7; font-size:13px; margin-top:-10px;'>Institutional Trading System</p>",
        unsafe_allow_html=True
    )

    st.markdown("---")

    # ================= FILTER =================
    st.markdown("### 📅 Filter Tanggal")

    selected_date = st.date_input(
        "Tanggal",
        value=df["Tanggal"].max()
    )

    st.markdown("### ⚙ Mode Analisis")

    mode = st.radio(
        "Mode",
        ["Harian", "1 Bulan", "Tahunan"]
    )

    st.markdown("---")

    # ================= CAPITAL =================
    st.markdown("### 💰 Manajemen Modal")

    capital = st.number_input(
        "Total Capital",
        100_000_000
    )

    risk_pct = st.slider(
        "Risk per Trade (%)",
        0.5, 5.0, 2.0
    )

    reward_ratio = st.slider(
        "Risk Reward Ratio",
        1.0, 5.0, 2.0
    )

    max_positions = st.slider(
        "Max Positions",
        1, 15, 5
    )

    vol_filter = st.slider(
        "Max Vol Regime",
        0.5, 3.0, 1.8
    )

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

st.markdown("""
<div class="section-header">
    <h1>🟢 Eligible Watchlist</h1>
    <p>Daftar saham yang memenuhi kriteria AI confidence & risk filter</p>
</div>
""", unsafe_allow_html=True)

watch_display = eligible[[
    "Symbol","Entry","Stop_Loss","Target",
    "RR","Score","Recommendation"
]].copy()

# ================= SUMMARY METRICS =================

st.markdown('<div class="metric-row">', unsafe_allow_html=True)
total_stock = len(watch_display)
strong_buy = (watch_display["Recommendation"] == "STRONG BUY").sum()
avg_score = watch_display["Score"].mean()

col1, col2, col3 = st.columns(3)

with col1:
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-label">Total Eligible</div>
        <div class="metric-value">{total_stock}</div>
    </div>
    """, unsafe_allow_html=True)

with col2:
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-label">Strong Buy</div>
        <div class="metric-value">{strong_buy}</div>
    </div>
    """, unsafe_allow_html=True)

with col3:
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-label">Average Score</div>
        <div class="metric-value">{avg_score:.2f}</div>
    </div>
    """, unsafe_allow_html=True)

st.markdown('</div>', unsafe_allow_html=True)

# ================= FORMAT ANGKA =================
watch_display["Entry"] = watch_display["Entry"].map("{:,.0f}".format)
watch_display["Stop_Loss"] = watch_display["Stop_Loss"].map("{:,.0f}".format)
watch_display["Target"] = watch_display["Target"].map("{:,.0f}".format)
watch_display["RR"] = watch_display["RR"].map("{:.2f}".format)
watch_display["Score"] = watch_display["Score"].map("{:.2f}".format)

# ================= STYLING RECOMMENDATION =================
def color_recommendation(val):
    if val == "STRONG BUY":
        return "background-color:#052e16; color:#4ade80; font-weight:600;"
    elif val == "BUY":
        return "background-color:#064e3b; color:#34d399; font-weight:600;"
    elif val == "HOLD":
        return "background-color:#78350f; color:#facc15; font-weight:600;"
    else:
        return "background-color:#450a0a; color:#f87171; font-weight:600;"

styled_df = watch_display.style.applymap(
    color_recommendation,
    subset=["Recommendation"]
)

st.dataframe(styled_df, use_container_width=True)


# =========================================================
# PORTFOLIO – CLEAN PROFESSIONAL VERSION
# =========================================================

signals = eligible.head(max_positions).copy()
risk_amount = capital * (risk_pct / 100)

signals["Position_Size"] = np.floor(risk_amount / signals["Risk"])
signals["Capital_Used"] = signals["Position_Size"] * signals["Entry"]

total_used = signals["Capital_Used"].sum()
remaining_cash = capital - total_used

st.markdown("<div style='height:30px'></div>", unsafe_allow_html=True)

st.markdown("""
<div class="section-header">
    <h1>🏦 Portfolio Allocation</h1>
    <p>Simulasi alokasi berdasarkan risk per trade</p>
</div>
""", unsafe_allow_html=True)

# ================= METRIC CARDS =================

st.markdown('<div class="metric-row">', unsafe_allow_html=True)

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-label">Total Capital</div>
        <div class="metric-value">{capital:,.0f}</div>
    </div>
    """, unsafe_allow_html=True)

with col2:
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-label">Used Capital</div>
        <div class="metric-value">{total_used:,.0f}</div>
    </div>
    """, unsafe_allow_html=True)

with col3:
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-label">Remaining Cash</div>
        <div class="metric-value">{remaining_cash:,.0f}</div>
    </div>
    """, unsafe_allow_html=True)

with col4:
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-label">Positions</div>
        <div class="metric-value">{len(signals)}</div>
    </div>
    """, unsafe_allow_html=True)

st.markdown('</div>', unsafe_allow_html=True)

st.markdown("<div style='height:30px'></div>", unsafe_allow_html=True)

# ================= FORMAT DATA =================

display_portfolio = signals[[
    "Symbol","Entry","Stop_Loss","Target",
    "Position_Size","Capital_Used","Recommendation"
]].copy()

display_portfolio["Entry"] = display_portfolio["Entry"].map("{:,.0f}".format)
display_portfolio["Stop_Loss"] = display_portfolio["Stop_Loss"].map("{:,.0f}".format)
display_portfolio["Target"] = display_portfolio["Target"].map("{:,.0f}".format)
display_portfolio["Capital_Used"] = display_portfolio["Capital_Used"].map("{:,.0f}".format)
display_portfolio["Position_Size"] = display_portfolio["Position_Size"].map("{:,.0f}".format)

# ================= RECOMMENDATION COLOR =================

def highlight_recommendation(val):
    if val == "STRONG BUY":
        return "color:#22c55e; font-weight:600;"
    elif val == "BUY":
        return "color:#10b981; font-weight:600;"
    elif val == "HOLD":
        return "color:#facc15; font-weight:600;"
    else:
        return "color:#ef4444; font-weight:600;"

styled_portfolio = display_portfolio.style.applymap(
    highlight_recommendation,
    subset=["Recommendation"]
)

st.dataframe(
    styled_portfolio,
    use_container_width=True,
    height=350
)


# =========================================================
# ALLOCATION CHART
# =========================================================
st.markdown("## 📊 Allocation Breakdown")

if len(signals) > 0:

    chart_df = signals[["Symbol", "Capital_Used"]].copy()

    bar_chart = alt.Chart(chart_df).mark_bar(
        cornerRadiusTopLeft=6,
        cornerRadiusTopRight=6
    ).encode(
        x=alt.X("Symbol:N", sort='-y', title="Symbol"),
        y=alt.Y("Capital_Used:Q", title="Capital Used"),
        tooltip=["Symbol", "Capital_Used"]
    ).properties(
        height=350
    ).configure_axis(
        labelColor="#374151",
        titleColor="#374151"
    ).configure_view(
        strokeWidth=0
    )

    st.altair_chart(bar_chart, use_container_width=True)


# =========================================================
# EQUITY PREVIEW
# =========================================================
st.markdown("## 📈 Equity Simulation (Preview)")

equity = capital
curve = []

for i in range(30):
    equity *= (1 + np.random.normal(0.0015, 0.01))
    curve.append(equity)

equity_df = pd.DataFrame({
    "Day": range(1, 31),
    "Equity": curve
})

line_chart = alt.Chart(equity_df).mark_line(
    interpolate="monotone",
    strokeWidth=3
).encode(
    x=alt.X("Day:Q"),
    y=alt.Y("Equity:Q"),
    tooltip=["Day", "Equity"]
).properties(
    height=350
).configure_axis(
    labelColor="#374151",
    titleColor="#374151"
).configure_view(
    strokeWidth=0
)

st.altair_chart(line_chart, use_container_width=True)

# =========================================================
# DEEP ANALYSIS + AI PANEL (ENHANCED UI)
# =========================================================
st.divider()

st.markdown("""
<div class="section-header">
    <h1>📊 Deep Stock Analysis</h1>
    <p>Analisis mendalam berbasis AI confidence & volatility regime</p>
</div>
""", unsafe_allow_html=True)

st.markdown("#### 📌 Pilih Saham")

selected_symbol = st.selectbox(
    "",
    sorted(df["Symbol"].unique()),
    key="symbol_selector"
)

stock_df = df[df["Symbol"] == selected_symbol].sort_values("Tanggal")

if len(stock_df) > 0:

    latest = stock_df.iloc[-1]

    entry = latest["Close"]
    stop = entry - (latest["ATR_RATIO"] * entry)
    target = entry + ((entry - stop) * reward_ratio)
    rr = (target - entry) / (entry - stop)

    weekly_conf = latest["ml_confidence_label_weekly"]
    monthly_conf = latest["ml_confidence_label_monthly"]

    if weekly_conf > weekly_th and monthly_conf > monthly_th and rr >= 2:
        status = "STRONG BUY"
    elif weekly_conf > weekly_th and monthly_conf > monthly_th:
        status = "BUY"
    elif weekly_conf > weekly_th:
        status = "HOLD"
    else:
        status = "WAIT"

    trend = "BULLISH" if weekly_conf > monthly_conf else "NEUTRAL"

    if latest["VOL_REGIME"] < 1:
        vol_status = "LOW"
    elif latest["VOL_REGIME"] < 2:
        vol_status = "MEDIUM"
    else:
        vol_status = "HIGH"

    status_color = {
        "STRONG BUY": "#22c55e",
        "BUY": "#10b981",
        "HOLD": "#facc15",
        "WAIT": "#ef4444"
    }

    # ================= AI PANEL =================
    # ================= AI CARD =================

    status_color = {
        "STRONG BUY": "#22c55e",
        "BUY": "#10b981",
        "HOLD": "#facc15",
        "WAIT": "#ef4444"
    }

    st.markdown('<div class="ai-card">', unsafe_allow_html=True)

    # ===== HEADER BADGE =====
    st.markdown(
        f"""
        <div class="ai-card-header">
            <span class="ai-status-badge"
                style="background:{status_color[status]}20;
                        color:{status_color[status]};">
                {status}
            </span>
        </div>
        """,
        unsafe_allow_html=True
    )

    # ===== GRID CONTENT =====
    col1, col2, col3 = st.columns(3)
    col4, col5, col6 = st.columns(3)

    col1.markdown(f"<div class='ai-item'><span>Trend</span><b>{trend}</b></div>", unsafe_allow_html=True)
    col2.markdown(f"<div class='ai-item'><span>Volatility</span><b>{vol_status}</b></div>", unsafe_allow_html=True)
    col3.markdown(f"<div class='ai-item'><span>Risk / Reward</span><b>{rr:.2f}</b></div>", unsafe_allow_html=True)

    col4.markdown(f"<div class='ai-item'><span>Entry</span><b>{entry:,.0f}</b></div>", unsafe_allow_html=True)
    col5.markdown(f"<div class='ai-item'><span>Stop</span><b>{stop:,.0f}</b></div>", unsafe_allow_html=True)
    col6.markdown(f"<div class='ai-item'><span>Target</span><b>{target:,.0f}</b></div>", unsafe_allow_html=True)

    st.markdown('</div>', unsafe_allow_html=True)

    # =====================================================
    # PRICE CHART
    # =====================================================

    st.markdown("### 📈 Price Chart")

    price_chart = (
        alt.Chart(stock_df)
        .mark_line(
            strokeWidth=3,
            interpolate="monotone",
            color="#166534"
        )
        .encode(
            x=alt.X("Tanggal:T", title="Tanggal"),
            y=alt.Y("Close:Q", title="Price"),
            tooltip=["Tanggal:T", "Close:Q"]
        )
        .properties(height=350)
    )

    st.altair_chart(price_chart, use_container_width=True)

    # =====================================================
    # CONFIDENCE CHART (FIXED VERSION)
    # =====================================================

    st.markdown("### 🤖 Confidence Trend")

    conf_df = stock_df[[
        "Tanggal",
        "ml_confidence_label_weekly",
        "ml_confidence_label_monthly"
    ]].copy()

    # Rename agar lebih clean
    conf_df = conf_df.rename(columns={
        "ml_confidence_label_weekly": "Weekly",
        "ml_confidence_label_monthly": "Monthly"
    })

    conf_melt = conf_df.melt(
        id_vars="Tanggal",
        var_name="Confidence",
        value_name="Score"
    )

    conf_chart = (
        alt.Chart(conf_melt)
        .mark_line(strokeWidth=2)
        .encode(
            x=alt.X("Tanggal:T", title="Tanggal"),
            y=alt.Y("Score:Q", title="Confidence Score"),
            color=alt.Color("Confidence:N"),
            tooltip=["Tanggal:T", "Confidence:N", "Score:Q"]
        )
        .properties(height=300)
    )

    st.altair_chart(conf_chart, use_container_width=True)

st.divider()

st.caption("SahamAI Quant Institutional – Full System © 2026")
