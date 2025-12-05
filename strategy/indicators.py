import pandas as pd
import numpy as np

def calculate_rsi(prices: pd.Series, period: int = 14) -> pd.Series:
    """Calculate RSI indicator"""
    delta = prices.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    
    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))
    return rsi

def calculate_rsa_ma(prices: pd.Series, rsi_period: int = 14, ma_period: int = 10) -> pd.Series:
    """Calculate RSI Moving Average"""
    rsi = calculate_rsi(prices, rsi_period)
    rsa_ma = rsi.rolling(window=ma_period).mean()
    return rsa_ma

def to_percentile_rank(series: pd.Series, window: int = 252) -> pd.Series:
    """Convert values to rolling percentile ranks"""
    return series.rolling(window).apply(
        lambda x: pd.Series(x).rank(pct=True).iloc[-1]
    )
