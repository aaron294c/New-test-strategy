/**
 * Risk Distance Tab - Support Distance Analysis for Risk-Adjusted Expectancy
 * Deterministic calculations only - no subjective recommendations
 */

import React, { useState, useCallback, useEffect, useMemo } from 'react';
import { ParsedSymbolData } from '../GammaScanner/types';
import { GammaDataParser } from '../GammaScanner/dataParser';
import { RiskDistanceInput, RiskDistanceOutput } from './types';
import { calculateRiskDistances, exportToJSON, exportToCSV } from './calculator';
import { SymbolCard } from './SymbolCard';
import { calculateMaxPain } from './maxPainCalculator';
import { batchGetPrices } from '../../utils/priceService';
import { ProximitySettings, ProximityConfig } from './ProximitySettings';

const API_BASE_URL = import.meta.env.VITE_API_URL || '';

export const RiskDistanceTab: React.FC = () => {
  const [symbols, setSymbols] = useState<ParsedSymbolData[]>([]);
  const [selectedSymbols, setSelectedSymbols] = useState<Set<string>>(new Set());
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string>('');
  const [lastUpdate, setLastUpdate] = useState<string>('');
  const [marketRegime, setMarketRegime] = useState<string>('');
  const [realPrices, setRealPrices] = useState<Map<string, number>>(new Map());
  const [lowerExtData, setLowerExtData] = useState<Map<string, number>>(new Map());
  const [nwLowerBandData, setNwLowerBandData] = useState<Map<string, number>>(new Map());

  // Proximity settings state
  const [proximityConfig, setProximityConfig] = useState<ProximityConfig>({
    lowerExtThresholdPct: 20,
    nwBandThresholdPct: 20,
    useAbsoluteDistance: true,
  });
  const [settingsExpanded, setSettingsExpanded] = useState(false);

  // Fetch data from API
  const fetchData = useCallback(async () => {
    setIsLoading(true);
    setError('');

    try {
      const fetchJson = async (url: string) => {
        const res = await fetch(url);
        if (!res.ok) {
          throw new Error(`HTTP ${res.status}: ${res.statusText}`);
        }
        return res.json();
      };

      let data;
      try {
        data = await fetchJson(`${API_BASE_URL}/api/gamma-data?t=${Date.now()}`);
      } catch (primaryErr) {
        console.warn('Primary gamma-data fetch failed, falling back to example:', primaryErr);
        data = await fetchJson(`${API_BASE_URL}/api/gamma-data/example`);
        setError('Live gamma data unavailable; showing example data.');
      }

      const parser = new GammaDataParser();
      const parsedSymbols: ParsedSymbolData[] = [];

      data.level_data.forEach((line: string, index: number) => {
        const parsed = parser.parseLevelData(line, index + 1);
        if (parsed) {
          parsedSymbols.push(parsed);
        }
      });

      setSymbols(parsedSymbols);
      setLastUpdate(data.last_update || new Date().toLocaleString());
      setMarketRegime(data.market_regime || '');
      setError('');

      // Fetch real prices for all symbols
      const priceRequests = parsedSymbols.map(s => ({
        symbol: s.symbol,
        estimatedPrice: s.currentPrice,
      }));

      const prices = await batchGetPrices(priceRequests);
      const priceMap = new Map<string, number>();

      prices.forEach((priceData, symbol) => {
        priceMap.set(symbol, priceData.price);
      });

      setRealPrices(priceMap);

      // Fetch lower extension data for all symbols
      const lowerExtMap = new Map<string, number>();
      await Promise.all(
        parsedSymbols.map(async (s) => {
          try {
            const response = await fetch(`${API_BASE_URL}/api/lower-extension/metrics/${s.symbol}?length=30&lookback_days=30&t=${Date.now()}`);
            if (response.ok) {
              const data = await response.json();
              if (data.lower_ext) {
                lowerExtMap.set(s.symbol, data.lower_ext);
              }
            }
          } catch (err) {
            console.warn(`Failed to fetch lower extension for ${s.symbol}:`, err);
          }
        })
      );

      setLowerExtData(lowerExtMap);

      // Fetch Nadaraya-Watson lower band data for all symbols
      const nwMap = new Map<string, number>();
      await Promise.all(
        parsedSymbols.map(async (s) => {
          try {
            const response = await fetch(`${API_BASE_URL}/api/nadaraya-watson/metrics/${s.symbol}?length=200&bandwidth=8.0&atr_period=50&atr_mult=2.0&t=${Date.now()}`);
            if (response.ok) {
              const data = await response.json();
              if (data.lower_band) {
                nwMap.set(s.symbol, data.lower_band);
              }
            }
          } catch (err) {
            console.warn(`Failed to fetch Nadaraya-Watson for ${s.symbol}:`, err);
          }
        })
      );

      setNwLowerBandData(nwMap);
    } catch (err: any) {
      console.error('Failed to fetch gamma data:', err);
      setError(err.message || 'Failed to fetch data');
    } finally {
      setIsLoading(false);
    }
  }, []);

  // Auto-load data on mount
  useEffect(() => {
    fetchData();
    const interval = setInterval(fetchData, 5 * 60 * 1000); // Refresh every 5 minutes
    return () => clearInterval(interval);
  }, [fetchData]);

  // Convert ParsedSymbolData to RiskDistanceInput
  const riskInputs: RiskDistanceInput[] = useMemo(() => {
    return symbols.map(symbol => {
      // Find wall values from the parsed data
      const stPutWall = symbol.walls.find(w => w.type === 'put' && w.timeframe === 'swing');
      const ltPutWall = symbol.walls.find(w => w.type === 'put' && w.timeframe === 'long');
      const qPutWall = symbol.walls.find(w => w.type === 'put' && w.timeframe === 'quarterly');

      // Use real price if available, otherwise fall back to estimated price
      const currentPrice = realPrices.get(symbol.symbol) || symbol.currentPrice;

      // Calculate proper max pain using options pain theory
      // Max pain = strike price where option holders experience maximum loss
      const maxPain = calculateMaxPain(symbol, { currentPriceOverride: currentPrice, marketRegime });

      return {
        symbol: symbol.symbol,
        price: currentPrice,
        st_put: stPutWall?.strike || null,
        lt_put: ltPutWall?.strike || null,
        q_put: qPutWall?.strike || null,
        max_pain: maxPain,
        lower_ext: lowerExtData.get(symbol.symbol) || null,
        nw_lower_band: nwLowerBandData.get(symbol.symbol) || null,
        last_update: lastUpdate,
      };
    });
  }, [symbols, lastUpdate, realPrices, lowerExtData, nwLowerBandData, marketRegime]);

  // Calculate risk distances for all symbols
  const riskOutputs: RiskDistanceOutput[] = useMemo(() => {
    return riskInputs.map(input => calculateRiskDistances(input));
  }, [riskInputs]);

  // Toggle symbol selection
  const toggleSelect = useCallback((symbol: string) => {
    setSelectedSymbols(prev => {
      const next = new Set(prev);
      if (next.has(symbol)) {
        next.delete(symbol);
      } else {
        next.add(symbol);
      }
      return next;
    });
  }, []);

  // Select all / none
  const selectAll = useCallback(() => {
    setSelectedSymbols(new Set(riskOutputs.map(o => o.symbol)));
  }, [riskOutputs]);

  const selectNone = useCallback(() => {
    setSelectedSymbols(new Set());
  }, []);

  // Export selected symbols
  const handleExportJSON = useCallback(() => {
    const selected = riskOutputs.filter(o => selectedSymbols.has(o.symbol));
    const json = exportToJSON(selected);

    // Download as file
    const blob = new Blob([json], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `risk-distances-${Date.now()}.json`;
    a.click();
    URL.revokeObjectURL(url);
  }, [riskOutputs, selectedSymbols]);

  const handleExportCSV = useCallback(() => {
    const selected = riskOutputs.filter(o => selectedSymbols.has(o.symbol));
    const csv = exportToCSV(selected);

    // Download as file
    const blob = new Blob([csv], { type: 'text/csv' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `risk-distances-${Date.now()}.csv`;
    a.click();
    URL.revokeObjectURL(url);
  }, [riskOutputs, selectedSymbols]);

  // Copy JSON to clipboard
  const handleCopyJSON = useCallback(() => {
    const selected = riskOutputs.filter(o => selectedSymbols.has(o.symbol));
    const json = exportToJSON(selected);
    navigator.clipboard.writeText(json);
    alert('JSON copied to clipboard!');
  }, [riskOutputs, selectedSymbols]);

  return (
    <div style={styles.container}>
      {/* Header */}
      <div style={styles.header}>
        <div style={styles.headerLeft}>
          <h2 style={styles.title}>Risk Distance Analysis</h2>
          <p style={styles.subtitle}>
            Deterministic support distance calculations for Risk-Adjusted Expectancy
          </p>
        </div>
        <div style={styles.headerRight}>
          <button onClick={fetchData} disabled={isLoading} style={styles.refreshButton}>
            {isLoading ? '⟳' : '↻'} Refresh
          </button>
        </div>
      </div>

      {/* Error Banner */}
      {error && (
        <div style={styles.errorBanner}>
          <span style={styles.errorIcon}>⚠️</span>
          {error}
        </div>
      )}

      {/* Proximity Settings */}
      <div style={styles.settingsContainer}>
        <ProximitySettings
          config={proximityConfig}
          onChange={setProximityConfig}
          isExpanded={settingsExpanded}
          onToggleExpanded={() => setSettingsExpanded(!settingsExpanded)}
        />
      </div>

      {/* Toolbar */}
      <div style={styles.toolbar}>
        <div style={styles.toolbarLeft}>
          <span style={styles.toolbarText}>
            {symbols.length} symbols | {selectedSymbols.size} selected
          </span>
          <button onClick={selectAll} style={styles.toolbarButton}>
            Select All
          </button>
          <button onClick={selectNone} style={styles.toolbarButton}>
            Select None
          </button>
        </div>
        <div style={styles.toolbarRight}>
          <button
            onClick={handleCopyJSON}
            disabled={selectedSymbols.size === 0}
            style={styles.exportButton}
          >
            📋 Copy JSON
          </button>
          <button
            onClick={handleExportJSON}
            disabled={selectedSymbols.size === 0}
            style={styles.exportButton}
          >
            💾 Export JSON
          </button>
          <button
            onClick={handleExportCSV}
            disabled={selectedSymbols.size === 0}
            style={styles.exportButton}
          >
            📊 Export CSV
          </button>
        </div>
      </div>

      {/* Symbol Cards Grid */}
      {symbols.length === 0 && !isLoading && !error && (
        <div style={styles.emptyState}>
          <div style={styles.emptyIcon}>📊</div>
          <div style={styles.emptyText}>No data loaded</div>
          <div style={styles.emptyHint}>Click Refresh to load gamma data</div>
        </div>
      )}

      {riskOutputs.length > 0 && (
        <div style={styles.grid}>
          {riskOutputs.map((output, idx) => (
            <SymbolCard
              key={idx}
              data={output}
              selected={selectedSymbols.has(output.symbol)}
              onSelect={toggleSelect}
              lowerExtThresholdPct={proximityConfig.lowerExtThresholdPct}
              nwBandThresholdPct={proximityConfig.nwBandThresholdPct}
              useAbsoluteDistance={proximityConfig.useAbsoluteDistance}
            />
          ))}
        </div>
      )}

      {/* Loading Overlay */}
      {isLoading && (
        <div style={styles.loadingOverlay}>
          <div style={styles.spinner} />
          <div style={styles.loadingText}>Loading data...</div>
        </div>
      )}

      {/* Info Footer */}
      <div style={styles.footer}>
        <div style={styles.footerText}>
          <strong>Note:</strong> This component provides deterministic distance calculations only.
          No subjective recommendations are included. Export JSON for integration with composite scoring systems.
        </div>
        <div style={styles.footerUpdate}>Last updated: {lastUpdate}</div>
      </div>
    </div>
  );
};

const styles: Record<string, React.CSSProperties> = {
  container: {
    width: '100%',
    height: '100vh',
    backgroundColor: '#0D1117',
    color: '#D1D4DC',
    fontFamily: '"Roboto", "Open Sans", "Arial", sans-serif',
    display: 'flex',
    flexDirection: 'column',
    overflow: 'hidden',
  },

  // Header
  header: {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    padding: '20px 24px',
    backgroundColor: '#1C2128',
    borderBottom: '1px solid #373E47',
  },
  headerLeft: {
    flex: 1,
  },
  headerRight: {
    display: 'flex',
    gap: '12px',
  },
  title: {
    margin: 0,
    fontSize: '20px',
    fontWeight: 700,
    color: '#D1D4DC',
  },
  subtitle: {
    margin: '4px 0 0 0',
    fontSize: '13px',
    color: '#8B949E',
  },
  refreshButton: {
    padding: '8px 16px',
    fontSize: '13px',
    fontWeight: 600,
    color: '#D1D4DC',
    backgroundColor: 'transparent',
    border: '1px solid #373E47',
    borderRadius: '6px',
    cursor: 'pointer',
    transition: 'all 0.2s',
  },

  // Error Banner
  errorBanner: {
    display: 'flex',
    alignItems: 'center',
    gap: '10px',
    padding: '12px 24px',
    backgroundColor: 'rgba(239, 83, 80, 0.12)',
    borderBottom: '1px solid #EF5350',
    color: '#EF5350',
    fontSize: '13px',
  },
  errorIcon: {
    fontSize: '16px',
  },

  // Settings Container
  settingsContainer: {
    padding: '16px 24px 0 24px',
    backgroundColor: '#0D1117',
  },

  // Toolbar
  toolbar: {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    padding: '12px 24px',
    backgroundColor: '#1C2128',
    borderBottom: '1px solid #373E47',
  },
  toolbarLeft: {
    display: 'flex',
    alignItems: 'center',
    gap: '12px',
  },
  toolbarRight: {
    display: 'flex',
    gap: '8px',
  },
  toolbarText: {
    fontSize: '12px',
    color: '#8B949E',
  },
  toolbarButton: {
    padding: '6px 12px',
    fontSize: '11px',
    fontWeight: 600,
    color: '#D1D4DC',
    backgroundColor: 'transparent',
    border: '1px solid #373E47',
    borderRadius: '4px',
    cursor: 'pointer',
    transition: 'all 0.2s',
  },
  exportButton: {
    padding: '6px 14px',
    fontSize: '12px',
    fontWeight: 600,
    color: '#FFFFFF',
    backgroundColor: '#2962FF',
    border: 'none',
    borderRadius: '5px',
    cursor: 'pointer',
    transition: 'all 0.2s',
  },

  // Grid
  grid: {
    flex: 1,
    padding: '20px 24px',
    display: 'grid',
    gridTemplateColumns: 'repeat(auto-fill, minmax(450px, 1fr))',
    gap: '16px',
    overflowY: 'auto',
    alignContent: 'start',
  },

  // Empty State
  emptyState: {
    flex: 1,
    display: 'flex',
    flexDirection: 'column',
    alignItems: 'center',
    justifyContent: 'center',
    gap: '16px',
  },
  emptyIcon: {
    fontSize: '64px',
    opacity: 0.3,
  },
  emptyText: {
    fontSize: '18px',
    fontWeight: 600,
    color: '#D1D4DC',
  },
  emptyHint: {
    fontSize: '13px',
    color: '#8B949E',
  },

  // Loading Overlay
  loadingOverlay: {
    position: 'absolute' as const,
    top: 0,
    left: 0,
    right: 0,
    bottom: 0,
    display: 'flex',
    flexDirection: 'column',
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: 'rgba(13, 17, 23, 0.9)',
    gap: '16px',
    zIndex: 1000,
  },
  spinner: {
    width: '40px',
    height: '40px',
    border: '4px solid #373E47',
    borderTop: '4px solid #2962FF',
    borderRadius: '50%',
    animation: 'spin 0.8s linear infinite',
  },
  loadingText: {
    fontSize: '13px',
    color: '#8B949E',
  },

  // Footer
  footer: {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    padding: '12px 24px',
    backgroundColor: '#1C2128',
    borderTop: '1px solid #373E47',
    fontSize: '11px',
    color: '#6E7681',
  },
  footerText: {
    flex: 1,
  },
  footerUpdate: {
    whiteSpace: 'nowrap' as const,
  },
};
