/**
 * Gamma Scanner Tab v3.0 - Full TradingView Experience
 * Complete integration with candlestick charts, timeframe selector, and bottom metrics panel
 */

import React, { useState, useCallback, useEffect } from 'react';
import { GammaChartCanvasV3 } from './GammaChartCanvas.v3';
import { GammaControlPanel } from './GammaControlPanel';
import { SymbolMetricsTable } from './SymbolMetricsTable';
import { GammaDataParser } from './dataParser';
import { ParsedSymbolData, GammaScannerSettings } from './types';

// TradingView Color Palette
const TV_COLORS = {
  background: '#131722',
  surface: '#1E222D',
  border: '#2A2E39',
  text: '#787B86',
  textBright: '#D1D4DC',
  blue: '#2962FF',
  green: '#26A69A',
  red: '#EF5350',
  orange: '#FFA726',
};

type TimeframeOption = '1D' | '1H' | '5M' | '15M' | '4H';

export const GammaScannerTabV3: React.FC = () => {
  const [symbols, setSymbols] = useState<ParsedSymbolData[]>([]);
  const [settings, setSettings] = useState<GammaScannerSettings>({
    selectedSymbols: [],
    showSwingWalls: true,
    showLongWalls: true,
    showQuarterlyWalls: true,
    showSDBands: true,
    showGammaFlip: true,
    showLabels: true,
    showTable: true,
    wallOpacity: 0.8,
    minStrength: 0,
    hideWeakWalls: false,
    applyRegimeAdjustment: true,
    dataSource: 'api',
    colorScheme: 'default',
    apiPollingInterval: 60,
  });
  const [marketRegime, setMarketRegime] = useState<string>('Normal Vol');
  const [vix, setVix] = useState<number>(0);
  const [lastUpdate, setLastUpdate] = useState<string>('');
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [error, setError] = useState<string>('');
  const [isLive, setIsLive] = useState<boolean>(false);
  const [sidebarCollapsed, setSidebarCollapsed] = useState<boolean>(false);
  const [metricsExpanded, setMetricsExpanded] = useState<boolean>(true);
  const [timeframe, setTimeframe] = useState<TimeframeOption>('1D');

  // Fetch data from API
  const fetchData = useCallback(async () => {
    if (settings.dataSource !== 'api') return;

    setIsLoading(true);
    setError('');

    try {
      const response = await fetch('/api/gamma-data');
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }

      const data = await response.json();
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
      setVix(data.vix || 0);
      setMarketRegime(data.market_regime || 'Normal Vol');
      setIsLive(true);
      setError('');
    } catch (err: any) {
      console.error('Failed to fetch gamma data:', err);
      setError(err.message || 'Failed to fetch data');
      setIsLive(false);
    } finally {
      setIsLoading(false);
    }
  }, [settings.dataSource]);

  // Auto-refresh every 5 minutes
  useEffect(() => {
    if (settings.dataSource === 'api') {
      fetchData();
      const interval = setInterval(fetchData, 5 * 60 * 1000);
      return () => clearInterval(interval);
    }
  }, [settings.dataSource, fetchData]);

  // Manual paste handler
  const handlePasteData = useCallback((pastedText: string) => {
    const parser = new GammaDataParser();
    const lines = pastedText.split('\n').filter((l) => l.trim().length > 0);
    const parsedSymbols: ParsedSymbolData[] = [];

    lines.forEach((line, index) => {
      const parsed = parser.parseLevelData(line, index + 1);
      if (parsed) {
        parsedSymbols.push(parsed);
      }
    });

    if (parsedSymbols.length > 0) {
      setSymbols(parsedSymbols);
      setLastUpdate(new Date().toLocaleString());
      setError('');
      setIsLive(false);
    } else {
      setError('No valid data found in pasted text');
    }
  }, []);

  // Settings update handler
  const handleSettingsChange = useCallback((updates: Partial<GammaScannerSettings>) => {
    setSettings((prev) => ({ ...prev, ...updates }));
  }, []);

  return (
    <div style={styles.container}>
      {/* TOP BAR */}
      <div style={styles.topBar}>
        <div style={styles.topBarLeft}>
          <span style={styles.title}>GAMMA WALL SCANNER</span>
          <div style={styles.divider} />
          {vix > 0 && (
            <>
              <span style={styles.metric}>VIX {vix.toFixed(1)}</span>
              <div style={styles.divider} />
            </>
          )}
          <span style={styles.metric}>Regime: {marketRegime}</span>
          <div style={styles.divider} />
          <span style={styles.metric}>Updated: {lastUpdate}</span>
        </div>

        <div style={styles.topBarRight}>
          {/* TIMEFRAME SELECTOR */}
          <div style={styles.timeframeSelector}>
            {(['5M', '15M', '1H', '4H', '1D'] as TimeframeOption[]).map((tf) => (
              <button
                key={tf}
                onClick={() => setTimeframe(tf)}
                style={{
                  ...styles.timeframeButton,
                  ...(timeframe === tf ? styles.timeframeButtonActive : {}),
                }}
              >
                {tf}
              </button>
            ))}
          </div>

          <div style={styles.divider} />

          {/* STATUS INDICATOR */}
          <div style={styles.statusContainer}>
            <div
              style={{
                ...styles.statusDot,
                backgroundColor: isLive ? TV_COLORS.green : TV_COLORS.red,
              }}
            />
            <span style={styles.statusText}>{isLive ? 'Live' : 'Offline'}</span>
          </div>
        </div>
      </div>

      {/* MAIN CONTENT */}
      <div style={styles.mainContent}>
        {/* SIDEBAR (COLLAPSIBLE) */}
        <div style={{ ...styles.sidebar, width: sidebarCollapsed ? '40px' : '280px' }}>
          {sidebarCollapsed ? (
            <button onClick={() => setSidebarCollapsed(false)} style={styles.expandButton}>
              ☰
            </button>
          ) : (
            <>
              <div style={styles.sidebarHeader}>
                <span style={styles.sidebarTitle}>Controls</span>
                <button onClick={() => setSidebarCollapsed(true)} style={styles.collapseButton}>
                  ✕
                </button>
              </div>
              <GammaControlPanel
                settings={settings}
                onSettingsChange={handleSettingsChange}
                availableSymbols={symbols.map((s) => s.symbol)}
                onManualPaste={handlePasteData}
                onRefresh={fetchData}
                loading={isLoading}
              />
            </>
          )}
        </div>

        {/* CHART CANVAS */}
        <div style={styles.chartContainer}>
          {error && (
            <div style={styles.errorBanner}>
              <span style={styles.errorIcon}>⚠️</span>
              {error}
            </div>
          )}

          {symbols.length === 0 && !isLoading && !error && (
            <div style={styles.emptyState}>
              <div style={styles.emptyStateIcon}>📊</div>
              <div style={styles.emptyStateText}>No data loaded</div>
              <div style={styles.emptyStateHint}>
                {settings.dataSource === 'api'
                  ? 'Waiting for API data...'
                  : 'Paste level_data strings in the control panel'}
              </div>
            </div>
          )}

          {symbols.length > 0 && (
            <>
              <GammaChartCanvasV3
                symbols={symbols}
                settings={settings}
                marketRegime={marketRegime}
                timeframe={timeframe}
              />

              {/* BOTTOM METRICS PANEL (COLLAPSIBLE) */}
              <div style={styles.bottomPanel}>
                <button onClick={() => setMetricsExpanded(!metricsExpanded)} style={styles.metricsToggle}>
                  <span style={styles.metricsToggleText}>Symbol Metrics</span>
                  <span style={styles.metricsToggleIcon}>{metricsExpanded ? '▼' : '▲'}</span>
                </button>

                {metricsExpanded && (
                  <div style={styles.metricsTableContainer}>
                    <SymbolMetricsTable symbols={symbols} />
                  </div>
                )}
              </div>
            </>
          )}

          {isLoading && (
            <div style={styles.loadingOverlay}>
              <div style={styles.spinner} />
              <div style={styles.loadingText}>Loading gamma data...</div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

const styles: Record<string, React.CSSProperties> = {
  container: {
    display: 'flex',
    flexDirection: 'column',
    width: '100%',
    height: '100vh',
    backgroundColor: TV_COLORS.background,
    fontFamily: '"Roboto", "Open Sans", "Arial", sans-serif',
    color: TV_COLORS.textBright,
  },

  // TOP BAR
  topBar: {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    padding: '8px 16px',
    backgroundColor: TV_COLORS.surface,
    borderBottom: `1px solid ${TV_COLORS.border}`,
    height: '40px',
    flexShrink: 0,
  },
  topBarLeft: {
    display: 'flex',
    alignItems: 'center',
    gap: '12px',
  },
  topBarRight: {
    display: 'flex',
    alignItems: 'center',
    gap: '12px',
  },
  title: {
    fontSize: '13px',
    fontWeight: 600,
    color: TV_COLORS.textBright,
    letterSpacing: '0.5px',
  },
  metric: {
    fontSize: '11px',
    color: TV_COLORS.text,
  },
  divider: {
    width: '1px',
    height: '16px',
    backgroundColor: TV_COLORS.border,
  },

  // TIMEFRAME SELECTOR
  timeframeSelector: {
    display: 'flex',
    gap: '4px',
    backgroundColor: TV_COLORS.background,
    borderRadius: '4px',
    padding: '2px',
  },
  timeframeButton: {
    padding: '4px 10px',
    fontSize: '11px',
    fontWeight: 500,
    color: TV_COLORS.text,
    backgroundColor: 'transparent',
    border: 'none',
    borderRadius: '3px',
    cursor: 'pointer',
    transition: 'all 0.2s ease',
  },
  timeframeButtonActive: {
    color: TV_COLORS.textBright,
    backgroundColor: TV_COLORS.blue,
  },

  // STATUS
  statusContainer: {
    display: 'flex',
    alignItems: 'center',
    gap: '6px',
  },
  statusDot: {
    width: '8px',
    height: '8px',
    borderRadius: '50%',
    animation: 'pulse 2s infinite',
  },
  statusText: {
    fontSize: '11px',
    fontWeight: 500,
    color: TV_COLORS.text,
  },

  // MAIN CONTENT
  mainContent: {
    display: 'flex',
    flex: 1,
    overflow: 'hidden',
  },

  // SIDEBAR
  sidebar: {
    display: 'flex',
    flexDirection: 'column',
    backgroundColor: TV_COLORS.surface,
    borderRight: `1px solid ${TV_COLORS.border}`,
    transition: 'width 0.3s ease',
    overflow: 'hidden',
    flexShrink: 0,
  },
  sidebarHeader: {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    padding: '12px 16px',
    borderBottom: `1px solid ${TV_COLORS.border}`,
  },
  sidebarTitle: {
    fontSize: '12px',
    fontWeight: 600,
    color: TV_COLORS.textBright,
    textTransform: 'uppercase',
    letterSpacing: '0.5px',
  },
  collapseButton: {
    padding: '4px 8px',
    fontSize: '12px',
    color: TV_COLORS.text,
    backgroundColor: 'transparent',
    border: 'none',
    borderRadius: '3px',
    cursor: 'pointer',
    transition: 'all 0.2s ease',
  },
  expandButton: {
    width: '100%',
    padding: '12px 0',
    fontSize: '18px',
    color: TV_COLORS.text,
    backgroundColor: 'transparent',
    border: 'none',
    cursor: 'pointer',
    transition: 'color 0.2s ease',
  },

  // CHART CONTAINER
  chartContainer: {
    flex: 1,
    display: 'flex',
    flexDirection: 'column',
    position: 'relative',
    overflow: 'hidden',
    backgroundColor: TV_COLORS.background,
  },

  // BOTTOM METRICS PANEL
  bottomPanel: {
    backgroundColor: TV_COLORS.surface,
    borderTop: `1px solid ${TV_COLORS.border}`,
    flexShrink: 0,
  },
  metricsToggle: {
    width: '100%',
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    padding: '10px 16px',
    backgroundColor: TV_COLORS.surface,
    border: 'none',
    cursor: 'pointer',
    transition: 'background-color 0.2s ease',
  },
  metricsToggleText: {
    fontSize: '12px',
    fontWeight: 600,
    color: TV_COLORS.textBright,
    textTransform: 'uppercase',
    letterSpacing: '0.5px',
  },
  metricsToggleIcon: {
    fontSize: '10px',
    color: TV_COLORS.text,
  },
  metricsTableContainer: {
    maxHeight: '300px',
    overflowY: 'auto',
    padding: '8px 16px 16px 16px',
  },

  // ERROR BANNER
  errorBanner: {
    display: 'flex',
    alignItems: 'center',
    gap: '10px',
    padding: '12px 16px',
    backgroundColor: 'rgba(239, 83, 80, 0.15)',
    borderBottom: `1px solid ${TV_COLORS.red}`,
    color: TV_COLORS.red,
    fontSize: '12px',
  },
  errorIcon: {
    fontSize: '16px',
  },

  // EMPTY STATE
  emptyState: {
    display: 'flex',
    flexDirection: 'column',
    alignItems: 'center',
    justifyContent: 'center',
    height: '100%',
    gap: '16px',
  },
  emptyStateIcon: {
    fontSize: '64px',
    opacity: 0.3,
  },
  emptyStateText: {
    fontSize: '18px',
    fontWeight: 500,
    color: TV_COLORS.textBright,
  },
  emptyStateHint: {
    fontSize: '13px',
    color: TV_COLORS.text,
    maxWidth: '400px',
    textAlign: 'center',
  },

  // LOADING OVERLAY
  loadingOverlay: {
    position: 'absolute',
    top: 0,
    left: 0,
    right: 0,
    bottom: 0,
    display: 'flex',
    flexDirection: 'column',
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: 'rgba(19, 23, 34, 0.85)',
    gap: '16px',
    zIndex: 1000,
  },
  spinner: {
    width: '40px',
    height: '40px',
    border: `4px solid ${TV_COLORS.border}`,
    borderTop: `4px solid ${TV_COLORS.blue}`,
    borderRadius: '50%',
    animation: 'spin 1s linear infinite',
  },
  loadingText: {
    fontSize: '13px',
    color: TV_COLORS.text,
  },
};
