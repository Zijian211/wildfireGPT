import pandas as pd
import os

print("⏳ Reading huge CSV file...")
# Read the big file
df = pd.read_csv('data/wildfire_literature.csv')

print("📦 Compressing to .gz...")
# Save it as a compressed GZIP file
df.to_csv('data/wildfire_literature.csv.gz', index=False, compression='gzip')

print("✅ Done! New file created: data/wildfire_literature.csv.gz")