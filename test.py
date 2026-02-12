import pandas as pd

ml = pd.read_parquet("processed/ml_confidence_label_daily.parquet")
print(ml.columns)
print(ml.head())
print(ml.dtypes)
