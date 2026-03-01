

import yfinance as yf
import pandas as pd

def load_data(ticker, start="2018-01-01"):
    data = yf.download(ticker, start=start)
    data = data[['Close']]
    data.dropna(inplace=True)
    return data
    