import pandas as pd
import numpy as np
import os

from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score
from sklearn.impute import SimpleImputer
from sklearn.pipeline import Pipeline

# =====================================================
# CONFIG
# =====================================================
DATA_PATH = "ml/dataset_ml_ready.parquet"
OUT_DIR = "processed"
os.makedirs(OUT_DIR, exist_ok=True)

FEATURES = [
    "EMA10",
    "EMA20",
    "EMA50",
    "RSI14",
    "VOL_RATIO",
    "DIST_SUPPORT",
    "DIST_RESISTANCE",
    "BANDAR_ENC"
]

TARGETS = [
    "label_daily",
    "label_weekly",
    "label_monthly"
]

# =====================================================
# LOAD DATA
# =====================================================
df = pd.read_parquet(DATA_PATH)

# konsistensi kolom
df = df.rename(columns={
    "Saham": "Symbol",
    "Tanggal": "Tanggal"
})

df = df.sort_values(["Symbol", "Tanggal"]).reset_index(drop=True)

print("📊 Total data:", len(df))
print("📈 Total saham:", df["Symbol"].nunique())

# =====================================================
# TIME-BASED SPLIT (80% train, 20% test by time)
# =====================================================
split_date = df["Tanggal"].quantile(0.80)

train_df = df[df["Tanggal"] <= split_date]
test_df  = df[df["Tanggal"] > split_date]

X_train = train_df[FEATURES]
X_test  = test_df[FEATURES]

print("🧪 Train rows:", len(train_df))
print("🧪 Test rows :", len(test_df))

# =====================================================
# PIPELINE (REUSABLE)
# =====================================================
pipeline = Pipeline([
    ("imputer", SimpleImputer(strategy="median")),
    ("scaler", StandardScaler()),
    ("model", LogisticRegression(
        max_iter=1000,
        class_weight="balanced",
        n_jobs=-1
    ))
])

# =====================================================
# LOOP TRAINING
# =====================================================
for TARGET in TARGETS:

    print("\n===================================")
    print(f"🤖 TRAINING → {TARGET.upper()}")
    print("===================================")

    y_train = train_df[TARGET]
    y_test  = test_df[TARGET]

    print("Target distribution (train):")
    print(y_train.value_counts(normalize=True).round(3))

    # =========================
    # TRAIN
    # =========================
    pipeline.fit(X_train, y_train)

    # =========================
    # EVALUATION (TEST ONLY)
    # =========================
    proba_test = pipeline.predict_proba(X_test)[:, 1]
    auc = roc_auc_score(y_test, proba_test)

    print(f"🎯 AUC ({TARGET}): {auc:.4f}")

    # =========================
    # FEATURE IMPORTANCE
    # =========================
    coef = pipeline.named_steps["model"].coef_[0]
    importance = (
        pd.Series(coef, index=FEATURES)
        .sort_values(ascending=False)
    )

    print("\n🧠 Feature importance:")
    print(importance.round(3))

    # =========================
    # GENERATE ML CONFIDENCE (FULL DATA, AFTER TRAIN)
    # =========================
    conf_col = f"ml_confidence_{TARGET}"
    df[conf_col] = pipeline.predict_proba(df[FEATURES])[:, 1]

    df_out = df[[
        "Symbol",
        "Tanggal",
        conf_col
    ]]

    output_path = f"{OUT_DIR}/ml_confidence_{TARGET}.parquet"
    df_out.to_parquet(output_path, index=False)

    print(f"\n💾 ML confidence saved → {output_path}")
    print(df_out.head())

print("\n✅ SEMUA MODEL SELESAI (TIME-SERIES SAFE)")
    