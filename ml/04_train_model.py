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

# GANTI SESUAI RUN:
# label_daily | label_weekly | label_monthly
TARGET = "label_monthly"

OUTPUT_PATH = f"processed/ml_confidence_{TARGET}.parquet"

# =========================
# LOAD DATA
# =========================
df = pd.read_parquet(DATA_PATH)

X = df[FEATURES]
y = df[TARGET]

print("Jumlah data:", len(df))
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
# PIPELINE (IMPUTE + SCALE + MODEL)
# =========================
pipeline = Pipeline([
    ("imputer", SimpleImputer(strategy="median")),
    ("scaler", StandardScaler()),
    ("model", LogisticRegression(
        max_iter=1000,
        class_weight="balanced",
        n_jobs=-1
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

print(f"\nAUC Score ({TARGET}): {auc:.4f}")

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
# SAVE CONFIDENCE (FULL DATA)
# =========================
df[f"ml_confidence_{TARGET}"] = pipeline.predict_proba(X)[:, 1]

df_out = df[[
    "Symbol",
    "Tanggal Perdagangan Terakhir",
    f"ml_confidence_{TARGET}"
]]

df_out.to_parquet(OUTPUT_PATH, index=False)

print(f"\nML confidence saved → {OUTPUT_PATH}")
print("\nSample:")
print(df_out.head())
