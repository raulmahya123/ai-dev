import pandas as pd

from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score
from sklearn.impute import SimpleImputer
from sklearn.pipeline import Pipeline

# =========================
# CONFIG
# =========================
DATA_PATH = "ml/dataset_ml_ready.parquet"

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

# TRAIN SEMUA TIMEFRAME
TARGETS = [
    "label_daily",
    "label_weekly",
    "label_monthly"
]

# =========================
# LOAD DATA
# =========================
df = pd.read_parquet(DATA_PATH)

print("Total data:", len(df))
print("Kolom tersedia:", df.columns.tolist())

# =========================
# LOOP TRAINING
# =========================
for TARGET in TARGETS:

    print("\n===================================")
    print(f"TRAINING ML → {TARGET.upper()}")
    print("===================================")

    X = df[FEATURES]
    y = df[TARGET]

    print("\nTarget distribution:")
    print(y.value_counts(normalize=True))

    # =========================
    # TRAIN / TEST SPLIT
    # =========================
    X_train, X_test, y_train, y_test = train_test_split(
        X,
        y,
        test_size=0.2,
        random_state=42,
        stratify=y
    )

    # =========================
    # PIPELINE
    # =========================
    pipeline = Pipeline([
        ("imputer", SimpleImputer(strategy="median")),
        ("scaler", StandardScaler()),
        ("model", LogisticRegression(
            max_iter=1000,
            class_weight="balanced"
        ))
    ])

    # =========================
    # TRAIN
    # =========================
    pipeline.fit(X_train, y_train)

    # =========================
    # EVALUATION
    # =========================
    proba_test = pipeline.predict_proba(X_test)[:, 1]
    auc = roc_auc_score(y_test, proba_test)

    print(f"AUC Score ({TARGET}): {auc:.4f}")

    # =========================
    # FEATURE IMPORTANCE
    # =========================
    coef = pipeline.named_steps["model"].coef_[0]
    importance = (
        pd.Series(coef, index=FEATURES)
        .sort_values(ascending=False)
    )

    print("\nFeature importance:")
    print(importance)

    # =========================
    # SAVE CONFIDENCE
    # =========================
    conf_col = f"ml_confidence_{TARGET}"
    df[conf_col] = pipeline.predict_proba(X)[:, 1]

    df_out = df[[
        "Symbol",
        "Tanggal Perdagangan Terakhir",
        conf_col
    ]]

    output_path = f"processed/ml_confidence_{TARGET}.parquet"
    df_out.to_parquet(output_path, index=False)

    print(f"\nML confidence saved → {output_path}")
    print("Sample:")
    print(df_out.head())

print("\n✅ SEMUA MODEL SELESAI")
