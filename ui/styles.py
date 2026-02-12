import streamlit as st

def load_css():
    st.markdown("""
    <style>

    /* ================= GLOBAL ================= */
    .stApp {
        background-color:#f4f6f9;
        font-family: 'Segoe UI', sans-serif;
        color:#212529;
    }

    h1,h2,h3 {
        font-weight:600;
        letter-spacing:0.5px;
    }

    h1 { color:#146c43; }
    h2,h3 { color:#198754; }

/* ================= SIDEBAR CLEAN ================= */

    [data-testid="stSidebar"] {
        background: linear-gradient(180deg,#14532d,#166534);
        padding:25px 20px;
    }

    [data-testid="stSidebar"] * {
        color:white !important;
    }

    /* Title */
    [data-testid="stSidebar"] h2 {
        margin-bottom:5px;
    }

    [data-testid="stSidebar"] h3 {
        margin-top:20px;
        margin-bottom:10px;
        font-size:15px !important;
    }

    /* Divider */
    [data-testid="stSidebar"] hr {
        border-color: rgba(255,255,255,0.15);
    }

    /* Input field */
    [data-testid="stSidebar"] input {
        background-color: rgba(255,255,255,0.1) !important;
        border-radius:10px !important;
        border:1px solid rgba(255,255,255,0.15) !important;
    }

    /* Radio spacing */
    div[role="radiogroup"] {
        gap:6px;
    }

    div[role="radiogroup"] label {
        padding:6px 8px;
        border-radius:8px;
    }

    /* Slider color */
    [data-testid="stSidebar"] .stSlider > div > div > div > div {
        background-color:#4ade80 !important;
    }

                
/* =======================================================
   CUSTOM METRIC CARD (STABLE VERSION)
======================================================= */

.metric-card {
    background: white;
    border-radius: 14px;
    padding: 22px;
    box-shadow: 0 8px 20px rgba(0,0,0,0.06);
}

.metric-label {
    font-size: 13px;
    color: #6b7280;
    margin-bottom: 6px;
    font-weight: 500;
}

.metric-value {
    font-size: 28px;
    font-weight: 700;
    color: #111827;
}

/* ================= SPACING FIX ================= */

.metric-row {
    margin-bottom: 30px;
}

/* ================= CHART CARD ================= */

.chart-card {
    background: white;
    border-radius: 16px;
    padding: 20px;
    box-shadow: 0 8px 20px rgba(0,0,0,0.06);
    margin-bottom: 40px;
}


    /* ================= DATAFRAME ================= */
    thead tr th {
        background-color:#198754 !important;
        color:white !important;
        font-weight:600;
        text-align:center;
    }

    tbody tr:nth-child(even) {
        background-color:#f1fdf6 !important;
    }

    tbody tr:hover {
        background-color:#d1f2e0 !important;
        transition:0.2s;
    }

    /* ================= AI BOX ================= */
    .ai-box {
        background:white;
        padding:25px;
        border-radius:16px;
        border-left:6px solid #198754;
        box-shadow:0 6px 18px rgba(0,0,0,0.08);
        line-height:1.8;
        font-size:16px;
    }

    /* ================= SECTION SPACING ================= */
    .block-container {
        padding-top:2rem;
        padding-bottom:2rem;
        padding-left:2rem;
        padding-right:2rem;
    }

    /* ================= SLIDER ================= */
    .stSlider > div > div > div > div {
        background-color:#198754 !important;
    }

    /* ================= BUTTON ================= */
    .stButton>button {
        background-color:#198754;
        color:white;
        border-radius:10px;
        border:none;
        padding:8px 16px;
        transition:0.3s;
    }

    .stButton>button:hover {
        background-color:#146c43;
    }

    /* ================= SECTION HEADER ================= */

    .section-header h1 {
        margin-bottom:4px;
    }

    .section-header p {
        opacity:0.7;
        margin-top:0;
        margin-bottom:15px;
    }

    /* ================= DATAFRAME STYLE ================= */

    thead tr th {
        background-color:#111827 !important;
        color:#e5e7eb !important;
        font-weight:600;
        text-align:center;
    }

    tbody tr:nth-child(even) {
        background-color:#0f172a !important;
    }

    tbody tr:hover {
        background-color:#1e293b !important;
        transition:0.2s;
    }

/* ================= DEEP ANALYSIS CLEAN ================= */

.section-header {
    margin-bottom: 20px;
}

/* STATUS BADGE */
.ai-status-wrapper {
    margin-bottom: 20px;
}

.ai-status-badge {
    padding: 8px 22px;
    border-radius: 30px;
    font-weight: 700;
    font-size: 13px;
}

/* INFO CARDS */
.ai-item {
    background: #ffffff;
    padding: 18px;
    border-radius: 14px;
    text-align: center;
    border: 1px solid #e5e7eb;
    box-shadow: 0 4px 12px rgba(0,0,0,0.04);
    margin-bottom: 10px;
}

.ai-item span {
    display: block;
    font-size: 12px;
    color: #6b7280;
    margin-bottom: 6px;
}

.ai-item b {
    font-size: 16px;
    color: #111827;
}

/* ================= CLEAN SELECTBOX ================= */

/* Main input container */
div[data-baseweb="select"] > div {
    background-color: #ffffff !important;
    border: 1px solid #d1d5db !important;
    border-radius: 12px !important;
    padding: 2px 6px !important;
    cursor: pointer !important;
    transition: all 0.2s ease;
}

/* Hover */
div[data-baseweb="select"] > div:hover {
    border: 1px solid #16a34a !important;
    box-shadow: 0 0 0 2px rgba(22,163,74,0.15);
}

/* Focus */
div[data-baseweb="select"] > div:focus-within {
    border: 1px solid #16a34a !important;
    box-shadow: 0 0 0 3px rgba(22,163,74,0.20);
}

/* Remove weird internal dark bg */
div[data-baseweb="select"] input {
    background: transparent !important;
    cursor: pointer !important;
}

/* Dropdown menu container */
div[role="listbox"] {
    background-color: #ffffff !important;
    border-radius: 12px !important;
    padding: 6px !important;
    box-shadow: 0 12px 30px rgba(0,0,0,0.15) !important;
    border: 1px solid #e5e7eb !important;
}

/* Each option */
div[role="option"] {
    background-color: #ffffff !important;
    border-radius: 8px !important;
    padding: 8px 12px !important;
    cursor: pointer !important;
    transition: background 0.15s ease;
}

/* Hover option */
div[role="option"]:hover {
    background-color: #ecfdf5 !important;
    color: #065f46 !important;
}

/* Selected option */
div[aria-selected="true"] {
    background-color: #16a34a !important;
    color: #ffffff !important;
    font-weight: 600;
}

/* Fix text color inside options */
div[role="option"] span {
    color: #111827 !important;
}

/* Scrollbar modern */
div[role="listbox"]::-webkit-scrollbar {
    width: 6px;
}

div[role="listbox"]::-webkit-scrollbar-thumb {
    background: #16a34a;
    border-radius: 10px;
}

    </style>
    """, unsafe_allow_html=True)
