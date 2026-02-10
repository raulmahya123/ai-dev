import pandas as pd

DATA_PATH = "../processed/daily_clean.parquet"
ML_PATH   = "../processed/ml_confidence_label_daily.parquet"

INITIAL_CAPITAL = 100_000_000

TP_PCT = 0.06
SL_PCT = 0.04
HOLDING_DAYS = 3          # daily itu cepat

MIN_ML_CONF  = 0.60       # ML = izin main
MIN_AI_SCORE = 60         # proxy sementara

VOL_SPIKE_MULT = 1.5      # 🔥 TRIGGER UTAMA DAILY

print("📥 Loading data...")

df = pd.read_parquet(DATA_PATH)
ml_df = pd.read_parquet(ML_PATH)

df = df.merge(
    ml_df,
    on=["Symbol", "Tanggal Perdagangan Terakhir"],
    how="left"
)

df = df.sort_values("Tanggal Perdagangan Terakhir").reset_index(drop=True)

print(f"✅ Rows: {len(df)} | Symbols: {df['Symbol'].nunique()}")

print("🛠️ Building VOL_MA20...")

df["VOL_MA20"] = (
    df
    .groupby("Symbol")["Volume"]
    .rolling(20)
    .mean()
    .reset_index(level=0, drop=True)
)

required_cols = ["Volume", "VOL_MA20", "Bandar", "Close", "High", "Low"]
missing = [c for c in required_cols if c not in df.columns]

if missing:
    raise ValueError(f"❌ Kolom wajib tidak ada: {missing}")

unique_dates = df["Tanggal Perdagangan Terakhir"].unique()

if len(unique_dates) <= HOLDING_DAYS:
    raise ValueError("❌ Data tidak cukup untuk forward test")

recommendation_date = unique_dates[-(HOLDING_DAYS + 1)]
print(f"\n📅 Tanggal Rekomendasi: {recommendation_date}")

df_today = df[df["Tanggal Perdagangan Terakhir"] == recommendation_date]

if df_today.empty:
    raise ValueError("❌ Tidak ada data di tanggal rekomendasi")


recommendations = []

for _, row in df_today.iterrows():

    # 1️⃣ Bandar filter
    if row["Bandar"] == "DISTRIBUSI":
        continue

    # 2️⃣ ML filter (izin masuk)
    ml_conf = row.get("ml_confidence_label_daily")
    if pd.isna(ml_conf) or ml_conf < MIN_ML_CONF:
        continue

    # 3️⃣ 🔥 VOLUME SPIKE = ENTRY TRIGGER DAILY
    if pd.isna(row["VOL_MA20"]) or row["Volume"] < row["VOL_MA20"] * VOL_SPIKE_MULT:
        continue

    # 4️⃣ AI score (sementara proxy)
    ai_score = 65
    if ai_score < MIN_AI_SCORE:
        continue

    recommendations.append(row["Symbol"])

recommendations = sorted(set(recommendations))

print(f"📌 Total Rekomendasi (Volume Spike): {len(recommendations)}")

if not recommendations:
    print("⚠️ Tidak ada saham yang memenuhi kriteria daily volume spike.")
    exit()

capital_per_stock = INITIAL_CAPITAL / len(recommendations)
results = []

for symbol in recommendations:

    d = (
        df[df["Symbol"] == symbol]
        .sort_values("Tanggal Perdagangan Terakhir")
        .reset_index(drop=True)
    )

    idx = d.index[
        d["Tanggal Perdagangan Terakhir"] == recommendation_date
    ].tolist()

    if not idx:
        continue

    i = idx[0]
    entry_price = d.loc[i, "Close"]

    future = d.loc[i + 1 : i + HOLDING_DAYS]
    if future.empty:
        continue

    tp_price = entry_price * (1 + TP_PCT)
    sl_price = entry_price * (1 - SL_PCT)

    exit_price = None
    result = "TIMEOUT"

    for _, f in future.iterrows():
        if f["Low"] <= sl_price:
            exit_price = sl_price
            result = "SL"
            break
        if f["High"] >= tp_price:
            exit_price = tp_price
            result = "TP"
            break

    if exit_price is None:
        exit_price = future.iloc[-1]["Close"]

    qty = capital_per_stock / entry_price
    pnl = (exit_price - entry_price) * qty

    results.append({
        "Symbol": symbol,
        "Entry": round(entry_price, 0),
        "Exit": round(exit_price, 0),
        "Result": result,
        "PNL": round(pnl, 0)
    })

res_df = pd.DataFrame(results)

if res_df.empty:
    print("\n⚠️ Tidak ada trade yang bisa dievaluasi.")
    exit()

total_pnl = res_df["PNL"].sum()
final_capital = INITIAL_CAPITAL + total_pnl
winrate = (res_df["PNL"] > 0).mean() * 100

print("\n================ HASIL PER SAHAM =================\n")
print(res_df)

print("\n================ SUMMARY =========================\n")
print(f"Modal Awal     : {INITIAL_CAPITAL:,.0f}")
print(f"Modal Akhir    : {final_capital:,.0f}")
print(f"Total PNL      : {total_pnl:,.0f}")
print(f"Winrate        : {winrate:.2f}%")

print("\nBreakdown Result:")
print(res_df["Result"].value_counts())

OUTPUT_PATH = "test_recommendation_daily_volume_spike_result.csv"
res_df.to_csv(OUTPUT_PATH, index=False)
print(f"\n📁 Saved: {OUTPUT_PATH}")

print("\n✅ TEST SELESAI.")