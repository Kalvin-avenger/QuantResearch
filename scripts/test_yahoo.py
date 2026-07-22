from quantresearch.data.yahoo import download_price_data


df = download_price_data(
    ticker="AAPL",
    start_date="2020-01-01",
)


print(df.head())

print("\nShape:")
print(df.shape)

print("\nColumns:")
print(df.columns)