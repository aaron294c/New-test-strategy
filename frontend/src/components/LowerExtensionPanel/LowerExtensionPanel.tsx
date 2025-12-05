import React, { useState, useEffect, useCallback } from 'react';
import {
  calculateLowerExtMetrics,
  exportToJSON,
  exportMultipleToJSON,
  CalculationSettings,
  LowerExtMetrics,
  IndicatorData,
} from '../../utils/lowerExtensionCalculations';
import LowerExtensionChart from './LowerExtensionChart';
import SymbolCard from './SymbolCard';
import SettingsPanel from './SettingsPanel';

interface CandleData {
  time: string | number;
  open: number;
  high: number;
  low: number;
  close: number;
}

interface LowerExtensionPanelProps {
  // Data from indicator parser
  indicatorData: IndicatorData[];
  // Candle data for chart visualization
  candleData: Record<string, CandleData[]>;
  // Optional callback to fetch historical prices if not provided
  onFetchHistoricalPrices?: (symbol: string, days: number) => Promise<Array<{ timestamp: string; price: number }>>;
}

const DEFAULT_SETTINGS: CalculationSettings = {
  lookback_days: 30,
  recent_N: 5,
  proximity_threshold: 5.0,
  price_source: 'close',
};

const LowerExtensionPanel: React.FC<LowerExtensionPanelProps> = ({
  indicatorData,
  candleData,
  onFetchHistoricalPrices,
}) => {
  const [settings, setSettings] = useState<CalculationSettings>(DEFAULT_SETTINGS);
  const [autoRefresh, setAutoRefresh] = useState(false);
  const [refreshInterval, setRefreshInterval] = useState(30);
  const [selectedSymbol, setSelectedSymbol] = useState<string | null>(null);
  const [metricsMap, setMetricsMap] = useState<Record<string, LowerExtMetrics>>({});
  const [showAnnotation, setShowAnnotation] = useState(true);
  const [showShading, setShowShading] = useState(true);

  // Calculate metrics for all symbols
  const calculateAllMetrics = useCallback(async () => {
    const newMetrics: Record<string, LowerExtMetrics> = {};

    for (const data of indicatorData) {
      // Check if data already has pre-calculated metrics from backend
      if (data.pct_dist_lower_ext !== undefined && data.is_below_lower_ext !== undefined) {
        // Use pre-calculated metrics from backend API
        newMetrics[data.symbol] = {
          symbol: data.symbol,
          price: data.price,
          lower_ext: data.lower_ext,
          pct_dist_lower_ext: data.pct_dist_lower_ext,
          is_below_lower_ext: data.is_below_lower_ext,
          abs_pct_dist_lower_ext: data.abs_pct_dist_lower_ext || Math.abs(data.pct_dist_lower_ext),
          min_pct_dist_30d: data.min_pct_dist_30d || 0,
          median_abs_pct_dist_30d: data.median_abs_pct_dist_30d || 0,
          breach_count_30d: data.breach_count_30d || 0,
          breach_rate_30d: data.breach_rate_30d || 0,
          recent_breached: data.recent_breached || false,
          proximity_score_30d: data.proximity_score_30d || 0,
          last_update: data.last_update || new Date().toISOString(),
          stale_data: false
        };
      } else {
        // Fallback: calculate metrics if not provided by backend
        // Fetch historical prices if needed and callback provided
        let historicalPrices = data.historical_prices;
        if ((!historicalPrices || historicalPrices.length === 0) && onFetchHistoricalPrices) {
          try {
            historicalPrices = await onFetchHistoricalPrices(data.symbol, settings.lookback_days);
          } catch (error) {
            console.error(`Failed to fetch historical prices for ${data.symbol}:`, error);
          }
        }

        const dataWithHistory: IndicatorData = {
          ...data,
          historical_prices: historicalPrices,
        };

        const metrics = calculateLowerExtMetrics(dataWithHistory, settings);
        if (metrics) {
          newMetrics[data.symbol] = metrics;
        }
      }
    }

    setMetricsMap(newMetrics);

    // Auto-select first symbol if none selected
    if (!selectedSymbol && indicatorData.length > 0) {
      setSelectedSymbol(indicatorData[0].symbol);
    }
  }, [indicatorData, settings, onFetchHistoricalPrices, selectedSymbol]);

  // Initial calculation
  useEffect(() => {
    calculateAllMetrics();
  }, [calculateAllMetrics]);

  // Auto-refresh
  useEffect(() => {
    if (!autoRefresh) return;

    const interval = setInterval(() => {
      calculateAllMetrics();
    }, refreshInterval * 1000);

    return () => clearInterval(interval);
  }, [autoRefresh, refreshInterval, calculateAllMetrics]);

  // Handle manual refresh
  const handleManualRefresh = () => {
    calculateAllMetrics();
  };

  // Handle JSON export for single symbol
  const handleExportJSON = (symbol: string) => {
    const metrics = metricsMap[symbol];
    if (!metrics) return;

    const json = exportToJSON(metrics);

    // Create blob and download
    const blob = new Blob([json], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `lower_ext_${symbol}_${new Date().toISOString().split('T')[0]}.json`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

  // Handle JSON export for all symbols
  const handleExportAllJSON = () => {
    const allMetrics = Object.values(metricsMap);
    const json = exportMultipleToJSON(allMetrics);

    // Create blob and download
    const blob = new Blob([json], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `lower_ext_all_symbols_${new Date().toISOString().split('T')[0]}.json`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

  const currentMetrics = selectedSymbol ? metricsMap[selectedSymbol] : null;
  const currentCandles = selectedSymbol ? candleData[selectedSymbol] || [] : [];
  const currentHistoricalPrices = indicatorData.find(d => d.symbol === selectedSymbol)?.historical_prices;

  return (
    <div style={{ background: '#111827', minHeight: '100vh', padding: '24px', color: 'white' }}>
      {/* Header */}
      <div
        style={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          marginBottom: '24px',
        }}
      >
        <div>
          <h1 style={{ fontSize: '32px', fontWeight: '700', margin: '0 0 8px 0' }}>
            Lower Extension Distance Analysis
          </h1>
          <p style={{ fontSize: '14px', color: '#9ca3af', margin: 0 }}>
            Compute signed percent distance to blue lower extension line with 30-day lookback metrics
          </p>
        </div>
        <button
          onClick={handleExportAllJSON}
          style={{
            background: '#10b981',
            color: 'white',
            border: 'none',
            padding: '12px 24px',
            borderRadius: '8px',
            fontSize: '14px',
            fontWeight: '600',
            cursor: 'pointer',
            transition: 'background 0.2s',
          }}
          onMouseOver={(e) => (e.currentTarget.style.background = '#059669')}
          onMouseOut={(e) => (e.currentTarget.style.background = '#10b981')}
        >
          Export All Symbols JSON
        </button>
      </div>

      {/* Symbol Tabs */}
      <div style={{ display: 'flex', gap: '8px', marginBottom: '24px', flexWrap: 'wrap' }}>
        {indicatorData.map((data) => {
          const metrics = metricsMap[data.symbol];
          const isSelected = selectedSymbol === data.symbol;

          return (
            <button
              key={data.symbol}
              onClick={() => setSelectedSymbol(data.symbol)}
              style={{
                padding: '12px 20px',
                background: isSelected ? '#3b82f6' : '#1f2937',
                border: 'none',
                borderRadius: '8px',
                color: 'white',
                fontSize: '14px',
                fontWeight: '600',
                cursor: 'pointer',
                transition: 'all 0.2s',
                position: 'relative',
              }}
              onMouseOver={(e) => {
                if (!isSelected) e.currentTarget.style.background = '#374151';
              }}
              onMouseOut={(e) => {
                if (!isSelected) e.currentTarget.style.background = '#1f2937';
              }}
            >
              <div>{data.symbol}</div>
              {metrics && (
                <div
                  style={{
                    fontSize: '10px',
                    marginTop: '2px',
                    color: metrics.is_below_lower_ext ? '#22c55e' : '#9ca3af',
                  }}
                >
                  {metrics.pct_dist_lower_ext >= 0 ? '+' : ''}
                  {metrics.pct_dist_lower_ext.toFixed(2)}%
                </div>
              )}
            </button>
          );
        })}
      </div>

      {/* Main Content */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 350px', gap: '24px' }}>
        {/* Left Column: Chart and Symbol Card */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
          {/* Chart */}
          {currentMetrics && (
            <div
              style={{
                background: '#1f2937',
                borderRadius: '12px',
                padding: '20px',
                boxShadow: '0 4px 12px rgba(0,0,0,0.3)',
              }}
            >
              <div
                style={{
                  display: 'flex',
                  justifyContent: 'space-between',
                  alignItems: 'center',
                  marginBottom: '16px',
                }}
              >
                <h3 style={{ fontSize: '18px', fontWeight: '700', margin: 0 }}>Price Chart with Lower Extension</h3>
                <div style={{ display: 'flex', gap: '12px' }}>
                  <label style={{ display: 'flex', alignItems: 'center', gap: '6px', fontSize: '14px' }}>
                    <input
                      type="checkbox"
                      checked={showAnnotation}
                      onChange={(e) => setShowAnnotation(e.target.checked)}
                      style={{ cursor: 'pointer' }}
                    />
                    Show Annotation
                  </label>
                  <label style={{ display: 'flex', alignItems: 'center', gap: '6px', fontSize: '14px' }}>
                    <input
                      type="checkbox"
                      checked={showShading}
                      onChange={(e) => setShowShading(e.target.checked)}
                      style={{ cursor: 'pointer' }}
                    />
                    Show Shading
                  </label>
                </div>
              </div>
              <LowerExtensionChart
                metrics={currentMetrics}
                candleData={currentCandles}
                showAnnotation={showAnnotation}
                showShading={showShading}
              />
            </div>
          )}

          {/* Symbol Card */}
          {currentMetrics && (
            <SymbolCard
              metrics={currentMetrics}
              historicalPrices={currentHistoricalPrices}
              onExportJSON={() => handleExportJSON(currentMetrics.symbol)}
            />
          )}

          {/* No data message */}
          {!currentMetrics && (
            <div
              style={{
                background: '#1f2937',
                borderRadius: '12px',
                padding: '40px',
                textAlign: 'center',
                color: '#9ca3af',
              }}
            >
              <div style={{ fontSize: '48px', marginBottom: '16px' }}>📊</div>
              <div style={{ fontSize: '18px', fontWeight: '600' }}>No Data Available</div>
              <div style={{ fontSize: '14px', marginTop: '8px' }}>
                Select a symbol or check your indicator data feed
              </div>
            </div>
          )}
        </div>

        {/* Right Column: Settings */}
        <div>
          <SettingsPanel
            settings={settings}
            onSettingsChange={setSettings}
            autoRefresh={autoRefresh}
            onAutoRefreshChange={setAutoRefresh}
            refreshInterval={refreshInterval}
            onRefreshIntervalChange={setRefreshInterval}
            onManualRefresh={handleManualRefresh}
          />

          {/* Quick Stats Summary */}
          <div
            style={{
              background: '#1f2937',
              borderRadius: '12px',
              padding: '20px',
              marginTop: '24px',
              boxShadow: '0 4px 12px rgba(0,0,0,0.3)',
            }}
          >
            <h3 style={{ fontSize: '16px', fontWeight: '700', margin: '0 0 16px 0' }}>Quick Stats</h3>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '12px', fontSize: '14px' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                <span style={{ color: '#9ca3af' }}>Total Symbols:</span>
                <span style={{ fontWeight: '600' }}>{indicatorData.length}</span>
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                <span style={{ color: '#9ca3af' }}>Below Lower Ext:</span>
                <span style={{ fontWeight: '600', color: '#22c55e' }}>
                  {Object.values(metricsMap).filter((m) => m.is_below_lower_ext).length}
                </span>
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                <span style={{ color: '#9ca3af' }}>Recently Breached:</span>
                <span style={{ fontWeight: '600', color: '#f59e0b' }}>
                  {Object.values(metricsMap).filter((m) => m.recent_breached).length}
                </span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default LowerExtensionPanel;
