import pandas as pd

df = pd.read_csv("data/raw/sp500_companies.csv")
print(f"Total tickers: {len(df)}")
print(f"\nColumns: {df.columns.tolist()}")
print(f"\nSector breakdown:")
print(df["Sector"].value_counts())
print(f"\nSample rows:")
print(df[["Symbol", "Sector"]].head(10))
