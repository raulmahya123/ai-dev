import pandas as pd
import os

os.makedirs("processed", exist_ok=True)

df = pd.DataFrame(columns=[
    "Tanggal",
    "Mode",
    "Saham",
    "Status",
    "Entry",
    "TP",
    "SL",
    "Catatan"
])

df.to_parquet("processed/recommendation_history.parquet", index=False)

print("✅ processed/recommendation_history.parquet BERHASIL DIBUAT")
