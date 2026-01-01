import React, { useState, useEffect } from 'react';
import { LowerExtensionPanel } from '../components/LowerExtensionPanel';
import { IndicatorData } from '../utils/lowerExtensionCalculations';

// Use environment variable for API base URL
const API_BASE_URL = import.meta.env.VITE_API_URL || '';

interface CandleData {
  time: string;
  open: number;
  high: number;
  low: number;
  close: number;
}

const LowerExtensionPage: React.FC = () => {
  const [indicatorData, setIndicatorData] = useState<IndicatorData[]>([]);
  const [candleData, setCandleData] = useState<Record<string, CandleData[]>>({});
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Default symbols to track (indices need ^ prefix for yfinance)
  const defaultSymbols = [
    '^GSPC', '^NDX', '^DJI', '^RUT',
    'AAPL', 'MSFT', 'GOOGL', 'AMZN', 'META',
    'NFLX', 'TSLA', 'BRK-B', 'NVDA'
  ];

  // Fetch data for all symbols
  useEffect(() => {
    async function fetchData() {
      setLoading(true);
      setError(null);

      try {
        const indicators: IndicatorData[] = [];
        const candles: Record<string, CandleData[]> = {};

        // Fetch data for each symbol in parallel
        await Promise.all(
          defaultSymbols.map(async (symbol) => {
            try {
              // Fetch indicator metrics
              const metricsResponse = await fetch(
                `${API_BASE_URL}/api/lower-extension/metrics/${symbol}?length=30&lookback_days=30`
              );

              if (!metricsResponse.ok) {
                throw new Error(`Failed to fetch metrics for ${symbol}`);
              }

              const metricsData = await metricsResponse.json();

              // Map API response to IndicatorData format with all pre-calculated metrics
              indicators.push({
                symbol: metricsData.symbol,
                price: metricsData.price,
                lower_ext: metricsData.lower_ext,
                timestamp: metricsData.last_update,
                last_update: metricsData.last_update,
                historical_prices: metricsData.historical_prices,
                // Include all pre-calculated metrics from backend
                pct_dist_lower_ext: metricsData.pct_dist_lower_ext,
                is_below_lower_ext: metricsData.is_below_lower_ext,
                abs_pct_dist_lower_ext: metricsData.abs_pct_dist_lower_ext,
                min_pct_dist_30d: metricsData.min_pct_dist_30d,
                median_abs_pct_dist_30d: metricsData.median_abs_pct_dist_30d,
                breach_count_30d: metricsData.breach_count_30d,
                breach_rate_30d: metricsData.breach_rate_30d,
                recent_breached: metricsData.recent_breached,
                proximity_score_30d: metricsData.proximity_score_30d,
                all_levels: metricsData.all_levels,
              });

              // Fetch candle data
              const candlesResponse = await fetch(
                `${API_BASE_URL}/api/lower-extension/candles/${symbol}?days=60`
              );

              if (!candlesResponse.ok) {
                throw new Error(`Failed to fetch candles for ${symbol}`);
              }

              const candlesData = await candlesResponse.json();
              candles[metricsData.symbol] = candlesData.candles;
            } catch (err) {
              console.error(`Error fetching data for ${symbol}:`, err);
            }
          })
        );

        setIndicatorData(indicators);
        setCandleData(candles);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'An error occurred');
      } finally {
        setLoading(false);
      }
    }

    fetchData();
  }, []);

  // Optional: Implement historical price fetcher
  const handleFetchHistoricalPrices = async (symbol: string, days: number) => {
    try {
      const response = await fetch(
        `${API_BASE_URL}/api/lower-extension/metrics/${symbol}?lookback_days=${days}`
      );

      if (!response.ok) {
        throw new Error(`Failed to fetch historical prices for ${symbol}`);
      }

      const data = await response.json();
      return data.historical_prices;
    } catch (err) {
      console.error('Error fetching historical prices:', err);
      return [];
    }
  };

  if (loading) {
    return (
      <div
        style={{
          display: 'flex',
          justifyContent: 'center',
          alignItems: 'center',
          height: '100vh',
          background: '#111827',
          color: 'white',
        }}
      >
        <div style={{ textAlign: 'center' }}>
          <div
            style={{
              fontSize: '48px',
              marginBottom: '16px',
              animation: 'spin 1s linear infinite',
            }}
          >
            ⟳
          </div>
          <div style={{ fontSize: '18px' }}>Loading lower extension data...</div>
        </div>
        <style>{`
          @keyframes spin {
            from { transform: rotate(0deg); }
            to { transform: rotate(360deg); }
          }
        `}</style>
      </div>
    );
  }

  if (error) {
    return (
      <div
        style={{
          display: 'flex',
          justifyContent: 'center',
          alignItems: 'center',
          height: '100vh',
          background: '#111827',
          color: 'white',
        }}
      >
        <div
          style={{
            background: '#1f2937',
            padding: '40px',
            borderRadius: '12px',
            boxShadow: '0 4px 12px rgba(0,0,0,0.3)',
            maxWidth: '500px',
            textAlign: 'center',
          }}
        >
          <div style={{ fontSize: '48px', marginBottom: '16px' }}>⚠️</div>
          <div style={{ fontSize: '20px', fontWeight: '700', marginBottom: '12px' }}>
            Error Loading Data
          </div>
          <div style={{ fontSize: '14px', color: '#9ca3af', marginBottom: '24px' }}>{error}</div>
          <button
            onClick={() => window.location.reload()}
            style={{
              background: '#3b82f6',
              color: 'white',
              border: 'none',
              padding: '12px 24px',
              borderRadius: '8px',
              fontSize: '14px',
              fontWeight: '600',
              cursor: 'pointer',
            }}
          >
            Retry
          </button>
        </div>
      </div>
    );
  }

  return (
    <LowerExtensionPanel
      indicatorData={indicatorData}
      candleData={candleData}
      onFetchHistoricalPrices={handleFetchHistoricalPrices}
    />
  );
};

export default LowerExtensionPage;
