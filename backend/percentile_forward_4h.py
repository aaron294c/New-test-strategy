#!/usr/bin/env python3
"""
4-Hour Percentile Forward Mapping

This module provides 4-hour timeframe analysis using the same methodology
as the daily Percentile Forward Mapping, but with:
- 4-hour OHLC candles
- Horizons: 12h (3 bars), 24h (6 bars), 36h (9 bars), 48h (12 bars)
- Same model suite: Empirical, Markov, Linear, Polynomial, Quantile, Kernel

This keeps the daily implementation unchanged while providing parallel 4H functionality.
"""

import numpy as np
import pandas as pd
import yfinance as yf
from typing import Dict
from datetime import datetime, timedelta
from dataclasses import asdict

from ticker_utils import resolve_yahoo_symbol

# Import the existing mapper (we'll reuse it with different horizons)
from percentile_forward_mapping import (
    PercentileForwardMapper,
    PercentileBinStats,
    TransitionMatrix,
    RegressionForecast,
    KernelForecast,
    PercentileFirstForecast,
    ConfidenceAssessment,
    ModelBinMapping,
    ForwardReturnPrediction
)


def fetch_4h_data(ticker: str, lookback_days: int = 365) -> pd.DataFrame:
    """
    Fetch 4-hour OHLC data from yfinance.

    Args:
        ticker: Stock symbol
        lookback_days: Days of historical data to fetch

    Returns:
        DataFrame with 4H OHLC data
    """
    print(f"Fetching 4-hour data for {ticker}...")

    # yfinance intervals: 1m, 2m, 5m, 15m, 30m, 60m, 90m, 1h, 1d, 5d, 1wk, 1mo, 3mo
    # For 4-hour, we need to use 1h and resample to 4H
    end_date = datetime.now()
    start_date = end_date - timedelta(days=lookback_days)

    # Fetch 1-hour data first (yfinance doesn't have native 4h)
    ticker_obj = yf.Ticker(resolve_yahoo_symbol(ticker))
    data_1h = ticker_obj.history(start=start_date, end=end_date, interval='1h')

    if data_1h.empty:
        raise ValueError(f"No data retrieved for {ticker}")

    # Resample 1-hour to 4-hour
    data_4h = pd.DataFrame()
    data_4h['Open'] = data_1h['Open'].resample('4H').first()
    data_4h['High'] = data_1h['High'].resample('4H').max()
    data_4h['Low'] = data_1h['Low'].resample('4H').min()
    data_4h['Close'] = data_1h['Close'].resample('4H').last()
    data_4h['Volume'] = data_1h['Volume'].resample('4H').sum()

    # Drop any rows with NaN
    data_4h = data_4h.dropna()

    print(f"  ✓ Retrieved {len(data_4h)} 4-hour bars")

    return data_4h


def calculate_rsi_ma_4h(data: pd.DataFrame, rsi_length: int = 14, ma_length: int = 14) -> pd.Series:
    """
    Calculate RSI-MA on 4-hour data using exact same method as daily.

    Pipeline (same as daily):
    1. Calculate log returns from Close price
    2. Calculate change of returns (diff)
    3. Apply RSI (14-period) using Wilder's method
    4. Apply EMA (14-period) to RSI
    """
    close_price = data['Close']

    # Step 1: Calculate log returns
    log_returns = np.log(close_price / close_price.shift(1)).fillna(0)

    # Step 2: Calculate change of returns (second derivative)
    delta = log_returns.diff()

    # Step 3: Apply RSI to delta
    gains = delta.where(delta > 0, 0)
    losses = -delta.where(delta < 0, 0)

    # Wilder's smoothing (RMA)
    avg_gains = gains.ewm(alpha=1/rsi_length, adjust=False).mean()
    avg_losses = losses.ewm(alpha=1/rsi_length, adjust=False).mean()

    rs = avg_gains / avg_losses
    rsi = 100 - (100 / (1 + rs))
    rsi = rsi.fillna(50)

    # Step 4: Apply EMA to RSI
    rsi_ma = rsi.ewm(span=ma_length, adjust=False).mean()

    return rsi_ma


def calculate_percentile_ranks_4h(rsi_ma: pd.Series, lookback_window: int = 410) -> pd.Series:
    """
    Calculate rolling percentile ranks for RSI-MA on 4H data.

    Args:
        rsi_ma: RSI-MA time series
        lookback_window: Number of 4H bars to use for percentile calculation (default 410 = 252 trading days)

    Note:
        - Daily percentile uses 252 bars = 252 trading days ≈ 1 year
        - 4H percentile uses 410 bars = 252 trading days ≈ 1 year
        - NYSE hours: 6.5 hours/day (9:30 AM - 4:00 PM)
        - Calculation: 252 trading days × 1.625 candles/day (6.5h ÷ 4h) = 409.5 ≈ 410 bars

    Returns:
        Series of percentile ranks (0-100)
    """
    percentiles = pd.Series(index=rsi_ma.index, dtype=float)

    for i in range(len(rsi_ma)):
        if i < lookback_window:
            # Not enough data yet
            percentiles.iloc[i] = np.nan
        else:
            window_data = rsi_ma.iloc[i - lookback_window:i]
            current_value = rsi_ma.iloc[i]

            # Calculate percentile rank
            rank = (window_data < current_value).sum() / len(window_data) * 100
            percentiles.iloc[i] = rank

    return percentiles


def run_percentile_forward_analysis_4h(ticker: str, lookback_days: int = 365) -> Dict:
    """
    Run complete percentile-to-forward-return analysis on 4-HOUR data.

    This function mirrors run_percentile_forward_analysis() but uses:
    - 4-hour candles instead of daily
    - Horizons: 3, 6, 9, 12 bars (= 12h, 24h, 36h, 48h)

    Returns comprehensive analysis with all methods, identical structure to daily.
    """
    print(f"\n{'='*80}")
    print(f"4-HOUR PERCENTILE FORWARD MAPPING ANALYSIS: {ticker}")
    print(f"{'='*80}\n")

    # 1. Fetch 4H data
    data_4h = fetch_4h_data(ticker, lookback_days=lookback_days)

    # 2. Calculate RSI-MA on 4H bars
    print("Calculating RSI-MA on 4-hour data...")
    rsi_ma_4h = calculate_rsi_ma_4h(data_4h, rsi_length=14, ma_length=14)
    print(f"  ✓ RSI-MA calculated")

    # 3. Calculate percentile ranks
    print("Calculating percentile ranks...")
    percentiles_4h = calculate_percentile_ranks_4h(rsi_ma_4h, lookback_window=410)
    print(f"  ✓ Percentiles calculated")

    # 4. Initialize mapper with 4H horizons
    # Horizons: 3, 6, 9, 12 bars = 12h, 24h, 36h, 48h
    mapper = PercentileForwardMapper(horizons=[3, 6, 9, 12])

    print("Building historical dataset...")
    df = mapper.build_historical_dataset(
        rsi_ma=rsi_ma_4h,
        percentile_ranks=percentiles_4h,
        prices=data_4h['Close'],
        lookback_window=410  # 410 4H bars = 252 trading days (matches daily timeframe period)
    )

    print(f"  ✓ Dataset: {len(df)} observations")

    # 5. Empirical bin stats
    print("\n1. Calculating empirical bin statistics...")
    bin_stats = mapper.calculate_empirical_bin_stats(df)
    print(f"  ✓ Computed stats for {len(bin_stats)} bins")

    for bin_idx, stats in bin_stats.items():
        print(f"    {stats.bin_label}: n={stats.count}, "
              f"E[R_3bars/12h]={stats.mean_return_3d:+.2f}%, "
              f"E[R_6bars/24h]={stats.mean_return_7d:+.2f}%, "
              f"E[R_9bars/36h]={stats.mean_return_14d:+.2f}%, "
              f"E[R_12bars/48h]={stats.mean_return_21d:+.2f}%")

    # 6. Transition matrices
    print("\n2. Building transition matrices...")
    for h in [3, 6, 9, 12]:
        tm = mapper.build_transition_matrix(df, h)
        print(f"  ✓ {h} bars ({h*4}h) transition matrix (sample sizes: {tm.sample_sizes.sum():.0f} total)")

    # 7. Regression models
    print("\n3. Fitting regression models...")
    mapper.fit_regression_models(df)
    print(f"  ✓ Fitted {len(mapper.regression_models)} models")

    for key, model in mapper.regression_models.items():
        if 'linear' in key:
            print(f"    {key}: R²={model['r2']:.3f}, MAE={model['mae']:.2f}%")

    # 8. Current prediction
    current_pct = percentiles_4h.iloc[-1]
    current_rsi = rsi_ma_4h.iloc[-1]

    print(f"\n4. Current state prediction...")
    print(f"  Current RSI-MA Percentile (4H): {current_pct:.1f}%ile")
    print(f"  Current RSI-MA Value (4H): {current_rsi:.2f}")

    prediction = mapper.predict_forward_returns(df, current_pct, current_rsi)

    print(f"\n  Ensemble Forecast:")
    print(f"    12h (3 bars):  {prediction.ensemble_forecast_3d:+.2f}%")
    print(f"    24h (6 bars):  {prediction.ensemble_forecast_7d:+.2f}%")
    print(f"    36h (9 bars):  {prediction.ensemble_forecast_14d:+.2f}%")
    print(f"    48h (12 bars): {prediction.ensemble_forecast_21d:+.2f}%")

    print(f"\n  Method Breakdown (12h / 3 bars):")
    if prediction.empirical_bin_stats:
        print(f"    Empirical:  {prediction.empirical_bin_stats.mean_return_3d:+.2f}%")
    print(f"    Markov:     {prediction.markov_forecast_3d:+.2f}%")
    if prediction.linear_regression:
        print(f"    Linear:     {prediction.linear_regression.forecast_3d:+.2f}%")
    if prediction.polynomial_regression:
        print(f"    Polynomial: {prediction.polynomial_regression.forecast_3d:+.2f}%")
    print(f"    Kernel:     {prediction.kernel_forecast.forecast_3d:+.2f}%")

    # 9. Rolling window backtest
    print(f"\n5. Running rolling window backtest...")
    backtest_df = mapper.rolling_window_backtest(df, train_window=252, test_window=21, step_size=21)
    print(f"  ✓ Backtest: {len(backtest_df)} predictions")

    # 10. Evaluate accuracy
    print(f"\n6. Evaluating forecast accuracy...")
    metrics = mapper.evaluate_forecast_accuracy(backtest_df)

    for horizon, m in metrics.items():
        # Convert bars to hours for display
        bars = int(horizon.replace('d', ''))
        hours = bars * 4
        print(f"\n  {hours}h ({bars} bars) Horizon:")
        print(f"    MAE:              {m['mae']:.2f}%")
        print(f"    RMSE:             {m['rmse']:.2f}%")
        print(f"    Hit Rate:         {m['hit_rate']:.1f}%")
        print(f"    Sharpe Ratio:     {m['sharpe']:.2f}")
        print(f"    Information Ratio: {m['information_ratio']:.2f}")
        print(f"    Correlation:      {m['correlation']:.3f}")

    # Return comprehensive result (same structure as daily)
    return {
        'ticker': ticker,
        'timeframe': '4H',
        'horizon_labels': ['12h', '24h', '36h', '48h'],
        'horizon_bars': [3, 6, 9, 12],
        'current_percentile': current_pct,
        'current_rsi_ma': current_rsi,
        'prediction': asdict(prediction),
        'bin_stats': {k: asdict(v) for k, v in bin_stats.items()},
        'transition_matrices': {h: {
            'bins': tm.bins,
            'matrix': tm.matrix.tolist(),
            'sample_sizes': tm.sample_sizes.tolist(),
            'horizon_bars': h,
            'horizon_label': f'{h*4}h'
        } for h, tm in mapper.transition_matrices.items()},
        'backtest_results': backtest_df.to_dict('records'),
        'accuracy_metrics': metrics,
        'model_bin_mappings': {
            model_name: {
                'model_name': mapping.model_name,
                'bin_forecasts': mapping.bin_forecasts,
                'bin_uncertainties': mapping.bin_uncertainties,
                'model_metadata': mapping.model_metadata
            }
            for model_name, mapping in prediction.model_bin_mappings.items()
        }
    }


if __name__ == '__main__':
    result = run_percentile_forward_analysis_4h('AAPL', lookback_days=365)

    print(f"\n{'='*80}")
    print("4-HOUR ANALYSIS COMPLETE")
    print(f"{'='*80}")
    print(f"\nCurrent 4H RSI-MA Percentile: {result['current_percentile']:.1f}%")
    print(f"\nForecasts:")
    pred = result['prediction']
    print(f"  12h: {pred['ensemble_forecast_3d']:+.2f}%")
    print(f"  24h: {pred['ensemble_forecast_7d']:+.2f}%")
    print(f"  36h: {pred['ensemble_forecast_14d']:+.2f}%")
    print(f"  48h: {pred['ensemble_forecast_21d']:+.2f}%")
