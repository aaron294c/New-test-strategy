import numpy as np
import pandas as pd
from scipy import stats

def calculate_hurst_exponent(prices: pd.Series, lags: list = None) -> float:
    """Calculate Hurst exponent to determine price series memory"""
    if lags is None:
        lags = [2, 5, 10, 20, 50]
    
    log_returns = np.log(prices).diff().dropna()
    tau = [np.sqrt(np.std(np.subtract(log_returns[lag:], log_returns[:-lag]))) for lag in lags]
    reg = np.polyfit(np.log(lags), np.log(tau), 1)
    return reg[0]

def autocorrelation_score(returns: pd.Series, window: int = 20) -> pd.Series:
    """Calculate rolling autocorrelation of returns"""
    return returns.rolling(window).apply(lambda x: x.autocorr(1))

def variance_ratio(prices: pd.Series, short_period: int = 1, long_period: int = 5) -> float:
    """Implement Lo-MacKinlay variance ratio test"""
    returns = np.log(prices).diff().dropna()
    short_var = returns.rolling(short_period).var()
    long_var = returns.rolling(long_period).var() / long_period
    return (short_var / long_var).mean()

def composite_regime_score(prices: pd.Series, window: int = 20) -> pd.Series:
    """Combine multiple regime indicators into a single score"""
    returns = prices.pct_change()
    
    # Calculate individual metrics
    hurst = pd.Series(index=prices.index, dtype=float)
    for i in range(window, len(prices)):
        hurst.iloc[i] = calculate_hurst_exponent(prices.iloc[i-window:i])
    
    autocorr = autocorrelation_score(returns, window)
    var_rat = pd.Series([variance_ratio(prices.iloc[max(0,i-window):i]) 
                        for i in range(len(prices))], index=prices.index)
    
    # Normalize and combine
    hurst_norm = (hurst - 0.5) * 2  # Scale to [-1, 1]
    autocorr_norm = autocorr  # Already in [-1, 1]
    var_rat_norm = (var_rat - 1)  # Center around 0
    
    composite = (hurst_norm + autocorr_norm + var_rat_norm) / 3
    return composite.fillna(0)
