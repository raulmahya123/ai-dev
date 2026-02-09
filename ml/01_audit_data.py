import pandas as pd

DATA_PATH = "processed/daily_clean.parquet"

df = pd.read_parquet(DATA_PATH)

print("Jumlah baris:", len(df))
print("Kolom data:")
print(df.columns)

print("\nContoh data:")
print(df.head())
