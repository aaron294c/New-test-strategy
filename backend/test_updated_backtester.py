#!/usr/bin/env python3
"""Test the updated backtester with Mean Price and standardized returns."""

from enhanced_backtester import EnhancedPerformanceMatrixBacktester

# Create backtester
backtester = EnhancedPerformanceMatrixBacktester(
    tickers=['AAPL'],
    rsi_length=14,
    ma_length=14,
    lookback_period=500,
    max_horizon=21
)

# Fetch data
print('Fetching AAPL data...')
data = backtester.fetch_data('AAPL')

if not data.empty:
    print(f'Fetched {len(data)} data points')
    print(f'Date range: {data.index[0].strftime("%Y-%m-%d")} to {data.index[-1].strftime("%Y-%m-%d")}')

    # Calculate RSI-MA using the new method
    print('\nCalculating RSI-MA with Mean Price + Standardized Returns...')
    rsi_ma = backtester.calculate_rsi_ma_indicator(data)

    # Show last 10 values
    print('\nLast 10 RSI-MA values:')
    for i in range(-10, 0):
        date = data.index[i]
        print(f'  {date.strftime("%Y-%m-%d")}: {rsi_ma.iloc[i]:.2f}')

    # Final result
    print(f'\n{"="*70}')
    print(f'FINAL RESULT')
    print(f'{"="*70}')
    print(f'Date: {data.index[-1].strftime("%Y-%m-%d")}')
    print(f'Close Price: ${data["Close"].iloc[-1]:.2f}')
    print(f'RSI-MA: {rsi_ma.iloc[-1]:.2f}')
    print(f'\nYour TradingView RSI-MA: 48.48')
    print(f'Difference: {abs(rsi_ma.iloc[-1] - 48.48):.2f}')

    if abs(rsi_ma.iloc[-1] - 48.48) < 3:
        print('\n✓ CLOSE MATCH! Within 3 points of TradingView')
    elif abs(rsi_ma.iloc[-1] - 48.48) < 5:
        print('\n✓ Good match! Within 5 points of TradingView')
    else:
        print('\n⚠ Still some difference - may need further calibration')
else:
    print('Failed to fetch data')
