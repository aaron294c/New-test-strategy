/**
 * Gamma Scanner Tab v4.0 - TradingView Quality Interface
 * Professional gradients, compact layout, maximum chart real estate
 */

import React, { useState, useCallback, useEffect } from 'react';
import { GammaChartCanvasV4 } from './GammaChartCanvas.v4';
import { GammaSidebarV4 } from './GammaSidebar.v4';
import { SymbolMetricsTable } from './SymbolMetricsTable';
import { GammaDataParser } from './dataParser';
import { ParsedSymbolData, GammaScannerSettings } from './types';
import { THEME_COLORS } from './colors';

type TimeframeOption = '1D' | '1H' | '5M' | '15M' | '4H';

export const GammaScannerTabV4: React.FC = () => {
  const [symbols, setSymbols] = useState<ParsedSymbolData[]>([]);
  const [settings, setSettings] = useState<GammaScannerSettings>({
    selectedSymbols: [],
    showSwingWalls: true,
    showLongWalls: true,
    showQuarterlyWalls: false,
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
      {/* COMPACT TOP BAR (30px) */}
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
          <span style={styles.metric}>{marketRegime}</span>
          <div style={styles.divider} />
          <span style={styles.metricTime}>{lastUpdate}</span>
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
                backgroundColor: isLive ? THEME_COLORS.green : THEME_COLORS.red,
              }}
            />
            <span style={styles.statusText}>{isLive ? 'Live' : 'Offline'}</span>
          </div>
        </div>
      </div>

      {/* MAIN CONTENT */}
      <div style={styles.mainContent}>
        {/* COMPACT SIDEBAR (220px) */}
        <div style={{ ...styles.sidebar, width: sidebarCollapsed ? '36px' : '220px' }}>
          {sidebarCollapsed ? (
            <button onClick={() => setSidebarCollapsed(false)} style={styles.expandButton}>
              ☰
            </button>
          ) : (
            <>
              <div style={styles.sidebarHeader}>
                <button onClick={() => setSidebarCollapsed(true)} style={styles.collapseButton}>
                  ✕
                </button>
              </div>
              <GammaSidebarV4
                settings={settings}
                onSettingsChange={handleSettingsChange}
                symbols={symbols.map((s) => s.symbol)}
                onManualPaste={handlePasteData}
                onRefresh={fetchData}
                loading={isLoading}
              />
            </>
          )}
        </div>

        {/* CHART CONTAINER - Maximum Real Estate */}
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
              <div style={styles.chartWrapper}>
                <GammaChartCanvasV4
                  symbols={symbols}
                  settings={settings}
                  marketRegime={marketRegime}
                  timeframe={timeframe}
                />
              </div>

              {/* COMPACT BOTTOM METRICS PANEL (120px fixed) */}
              {settings.showTable && (
                <div style={styles.bottomPanel}>
                  <button
                    onClick={() => setMetricsExpanded(!metricsExpanded)}
                    style={styles.metricsToggle}
                  >
                    <span style={styles.metricsToggleText}>
                      📈 SYMBOL METRICS ({symbols.length})
                    </span>
                    <span style={styles.metricsToggleIcon}>{metricsExpanded ? '▼' : '▲'}</span>
                  </button>

                  {metricsExpanded && (
                    <div style={styles.metricsTableContainer}>
                      <SymbolMetricsTable symbols={symbols} />
                    </div>
                  )}
                </div>
              )}
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
    backgroundColor: THEME_COLORS.background,
    fontFamily: '"Roboto", "Open Sans", "Arial", sans-serif',
    color: THEME_COLORS.textBright,
  },

  // COMPACT TOP BAR (30px instead of 40px)
  topBar: {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    padding: '6px 16px',
    backgroundColor: THEME_COLORS.surface,
    borderBottom: `1px solid ${THEME_COLORS.border}`,
    height: '30px',
    flexShrink: 0,
  },
  topBarLeft: {
    display: 'flex',
    alignItems: 'center',
    gap: '10px',
  },
  topBarRight: {
    display: 'flex',
    alignItems: 'center',
    gap: '10px',
  },
  title: {
    fontSize: '11px',
    fontWeight: 700,
    color: THEME_COLORS.textBright,
    letterSpacing: '0.6px',
  },
  metric: {
    fontSize: '10px',
    color: THEME_COLORS.text,
  },
  metricTime: {
    fontSize: '9px',
    color: THEME_COLORS.textMuted,
  },
  divider: {
    width: '1px',
    height: '14px',
    backgroundColor: THEME_COLORS.border,
  },

  // TIMEFRAME SELECTOR
  timeframeSelector: {
    display: 'flex',
    gap: '3px',
    backgroundColor: THEME_COLORS.background,
    borderRadius: '4px',
    padding: '2px',
  },
  timeframeButton: {
    padding: '4px 9px',
    fontSize: '10px',
    fontWeight: 600,
    color: THEME_COLORS.text,
    backgroundColor: 'transparent',
    border: 'none',
    borderRadius: '3px',
    cursor: 'pointer',
    transition: 'all 0.15s',
  },
  timeframeButtonActive: {
    color: '#FFFFFF',
    backgroundColor: THEME_COLORS.blue,
    boxShadow: '0 0 8px rgba(41, 98, 255, 0.4)',
  },

  // STATUS
  statusContainer: {
    display: 'flex',
    alignItems: 'center',
    gap: '5px',
  },
  statusDot: {
    width: '7px',
    height: '7px',
    borderRadius: '50%',
  },
  statusText: {
    fontSize: '10px',
    fontWeight: 600,
    color: THEME_COLORS.text,
  },

  // MAIN CONTENT
  mainContent: {
    display: 'flex',
    flex: 1,
    overflow: 'hidden',
  },

  // COMPACT SIDEBAR (220px instead of 280px)
  sidebar: {
    display: 'flex',
    flexDirection: 'column',
    backgroundColor: THEME_COLORS.surface,
    borderRight: `1px solid ${THEME_COLORS.border}`,
    transition: 'width 0.25s ease',
    overflow: 'hidden',
    flexShrink: 0,
  },
  sidebarHeader: {
    display: 'flex',
    justifyContent: 'flex-end',
    padding: '8px 10px',
    borderBottom: `1px solid ${THEME_COLORS.border}`,
  },
  collapseButton: {
    padding: '4px 8px',
    fontSize: '11px',
    color: THEME_COLORS.text,
    backgroundColor: 'transparent',
    border: 'none',
    borderRadius: '3px',
    cursor: 'pointer',
    transition: 'all 0.2s',
  },
  expandButton: {
    width: '100%',
    padding: '12px 0',
    fontSize: '16px',
    color: THEME_COLORS.text,
    backgroundColor: 'transparent',
    border: 'none',
    cursor: 'pointer',
    transition: 'color 0.2s',
  },

  // CHART CONTAINER - Maximum Real Estate
  chartContainer: {
    flex: 1,
    display: 'flex',
    flexDirection: 'column',
    position: 'relative',
    overflow: 'hidden',
    backgroundColor: THEME_COLORS.background,
  },
  chartWrapper: {
    flex: 1,
    overflow: 'hidden',
  },

  // COMPACT BOTTOM PANEL (120px fixed height)
  bottomPanel: {
    backgroundColor: THEME_COLORS.surface,
    borderTop: `1px solid ${THEME_COLORS.border}`,
    flexShrink: 0,
    maxHeight: '150px',
  },
  metricsToggle: {
    width: '100%',
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    padding: '8px 14px',
    backgroundColor: THEME_COLORS.surface,
    border: 'none',
    cursor: 'pointer',
    transition: 'background-color 0.2s',
  },
  metricsToggleText: {
    fontSize: '10px',
    fontWeight: 700,
    color: THEME_COLORS.textBright,
    letterSpacing: '0.6px',
  },
  metricsToggleIcon: {
    fontSize: '9px',
    color: THEME_COLORS.text,
  },
  metricsTableContainer: {
    height: '120px',
    overflowY: 'auto',
    overflowX: 'auto',
    padding: '8px 14px 14px 14px',
  },

  // ERROR BANNER
  errorBanner: {
    display: 'flex',
    alignItems: 'center',
    gap: '10px',
    padding: '10px 14px',
    backgroundColor: 'rgba(239, 83, 80, 0.12)',
    borderBottom: `1px solid ${THEME_COLORS.red}`,
    color: THEME_COLORS.red,
    fontSize: '11px',
  },
  errorIcon: {
    fontSize: '14px',
  },

  // EMPTY STATE
  emptyState: {
    display: 'flex',
    flexDirection: 'column',
    alignItems: 'center',
    justifyContent: 'center',
    height: '100%',
    gap: '14px',
  },
  emptyStateIcon: {
    fontSize: '56px',
    opacity: 0.25,
  },
  emptyStateText: {
    fontSize: '16px',
    fontWeight: 600,
    color: THEME_COLORS.textBright,
  },
  emptyStateHint: {
    fontSize: '12px',
    color: THEME_COLORS.text,
    maxWidth: '350px',
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
    backgroundColor: 'rgba(13, 17, 23, 0.88)',
    backdropFilter: 'blur(8px)',
    gap: '14px',
    zIndex: 1000,
  },
  spinner: {
    width: '36px',
    height: '36px',
    border: `3px solid ${THEME_COLORS.border}`,
    borderTop: `3px solid ${THEME_COLORS.blue}`,
    borderRadius: '50%',
    animation: 'spin 0.8s linear infinite',
  },
  loadingText: {
    fontSize: '12px',
    color: THEME_COLORS.text,
    fontWeight: 500,
  },
};
