import os
import pandas as pd
import ta.volume
import yfinance as yf
from matplotlib import pyplot as plt
from typing import Annotated, List, Tuple
from pandas import DateOffset
from datetime import datetime, timedelta
import matplotlib.pyplot as plt
import requests
import ta
import akshare as ak
api_key="LS5RN88HLIZU7NOH"


def plot_stock_price_chart(
    ticker_symbol: Annotated[
        str, "Ticker symbol of the stock (e.g., 'AAPL' for Apple)"
    ],
   
    save_path: Annotated[str, "File path where the plot should be saved"],
) -> str:
    """
    Plot a stock price chart using mplfinance for the specified stock and time period,
    and save the plot to a file.
    """
    # Fetch historical data
    stock_data = ak.stock_us_daily(symbol=ticker_symbol, adjust="").tail(10)
    stock_data['date'].astype(str)
    stock_data['date'].dt.strftime('%Y-%m-%d')
    print(stock_data)

    if stock_data.empty:
        print("No data found for the given date range.")
        return
    

    plt.figure(figsize=(10, 6))
    plt.plot(stock_data['date'],stock_data['close'],label=ticker_symbol+' Stock Price')
    plt.title('sStock Price Movement')
    plt.xlabel('Date')
    plt.ylabel('Price (USD)')
    plt.legend()
    plt.grid(True)
    plt.savefig(save_path)
    return f"{ticker_symbol} chart saved to <img {save_path}>"



    

def get_price(ticker_symbol: Annotated[
        str, "Ticker symbol of the stock (e.g., 'AAPL' for Apple)"
    ]) -> str:
   
    df = ak.stock_us_daily(symbol=ticker_symbol, adjust="")
    print(df['date'].dtype)
    # df['date'].astype(str)
    df['date']=df['date'].dt.strftime('%Y-%m-%d')
    # df['date']=df['date'].dt.date
    #print(df['date'].dtypes)


    df.set_index('date', inplace=True)

    # Calculating MACD
    df['MACD'] = ta.trend.macd(df['close'])
    df['MACD_Signal'] = ta.trend.macd_signal(df['close'])
    df['MACD_Diff'] = ta.trend.macd_diff(df['close'])

    # Calculating RSI
    df['RSI'] = ta.momentum.rsi(df['close'])

    # Calculating EMA
    df['EMA'] = ta.trend.ema_indicator(df['close'])
    df['ADI']=ta.volume.AccDistIndexIndicator(high=df['high'], low=df['low'], close=df['close'], volume=df['volume']).acc_dist_index()
    df['FI']=ta.volume.ForceIndexIndicator(df['close'], df['volume']).force_index() 

    # Calculating Bollinger Bands
    indicator_bb = ta.volatility.BollingerBands(close=df['close'], window=20, window_dev=2)
    df['BB_High'] = indicator_bb.bollinger_hband()
    df['BB_Low'] = indicator_bb.bollinger_lband()
    df['BB_Middle'] = indicator_bb.bollinger_mavg()

    return df.tail(10).to_json()



def test_price(ticker,start_date,end_date):
    df=ak.stock_us_daily(symbol=ticker, adjust="")
    df.set_index('date', inplace=True)

    return df.loc[start_date:end_date]

today=datetime.today().strftime('%Y-%m-%d')
one_week_later = (datetime.today() + timedelta(days=7)).strftime('%Y-%m-%d')

print(one_week_later)
print(type(one_week_later))
a=test_price("MSFT","2021-01-01","2021-01-10")
print(type(a))