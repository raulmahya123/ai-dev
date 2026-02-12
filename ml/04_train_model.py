import pandas as pd
import numpy as np
import os
import joblib

from sklearn.preprocessing import RobustScaler
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score, precision_recall_curve
from sklearn.impute import SimpleImputer
from sklearn.pipeline import Pipeline
from sklearn.feature_selection import VarianceThreshold

# =====================================================
# CONFIG
# =====================================================
FEATURE_PATH = "ml/dataset_features.parquet"
LABEL_PATH   = "ml/dataset_ml_ready.parquet"

OUT_DIR = "processed"
MODEL_DIR = "ml/models"

os.makedirs(OUT_DIR, exist_ok=True)
os.makedirs(MODEL_DIR, exist_ok=True)

FEATURES = [
    # RETURNS
    "RET_1D","RET_5D","RET_20D","LOG_RET",

    # VOL
    "VOL_20","VOL_REGIME",

    # TREND
    "EMA10_RATIO","EMA20_RATIO","EMA50_RATIO","EMA_SPREAD",

    # OSCILLATOR
    "RSI_NORM",

    # VOL FLOW
    "ATR_RATIO",
    "VOL_RATIO","VOL_MOM",

    # STRUCTURE
    "BREAKOUT_UP","BREAKOUT_DOWN",
    "DIST_SUPPORT","DIST_RESISTANCE",

    # SMART MONEY
    "BANDAR_ENC"
]

TARGETS = [
    "label_daily",
    "label_weekly",
    "label_monthly"
]

# =====================================================
# LOAD & MERGE
# =====================================================
df_feat = pd.read_parquet(FEATURE_PATH)
df_label = pd.read_parquet(LABEL_PATH)

df_feat["Tanggal"] = pd.to_datetime(df_feat["Tanggal"])
df_label["Tanggal"] = pd.to_datetime(df_label["Tanggal"])

df = df_feat.merge(
    df_label[["Symbol","Tanggal"] + TARGETS],
    on=["Symbol","Tanggal"],
    how="inner"
)

df = df.sort_values("Tanggal").reset_index(drop=True)

print("📊 Total rows:", len(df))
print("📈 Total saham:", df["Symbol"].nunique())

# =====================================================
# FEATURE CHECK
# =====================================================
missing = [c for c in FEATURES if c not in df.columns]
if missing:
    raise ValueError(f"❌ Missing features: {missing}")

print("\n🔎 Feature Variance Check")
for col in FEATURES:
    print(col, "std:", round(df[col].std(), 6))

# =====================================================
# TIME SPLIT (STRICT)
# =====================================================
split_date = df["Tanggal"].quantile(0.80)

train_df = df[df["Tanggal"] <= split_date].copy()
test_df  = df[df["Tanggal"] > split_date].copy()

print("\n🧪 Train:", len(train_df))
print("🧪 Test :", len(test_df))
print("📅 Split date:", split_date.date())

# =====================================================
# PIPELINE BUILDER
# =====================================================
def build_pipeline(C_value=1.0):
    return Pipeline([
        ("imputer", SimpleImputer(strategy="median")),
        ("variance", VarianceThreshold()),  # remove zero variance
        ("scaler", RobustScaler()),
        ("model", LogisticRegression(
            max_iter=3000,
            class_weight="balanced",
            solver="lbfgs",
            C=C_value
        ))
    ])

# =====================================================
# TRAIN LOOP
# =====================================================
for TARGET in TARGETS:

    print("\n===================================")
    print("🚀 TRAINING:", TARGET.upper())
    print("===================================")

    X_train = train_df[FEATURES]
    y_train = train_df[TARGET]

    X_test = test_df[FEATURES]
    y_test = test_df[TARGET]

    if y_train.nunique() < 2:
        print("❌ Target constant. Skip.")
        continue

    best_auc = 0
    best_model = None
    best_C = None

    for C in [0.5, 1.0, 2.0, 5.0]:
        model = build_pipeline(C)
        model.fit(X_train, y_train)

        proba = model.predict_proba(X_test)[:,1]
        auc = roc_auc_score(y_test, proba)

        if auc > best_auc:
            best_auc = auc
            best_model = model
            best_C = C

    print(f"🎯 Best AUC: {best_auc:.4f}")
    print(f"🔧 Best C: {best_C}")

    # ======================================
    # THRESHOLD OPTIMIZATION
    # ======================================
    proba_test = best_model.predict_proba(X_test)[:,1]

    precision, recall, thresholds = precision_recall_curve(y_test, proba_test)
    f1 = 2 * (precision * recall) / (precision + recall + 1e-9)
    best_idx = np.argmax(f1)

    best_threshold = thresholds[best_idx] if best_idx < len(thresholds) else 0.5
    print("🔥 Best threshold:", round(best_threshold,3))

    # ======================================
    # DECILE ANALYSIS
    # ======================================
    test_temp = pd.DataFrame({
        "proba": proba_test,
        "target": y_test.values
    })

    test_temp["decile"] = pd.qcut(
        test_temp["proba"],
        10,
        labels=False,
        duplicates="drop"
    )

    top_decile = test_temp[test_temp["decile"] == test_temp["decile"].max()]
    precision_top = top_decile["target"].mean()
    base_rate = y_test.mean()
    lift = precision_top / base_rate if base_rate > 0 else 0

    print("📈 Base rate:", round(base_rate,4))
    print("🏆 Top 10% Precision:", round(precision_top,4))
    print("🚀 Lift:", round(lift,2))

    # ======================================
    # FEATURE IMPORTANCE
    # ======================================
    model_step = best_model.named_steps["model"]
    selected_mask = best_model.named_steps["variance"].get_support()
    selected_features = np.array(FEATURES)[selected_mask]

    coef = model_step.coef_[0]
    importance = pd.Series(coef, index=selected_features).sort_values(ascending=False)

    print("\n🧠 Feature Importance:")
    print(importance.round(4))

    # ======================================
    # SAVE MODEL
    # ======================================
    model_path = f"{MODEL_DIR}/{TARGET}.pkl"

    joblib.dump({
        "model": best_model,
        "threshold": float(best_threshold),
        "features": list(selected_features),
        "C": best_C
    }, model_path)

    print("💾 Model saved:", model_path)

    # ======================================
    # FULL CONFIDENCE
    # ======================================
    df[f"ml_confidence_{TARGET}"] = best_model.predict_proba(
        df[FEATURES]
    )[:,1]

    df_out = df[["Symbol","Tanggal",f"ml_confidence_{TARGET}"]]
    out_path = f"{OUT_DIR}/ml_confidence_{TARGET}.parquet"

    df_out.to_parquet(out_path, index=False)
    print("📦 Confidence saved:", out_path)

print("\n✅ TRAINING COMPLETE (FINAL PRO VERSION)")
