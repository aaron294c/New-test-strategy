"""
Generate sample stock data to test the RSI indicator when Yahoo Finance is blocked.
"""
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

def generate_sample_stock_data(ticker: str = "AAPL", days: int = 365) -> pd.DataFrame:
    """Generate realistic sample stock data."""
    
    # Start date
    end_date = datetime.now()
    start_date = end_date - timedelta(days=days)
    
    # Generate date range
    dates = pd.date_range(start=start_date, end=end_date, freq='D')
    dates = dates[dates.dayofweek < 5]  # Only weekdays
    
    # Generate realistic price movement
    np.random.seed(hash(ticker) % 2**32)  # Consistent data for same ticker
    
    # Starting price based on ticker
    start_prices = {
        'AAPL': 150,
        'MSFT': 300,
        'GOOGL': 120,
        'AMZN': 140,
        'META': 300,
        'NVDA': 400,
        'QQQ': 350,
        'SPY': 420
    }
    
    base_price = start_prices.get(ticker, 100)
    
    # Generate returns with trends and volatility
    returns = np.random.randn(len(dates)) * 0.02  # 2% daily volatility
    
    # Add trend
    trend = np.linspace(0, 0.3, len(dates))  # 30% upward trend over period
    returns += trend / len(dates)
    
    # Add some cyclical patterns (RSI oversold/overbought zones)
    cycle = np.sin(np.linspace(0, 4 * np.pi, len(dates))) * 0.01
    returns += cycle
    
    # Calculate prices
    price_multipliers = np.exp(np.cumsum(returns))
    close_prices = base_price * price_multipliers
    
    # Generate OHLC data
    data = pd.DataFrame({
        'Open': close_prices * (1 + np.random.randn(len(dates)) * 0.005),
        'High': close_prices * (1 + np.abs(np.random.randn(len(dates))) * 0.01),
        'Low': close_prices * (1 - np.abs(np.random.randn(len(dates))) * 0.01),
        'Close': close_prices,
        'Volume': np.random.randint(50000000, 150000000, len(dates))
    }, index=dates)
    
    # Ensure High is highest and Low is lowest
    data['High'] = data[['Open', 'High', 'Close']].max(axis=1)
    data['Low'] = data[['Open', 'Low', 'Close']].min(axis=1)
    
    return data


if __name__ == '__main__':
    # Test the generator
    for ticker in ['AAPL', 'MSFT', 'GOOGL']:
        df = generate_sample_stock_data(ticker, days=252)
        print(f"\n{ticker}: {len(df)} days")
        print(df.head())
        print(f"Price range: ${df['Close'].min():.2f} - ${df['Close'].max():.2f}")
