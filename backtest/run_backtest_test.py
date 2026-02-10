# ============================================================
# BACKTEST TEST RUNNER – DAILY (WITH ML)
# ============================================================

import pandas as pd
from backtest_daily_engine import backtest_daily_capital


# ============================================================
# PATH CONFIG
# ============================================================

DATA_PATH = "../processed/daily_clean.parquet"
ML_DAILY_PATH = "../processed/ml_confidence_label_daily.parquet"
OUTPUT_PATH = "backtest_result_daily.csv"


# ============================================================
# LOAD MAIN DATA
# ============================================================

print("📥 Loading daily price data...")
df = pd.read_parquet(DATA_PATH)

print(f"✅ Daily data loaded | rows={len(df)} | symbols={df['Symbol'].nunique()}")


# ============================================================
# LOAD & MERGE ML DAILY CONFIDENCE
# ============================================================

print("📥 Loading ML daily confidence...")
ml_df = pd.read_parquet(ML_DAILY_PATH)

required_cols = {
    "Symbol",
    "Tanggal Perdagangan Terakhir",
    "ml_confidence_label_daily"
}

missing = required_cols - set(ml_df.columns)
if missing:
    raise ValueError(f"❌ ML file missing columns: {missing}")

df = df.merge(
    ml_df[
        ["Symbol", "Tanggal Perdagangan Terakhir", "ml_confidence_label_daily"]
    ],
    on=["Symbol", "Tanggal Perdagangan Terakhir"],
    how="left"
)

print("✅ ML daily confidence merged")


# ============================================================
# AI SCORE MAP (TEST MODE)
# NOTE:
# - sementara pakai nilai flat
# - nanti bisa diganti AI_SCORE_MAP asli
# ============================================================

ai_score_map = {
    s: 65 for s in df["Symbol"].unique()
}

print("🤖 AI score map ready (test mode)")


# ============================================================
# RUN BACKTEST
# ============================================================

print("\n🚀 Running backtest...\n")

trades_df, summary = backtest_daily_capital(
    df=df,
    ai_score_map=ai_score_map,
    initial_capital=100_000_000,
    risk_per_trade=0.01,        # 1% risk per trade (AMAN BUAT TEST)
    tp_pct=0.06,
    sl_pct=0.04,
    max_holding_days=5,
    min_ai_score=60
)


# ============================================================
# HANDLE EMPTY RESULT
# ============================================================

if trades_df is None or trades_df.empty:
    print("❌ Tidak ada trade yang terjadi.")
    print("👉 Cek threshold ML / AI / data Bandar.")
    exit()


# ============================================================
# SUMMARY OUTPUT
# ============================================================

print("================ BACKTEST SUMMARY ================\n")
for k, v in summary.items():
    print(f"{k}: {v}")

print("\n================ TRADE RESULT COUNT ================\n")
print(trades_df["Result"].value_counts())

print("\n================ SAMPLE TRADES (FIRST 10) ==========\n")
print(trades_df.head(10))

print("\n================ SAMPLE TRADES (LAST 10) ============\n")
print(trades_df.tail(10))


# ============================================================
# SAVE RESULT
# ============================================================

trades_df.to_csv(OUTPUT_PATH, index=False)
print(f"\n📁 Backtest result saved to: {OUTPUT_PATH}")


# ============================================================
# QUICK SANITY CHECK
# ============================================================

print("\n================ SANITY CHECK ======================\n")
print("Avg ML Confidence:",
        round(trades_df["ML Conf"].mean(), 3))
print("Max Equity:", trades_df["Equity"].max())
print("Min Equity:", trades_df["Equity"].min())

print("\n✅ DONE.")
