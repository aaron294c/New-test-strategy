# Lower Extension Distance Panel - Example Usage

## Complete Working Example

This example demonstrates a complete integration with mock data and all features enabled.

```typescript
import React, { useState, useEffect } from 'react';
import { LowerExtensionPanel } from './components/LowerExtensionPanel';
import { IndicatorData } from './utils/lowerExtensionCalculations';

// Mock data generator for testing
function generateMockData(): IndicatorData[] {
  const symbols = ['SPX', 'NDX', 'DJI', 'RUT'];
  const basePrice = 6900;

  return symbols.map((symbol, idx) => {
    const priceOffset = (idx - 1.5) * 50; // Vary prices around base
    const currentPrice = basePrice + priceOffset + Math.random() * 20;
    const lowerExt = basePrice;

    // Generate 30 days of historical prices
    const historical = Array.from({ length: 30 }, (_, i) => {
      const daysAgo = 30 - i;
      const date = new Date();
      date.setDate(date.getDate() - daysAgo);

      // Simulate price movement with breaches
      const volatility = 50 + Math.random() * 30;
      const trend = (30 - daysAgo) * 2; // Upward trend
      const price = basePrice - volatility + trend + Math.random() * 40;

      return {
        timestamp: date.toISOString(),
        price: Math.round(price * 100) / 100,
      };
    });

    return {
      symbol,
      price: Math.round(currentPrice * 100) / 100,
      lower_ext: lowerExt,
      last_update: new Date().toLocaleString('en-US', {
        month: 'short',
        day: 'numeric',
        hour: 'numeric',
        minute: '2-digit',
        hour12: true,
      }).toLowerCase(),
      historical_prices: historical,
    };
  });
}

// Mock candle data generator
function generateMockCandles(symbol: string, days: number = 60) {
  const candles = [];
  const basePrice = 6900;

  for (let i = days; i >= 0; i--) {
    const date = new Date();
    date.setDate(date.getDate() - i);

    const open = basePrice + Math.random() * 100 - 50;
    const close = open + Math.random() * 40 - 20;
    const high = Math.max(open, close) + Math.random() * 20;
    const low = Math.min(open, close) - Math.random() * 20;

    candles.push({
      time: date.toISOString().split('T')[0],
      open: Math.round(open * 100) / 100,
      high: Math.round(high * 100) / 100,
      low: Math.round(low * 100) / 100,
      close: Math.round(close * 100) / 100,
    });
  }

  return candles;
}

function App() {
  const [indicatorData, setIndicatorData] = useState<IndicatorData[]>([]);
  const [candleData, setCandleData] = useState<Record<string, any[]>>({});

  useEffect(() => {
    // Initialize with mock data
    const mockData = generateMockData();
    setIndicatorData(mockData);

    const mockCandles: Record<string, any[]> = {};
    mockData.forEach((data) => {
      mockCandles[data.symbol] = generateMockCandles(data.symbol);
    });
    setCandleData(mockCandles);

    // Simulate live price updates every 5 seconds
    const interval = setInterval(() => {
      setIndicatorData((prev) =>
        prev.map((item) => ({
          ...item,
          price: item.price + (Math.random() - 0.5) * 10,
          last_update: new Date().toLocaleString('en-US', {
            month: 'short',
            day: 'numeric',
            hour: 'numeric',
            minute: '2-digit',
            hour12: true,
          }).toLowerCase(),
        }))
      );
    }, 5000);

    return () => clearInterval(interval);
  }, []);

  // Optional: Implement historical price fetcher
  const handleFetchHistoricalPrices = async (symbol: string, days: number) => {
    // In production, this would call your API
    console.log(`Fetching ${days} days of historical prices for ${symbol}`);

    // Mock implementation
    return new Promise<Array<{ timestamp: string; price: number }>>((resolve) => {
      setTimeout(() => {
        const historical = Array.from({ length: days }, (_, i) => {
          const date = new Date();
          date.setDate(date.getDate() - (days - i));
          return {
            timestamp: date.toISOString(),
            price: 6900 + Math.random() * 100 - 50,
          };
        });
        resolve(historical);
      }, 500);
    });
  };

  return (
    <div>
      <LowerExtensionPanel
        indicatorData={indicatorData}
        candleData={candleData}
        onFetchHistoricalPrices={handleFetchHistoricalPrices}
      />
    </div>
  );
}

export default App;
```

## Integration with Real Indicator Parser

```typescript
import React, { useState, useEffect } from 'react';
import { LowerExtensionPanel } from './components/LowerExtensionPanel';
import { IndicatorData } from './utils/lowerExtensionCalculations';

// Parse your MBAD indicator output
async function parseIndicatorOutput(): Promise<IndicatorData[]> {
  try {
    // Fetch from your indicator API
    const response = await fetch('/api/indicator/mbad');
    const data = await response.json();

    // Map to required format
    return data.symbols.map((symbol: any) => ({
      symbol: symbol.ticker,
      price: symbol.currentPrice || symbol.close,
      lower_ext: symbol.levels.ext_lower, // Blue lower extension line
      timestamp: symbol.timestamp,
      last_update: new Date(symbol.timestamp).toLocaleString('en-US', {
        month: 'short',
        day: 'numeric',
        hour: 'numeric',
        minute: '2-digit',
        hour12: true,
      }).toLowerCase(),
      historical_prices: symbol.history?.map((h: any) => ({
        timestamp: h.time,
        price: h.close || h.price,
      })),
    }));
  } catch (error) {
    console.error('Failed to parse indicator output:', error);
    return [];
  }
}

// Fetch candle data
async function fetchCandleData(symbols: string[]): Promise<Record<string, any[]>> {
  const candleData: Record<string, any[]> = {};

  for (const symbol of symbols) {
    try {
      const response = await fetch(`/api/candles/${symbol}?days=60`);
      const candles = await response.json();
      candleData[symbol] = candles;
    } catch (error) {
      console.error(`Failed to fetch candles for ${symbol}:`, error);
      candleData[symbol] = [];
    }
  }

  return candleData;
}

function RealIndicatorIntegration() {
  const [indicatorData, setIndicatorData] = useState<IndicatorData[]>([]);
  const [candleData, setCandleData] = useState<Record<string, any[]>>({});
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function loadData() {
      setLoading(true);

      const indicators = await parseIndicatorOutput();
      setIndicatorData(indicators);

      const symbols = indicators.map((i) => i.symbol);
      const candles = await fetchCandleData(symbols);
      setCandleData(candles);

      setLoading(false);
    }

    loadData();

    // Auto-refresh every minute
    const interval = setInterval(loadData, 60000);

    return () => clearInterval(interval);
  }, []);

  if (loading) {
    return <div>Loading indicator data...</div>;
  }

  return (
    <LowerExtensionPanel
      indicatorData={indicatorData}
      candleData={candleData}
      onFetchHistoricalPrices={async (symbol, days) => {
        const response = await fetch(`/api/history/${symbol}?days=${days}`);
        return response.json();
      }}
    />
  );
}

export default RealIndicatorIntegration;
```

## Integration with WebSocket Live Updates

```typescript
import React, { useState, useEffect, useRef } from 'react';
import { LowerExtensionPanel } from './components/LowerExtensionPanel';
import { IndicatorData } from './utils/lowerExtensionCalculations';

function LivePriceIntegration() {
  const [indicatorData, setIndicatorData] = useState<IndicatorData[]>([]);
  const [candleData, setCandleData] = useState<Record<string, any[]>>({});
  const wsRef = useRef<WebSocket | null>(null);

  useEffect(() => {
    // Initial data load
    async function loadInitialData() {
      const response = await fetch('/api/indicator/mbad');
      const data = await response.json();

      const indicators = data.symbols.map((s: any) => ({
        symbol: s.ticker,
        price: s.currentPrice,
        lower_ext: s.levels.ext_lower,
        last_update: new Date().toLocaleString(),
        historical_prices: s.history,
      }));

      setIndicatorData(indicators);

      // Load candles for each symbol
      const candles: Record<string, any[]> = {};
      for (const indicator of indicators) {
        const res = await fetch(`/api/candles/${indicator.symbol}`);
        candles[indicator.symbol] = await res.json();
      }
      setCandleData(candles);
    }

    loadInitialData();

    // Setup WebSocket for live price updates
    const ws = new WebSocket('wss://your-api.com/prices');

    ws.onopen = () => {
      console.log('WebSocket connected');
    };

    ws.onmessage = (event) => {
      const update = JSON.parse(event.data);

      // Update price in real-time
      setIndicatorData((prev) =>
        prev.map((item) =>
          item.symbol === update.symbol
            ? {
                ...item,
                price: update.price,
                last_update: new Date().toLocaleString('en-US', {
                  month: 'short',
                  day: 'numeric',
                  hour: 'numeric',
                  minute: '2-digit',
                  hour12: true,
                }).toLowerCase(),
              }
            : item
        )
      );

      // Update candle data
      if (update.candle) {
        setCandleData((prev) => ({
          ...prev,
          [update.symbol]: [...(prev[update.symbol] || []), update.candle],
        }));
      }
    };

    ws.onerror = (error) => {
      console.error('WebSocket error:', error);
    };

    ws.onclose = () => {
      console.log('WebSocket disconnected');
      // Attempt reconnection after 5 seconds
      setTimeout(() => {
        loadInitialData();
      }, 5000);
    };

    wsRef.current = ws;

    return () => {
      if (wsRef.current) {
        wsRef.current.close();
      }
    };
  }, []);

  return (
    <LowerExtensionPanel
      indicatorData={indicatorData}
      candleData={candleData}
    />
  );
}

export default LivePriceIntegration;
```

## Custom Composite Risk Scoring

Use exported JSON for downstream composite scoring:

```typescript
import React, { useState } from 'react';
import { LowerExtensionPanel } from './components/LowerExtensionPanel';
import { LowerExtMetrics } from './utils/lowerExtensionCalculations';

interface CompositeScore {
  symbol: string;
  risk_score: number;
  opportunity_score: number;
  recommendation: 'buy' | 'sell' | 'hold';
}

function CompositeRiskScoring() {
  const [indicatorData, setIndicatorData] = useState([]);
  const [candleData, setCandleData] = useState({});
  const [compositeScores, setCompositeScores] = useState<CompositeScore[]>([]);

  // Calculate composite risk score from lower ext metrics
  function calculateCompositeScore(metrics: LowerExtMetrics): CompositeScore {
    // Example composite scoring logic
    let risk_score = 0;
    let opportunity_score = 0;

    // Factor 1: Distance to lower_ext (higher proximity = higher opportunity)
    if (metrics.is_below_lower_ext) {
      opportunity_score += 40; // Strong buy signal
      risk_score += 20; // But some risk if deeply breached
    } else if (metrics.abs_pct_dist_lower_ext < 2) {
      opportunity_score += 30; // Close to lower_ext
    }

    // Factor 2: Proximity score (0-1)
    opportunity_score += metrics.proximity_score_30d * 30;

    // Factor 3: Recent breach (indicates current weakness)
    if (metrics.recent_breached) {
      opportunity_score += 20; // Good entry opportunity
      risk_score += 10; // But watch for continued downside
    }

    // Factor 4: Breach frequency (high frequency = higher risk)
    if (metrics.breach_rate_30d > 0.3) {
      risk_score += 30; // Frequently breaches = unstable
    } else if (metrics.breach_rate_30d < 0.1) {
      risk_score -= 10; // Rarely breaches = stable
    }

    // Factor 5: Min distance (deepest breach)
    if (metrics.min_pct_dist_30d < -5) {
      risk_score += 20; // Had very deep breach recently
    }

    // Normalize scores to 0-100
    risk_score = Math.max(0, Math.min(100, risk_score));
    opportunity_score = Math.max(0, Math.min(100, opportunity_score));

    // Determine recommendation
    let recommendation: 'buy' | 'sell' | 'hold' = 'hold';
    if (opportunity_score > 60 && risk_score < 40) {
      recommendation = 'buy';
    } else if (risk_score > 60) {
      recommendation = 'sell';
    }

    return {
      symbol: metrics.symbol,
      risk_score,
      opportunity_score,
      recommendation,
    };
  }

  // Handle export and calculate composite scores
  const handleCalculateComposite = (metrics: LowerExtMetrics) => {
    const compositeScore = calculateCompositeScore(metrics);
    setCompositeScores((prev) => {
      const existing = prev.filter((s) => s.symbol !== compositeScore.symbol);
      return [...existing, compositeScore];
    });
  };

  return (
    <div>
      <LowerExtensionPanel
        indicatorData={indicatorData}
        candleData={candleData}
      />

      {/* Composite Scores Dashboard */}
      <div style={{ marginTop: '40px', padding: '20px' }}>
        <h2>Composite Risk Scores</h2>
        <table style={{ width: '100%', borderCollapse: 'collapse' }}>
          <thead>
            <tr>
              <th>Symbol</th>
              <th>Risk Score</th>
              <th>Opportunity Score</th>
              <th>Recommendation</th>
            </tr>
          </thead>
          <tbody>
            {compositeScores.map((score) => (
              <tr key={score.symbol}>
                <td>{score.symbol}</td>
                <td>{score.risk_score.toFixed(0)}/100</td>
                <td>{score.opportunity_score.toFixed(0)}/100</td>
                <td style={{
                  color: score.recommendation === 'buy' ? 'green' :
                         score.recommendation === 'sell' ? 'red' : 'gray'
                }}>
                  {score.recommendation.toUpperCase()}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

export default CompositeRiskScoring;
```

## Mean Reversion Strategy Example

```typescript
/**
 * Mean Reversion Trading Strategy using Lower Extension Metrics
 */

interface TradeSignal {
  symbol: string;
  signal: 'entry' | 'exit' | 'none';
  confidence: number;
  reason: string;
}

function meanReversionStrategy(metrics: LowerExtMetrics): TradeSignal {
  // Entry conditions (price near/below lower_ext)
  if (
    metrics.is_below_lower_ext &&
    metrics.abs_pct_dist_lower_ext < 1.5 &&
    !metrics.recent_breached
  ) {
    return {
      symbol: metrics.symbol,
      signal: 'entry',
      confidence: metrics.proximity_score_30d,
      reason: `Price breached lower_ext by ${metrics.pct_dist_lower_ext.toFixed(2)}%. No recent breaches = stable support.`,
    };
  }

  // Strong entry (deeply breached but recovering)
  if (
    metrics.min_pct_dist_30d < -3 &&
    metrics.pct_dist_lower_ext > metrics.min_pct_dist_30d &&
    metrics.proximity_score_30d > 0.7
  ) {
    return {
      symbol: metrics.symbol,
      signal: 'entry',
      confidence: 0.9,
      reason: `Recovering from deep breach (${metrics.min_pct_dist_30d.toFixed(2)}%). High proximity score = strong mean reversion opportunity.`,
    };
  }

  // Exit conditions (price far above lower_ext)
  if (
    !metrics.is_below_lower_ext &&
    metrics.abs_pct_dist_lower_ext > 3.0
  ) {
    return {
      symbol: metrics.symbol,
      signal: 'exit',
      confidence: 0.8,
      reason: `Price ${metrics.pct_dist_lower_ext.toFixed(2)}% above lower_ext. Take profits on mean reversion trade.`,
    };
  }

  return {
    symbol: metrics.symbol,
    signal: 'none',
    confidence: 0,
    reason: 'No clear signal.',
  };
}

// Use in strategy dashboard
function StrategyDashboard() {
  const [signals, setSignals] = useState<TradeSignal[]>([]);

  const handleMetricsUpdate = (metricsArray: LowerExtMetrics[]) => {
    const newSignals = metricsArray.map(meanReversionStrategy);
    setSignals(newSignals);
  };

  return (
    <div>
      {/* Render signals */}
      {signals.filter(s => s.signal !== 'none').map(signal => (
        <div key={signal.symbol} style={{
          padding: '16px',
          margin: '8px',
          background: signal.signal === 'entry' ? '#22c55e' : '#ef4444',
          color: 'white',
          borderRadius: '8px',
        }}>
          <h3>{signal.symbol} - {signal.signal.toUpperCase()}</h3>
          <p>Confidence: {(signal.confidence * 100).toFixed(0)}%</p>
          <p>{signal.reason}</p>
        </div>
      ))}
    </div>
  );
}
```

## Running Tests

```bash
# Install dependencies
npm install

# Run tests
npm test -- lowerExtensionCalculations.test.ts

# Run tests with coverage
npm test -- --coverage lowerExtensionCalculations.test.ts

# Watch mode
npm test -- --watch lowerExtensionCalculations.test.ts
```

## Deployment Checklist

- [ ] Indicator parser provides all required fields
- [ ] Historical prices available for 30+ days
- [ ] Candle data endpoint configured
- [ ] WebSocket setup for live updates (optional)
- [ ] Settings configured for your strategy
- [ ] Export JSON tested and validated
- [ ] Performance tested with 10+ symbols
- [ ] Error handling for missing/stale data
- [ ] Visual customization matches app theme
