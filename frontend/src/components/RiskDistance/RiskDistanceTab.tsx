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

type ScannerJsonSymbol = {
  symbol: string;
  current_price: number;
  st_put_wall: number;
  lt_put_wall: number;
  q_put_wall: number;
  max_pain?: number;
};

type ScannerJsonPayload = {
  last_update?: string;
  market_regime?: string;
  vix?: number;
  symbols?: Record<string, ScannerJsonSymbol>;
};

export const RiskDistanceTab: React.FC = () => {
  const [symbols, setSymbols] = useState<ParsedSymbolData[]>([]);
  const [selectedSymbols, setSelectedSymbols] = useState<Set<string>>(new Set());
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string>('');
  const [lastUpdate, setLastUpdate] = useState<string>('');
  const [marketRegime, setMarketRegime] = useState<string>('');
  const [scannerJson, setScannerJson] = useState<ScannerJsonPayload | null>(null);
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

  // Nadaraya-Watson parameters (match PineScript indicator inputs)
  const [nwConfig, setNwConfig] = useState({
    length: 200,
    bandwidth: 8.0,
    atrPeriod: 50,
    atrMult: 2.0,
  });

  // Fetch data from API
  const fetchData = useCallback(async (forceRefresh: boolean = false) => {
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
        const url = `${API_BASE_URL}/api/gamma-data?t=${Date.now()}${forceRefresh ? '&force_refresh=true' : ''}`;
        data = await fetchJson(url);
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

      // Pull enhanced scanner JSON (source of truth for proximity-filtered walls and 7D max pain)
      let scanner: ScannerJsonPayload | null = null;
      try {
        const url = `${API_BASE_URL}/api/gamma-data/scanner-json?t=${Date.now()}${forceRefresh ? '&force_refresh=true' : ''}`;
        scanner = await fetchJson(url);
        setScannerJson(scanner);
        if (scanner?.last_update) setLastUpdate(scanner.last_update);
        if (scanner?.market_regime) setMarketRegime(scanner.market_regime);
      } catch (scannerErr) {
        console.warn('Failed to fetch scanner-json (will fall back to parsed level_data only):', scannerErr);
        setScannerJson(null);
      }

      const scannerSymbols = scanner?.symbols ? Object.keys(scanner.symbols) : [];
      const parsedSymbolNames = parsedSymbols.map(s => s.symbol);
      const symbolUniverse = Array.from(new Set([...scannerSymbols, ...parsedSymbolNames]));

      // Fetch real prices for all symbols we plan to display
      const priceRequests = symbolUniverse.map(symbol => {
        const parsed = parsedSymbols.find(s => s.symbol === symbol);
        const scannerPrice = scanner?.symbols?.[symbol]?.current_price;
        return {
          symbol,
          estimatedPrice: parsed?.currentPrice || (typeof scannerPrice === 'number' ? scannerPrice : 0),
        };
      });

      const prices = await batchGetPrices(priceRequests);
      const priceMap = new Map<string, number>();

      prices.forEach((priceData, symbol) => {
        priceMap.set(symbol, priceData.price);
      });

      setRealPrices(priceMap);

      // Fetch lower extension data for all symbols
      const lowerExtMap = new Map<string, number>();
      await Promise.all(
        symbolUniverse.map(async (symbol) => {
          try {
            const response = await fetch(`${API_BASE_URL}/api/lower-extension/metrics/${symbol}?length=30&lookback_days=30&t=${Date.now()}`);
            if (response.ok) {
              const data = await response.json();
              if (data.lower_ext) {
                lowerExtMap.set(symbol, data.lower_ext);
              }
            }
          } catch (err) {
            console.warn(`Failed to fetch lower extension for ${symbol}:`, err);
          }
        })
      );

      setLowerExtData(lowerExtMap);

      // Fetch Nadaraya-Watson lower band data for all symbols
      const nwMap = new Map<string, number>();
      await Promise.all(
        symbolUniverse.map(async (symbol) => {
          try {
            const response = await fetch(
              `${API_BASE_URL}/api/nadaraya-watson/metrics/${symbol}?length=${nwConfig.length}&bandwidth=${nwConfig.bandwidth}&atr_period=${nwConfig.atrPeriod}&atr_mult=${nwConfig.atrMult}&t=${Date.now()}`
            );
            if (response.ok) {
              const data = await response.json();
              if (typeof data.lower_band === 'number') {
                nwMap.set(symbol, data.lower_band);
              }
            }
          } catch (err) {
            console.warn(`Failed to fetch Nadaraya-Watson for ${symbol}:`, err);
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
  }, [nwConfig.atrMult, nwConfig.atrPeriod, nwConfig.bandwidth, nwConfig.length]);

  // Auto-load data on mount
  useEffect(() => {
    fetchData();
    const interval = setInterval(fetchData, 5 * 60 * 1000); // Refresh every 5 minutes
    return () => clearInterval(interval);
  }, [fetchData]);

  // Convert ParsedSymbolData to RiskDistanceInput
  const riskInputs: RiskDistanceInput[] = useMemo(() => {
    const scannerSymbols = scannerJson?.symbols || {};
    const scannerSymbolNames = Object.keys(scannerSymbols);
    const parsedSymbolNames = symbols.map(s => s.symbol);
    const displaySymbols = scannerSymbolNames.length ? scannerSymbolNames : parsedSymbolNames;

    return displaySymbols.map(symbolName => {
      const parsed = symbols.find(s => s.symbol === symbolName) || null;
      const scanner = scannerSymbols[symbolName];

      const currentPrice =
        realPrices.get(symbolName) ||
        (scanner && typeof scanner.current_price === 'number' ? scanner.current_price : null) ||
        parsed?.currentPrice ||
        null;

      const stPutWall = parsed?.walls.find(w => w.type === 'put' && w.timeframe === 'swing')?.strike ?? null;
      const ltPutWall = parsed?.walls.find(w => w.type === 'put' && w.timeframe === 'long')?.strike ?? null;
      const qPutWall = parsed?.walls.find(w => w.type === 'put' && w.timeframe === 'quarterly')?.strike ?? null;

      const stPut = (scanner && scanner.st_put_wall) || stPutWall || null;
      const ltPut = (scanner && scanner.lt_put_wall) || ltPutWall || null;
      const qPut = (scanner && scanner.q_put_wall) || qPutWall || null;

      const scannerMaxPain = scanner?.max_pain && scanner.max_pain > 0 ? scanner.max_pain : null;
      const fallbackMaxPain =
        parsed && currentPrice !== null
          ? calculateMaxPain(parsed, { currentPriceOverride: currentPrice, marketRegime })
          : null;
      const maxPain = scannerMaxPain ?? fallbackMaxPain;

      return {
        symbol: symbolName,
        price: currentPrice,
        st_put: stPut,
        lt_put: ltPut,
        q_put: qPut,
        max_pain: maxPain,
        lower_ext: lowerExtData.get(symbolName) || null,
        nw_lower_band: nwLowerBandData.get(symbolName) || null,
        last_update: lastUpdate,
      };
    });
  }, [symbols, lastUpdate, realPrices, lowerExtData, nwLowerBandData, marketRegime, scannerJson]);

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
          <button onClick={() => fetchData(true)} disabled={isLoading} style={styles.refreshButton}>
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
        <div style={styles.nwSettingsContainer}>
          <div style={styles.nwSettingsHeader}>
            <span style={styles.nwSettingsTitle}>NW Envelope Settings</span>
            <span style={styles.nwSettingsSubtitle}>Matches PineScript inputs</span>
          </div>

          <div style={styles.nwSettingsGrid}>
            <label style={styles.nwSettingsLabel} htmlFor="nw-length">
              Window Size
            </label>
            <input
              id="nw-length"
              type="number"
              min={20}
              max={500}
              step={1}
              value={nwConfig.length}
              onChange={(e) => setNwConfig((prev) => ({ ...prev, length: Number(e.target.value) }))}
              style={styles.nwSettingsInput}
            />

            <label style={styles.nwSettingsLabel} htmlFor="nw-bandwidth">
              Bandwidth
            </label>
            <input
              id="nw-bandwidth"
              type="number"
              min={0.1}
              step={0.1}
              value={nwConfig.bandwidth}
              onChange={(e) => setNwConfig((prev) => ({ ...prev, bandwidth: Number(e.target.value) }))}
              style={styles.nwSettingsInput}
            />

            <label style={styles.nwSettingsLabel} htmlFor="nw-atr-period">
              ATR Period
            </label>
            <input
              id="nw-atr-period"
              type="number"
              min={10}
              step={1}
              value={nwConfig.atrPeriod}
              onChange={(e) => setNwConfig((prev) => ({ ...prev, atrPeriod: Number(e.target.value) }))}
              style={styles.nwSettingsInput}
            />

            <label style={styles.nwSettingsLabel} htmlFor="nw-atr-mult">
              ATR Mult
            </label>
            <input
              id="nw-atr-mult"
              type="number"
              min={0.1}
              step={0.1}
              value={nwConfig.atrMult}
              onChange={(e) => setNwConfig((prev) => ({ ...prev, atrMult: Number(e.target.value) }))}
              style={styles.nwSettingsInput}
            />
          </div>

          <div style={styles.nwSettingsNote}>
            NW Band value used in Risk Distance is the indicator’s `lower_band` (support).
          </div>
          <div style={styles.nwSettingsFooter}>
            <button
              onClick={() => setNwConfig({ length: 200, bandwidth: 8.0, atrPeriod: 50, atrMult: 2.0 })}
              style={styles.nwSettingsResetButton}
            >
              Reset NW Defaults
            </button>
          </div>
        </div>
      </div>

      {/* Toolbar */}
      <div style={styles.toolbar}>
        <div style={styles.toolbarLeft}>
          <span style={styles.toolbarText}>
            {riskOutputs.length} symbols | {selectedSymbols.size} selected
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

  nwSettingsContainer: {
    backgroundColor: '#1C2128',
    border: '1px solid #373E47',
    borderRadius: '6px',
    padding: '12px 16px',
    marginBottom: '16px',
  },
  nwSettingsHeader: {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'baseline',
    marginBottom: '10px',
  },
  nwSettingsTitle: {
    fontSize: '13px',
    fontWeight: 600,
    color: '#D1D4DC',
  },
  nwSettingsSubtitle: {
    fontSize: '11px',
    color: '#6E7681',
  },
  nwSettingsLabel: {
    fontSize: '12px',
    color: '#8B949E',
    minWidth: '84px',
  },
  nwSettingsGrid: {
    display: 'grid',
    gridTemplateColumns: '96px 1fr',
    gap: '10px 12px',
    alignItems: 'center',
  },
  nwSettingsInput: {
    backgroundColor: '#0D1117',
    border: '1px solid #373E47',
    color: '#D1D4DC',
    borderRadius: '6px',
    padding: '8px 10px',
    fontSize: '12px',
    fontFamily: 'monospace',
    outline: 'none',
  },
  nwSettingsNote: {
    marginTop: '8px',
    fontSize: '11px',
    color: '#6E7681',
  },
  nwSettingsFooter: {
    marginTop: '10px',
    display: 'flex',
    justifyContent: 'flex-end',
  },
  nwSettingsResetButton: {
    padding: '6px 10px',
    fontSize: '11px',
    fontWeight: 600,
    color: '#D1D4DC',
    backgroundColor: 'transparent',
    border: '1px solid #373E47',
    borderRadius: '6px',
    cursor: 'pointer',
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
