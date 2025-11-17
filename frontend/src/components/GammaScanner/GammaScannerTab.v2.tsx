/**
 * Gamma Scanner Tab v2.0 - TradingView-Inspired Design
 * Professional, minimalist dark-theme with maximum data clarity
 */

import React, { useState, useEffect, useCallback } from 'react';
import { GammaChartCanvasV2 } from './GammaChartCanvas.v2';
import { GammaControlPanel } from './GammaControlPanel';
import { GammaDataParser } from './dataParser';
import {
  GammaScannerSettings,
  ParsedSymbolData,
  ParseError,
  GammaDataResponse,
  MarketRegime,
} from './types';
import axios from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

const DEFAULT_SETTINGS: GammaScannerSettings = {
  selectedSymbols: [],
  showSwingWalls: true,
  showLongWalls: true,
  showQuarterlyWalls: true,
  showGammaFlip: true,
  showSDBands: true,
  showLabels: true,
  showTable: true,
  wallOpacity: 0.8,
  colorScheme: 'default',
  dataSource: 'api',
  apiPollingInterval: 60,
  applyRegimeAdjustment: true,
  minStrength: 20,
  hideWeakWalls: false,
};

export const GammaScannerTabV2: React.FC = () => {
  const [settings, setSettings] = useState<GammaScannerSettings>(DEFAULT_SETTINGS);
  const [symbols, setSymbols] = useState<ParsedSymbolData[]>([]);
  const [errors, setErrors] = useState<ParseError[]>([]);
  const [rawData, setRawData] = useState<GammaDataResponse | null>(null);
  const [marketRegime, setMarketRegime] = useState<MarketRegime>({
    regime: 'Normal Volatility',
    vix: 15.5,
    bgColor: '#45B7D1',
    adjustmentEnabled: true,
  });
  const [loading, setLoading] = useState(false);
  const [lastUpdate, setLastUpdate] = useState<string>('');
  const [connectionStatus, setConnectionStatus] = useState<'connected' | 'disconnected' | 'error'>('disconnected');
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);

  const parser = new GammaDataParser();

  const fetchGammaData = useCallback(async () => {
    if (settings.dataSource !== 'api') return;

    setLoading(true);
    try {
      const response = await axios.get<GammaDataResponse>(`${API_BASE_URL}/api/gamma-data`, {
        timeout: 10000,
      });

      const data = response.data;
      setRawData(data);

      const parseResult = parser.parseGammaData(data);
      setSymbols(parseResult.symbols);
      setErrors(parseResult.errors);
      setLastUpdate(parseResult.metadata.lastUpdate);

      setMarketRegime({
        regime: parseResult.metadata.marketRegime,
        vix: parseResult.metadata.currentVix,
        bgColor: getRegimeColor(parseResult.metadata.marketRegime),
        adjustmentEnabled: parseResult.metadata.regimeAdjustmentEnabled,
      });

      setConnectionStatus('connected');
    } catch (error) {
      console.error('Failed to fetch gamma data:', error);
      setConnectionStatus('error');
    } finally {
      setLoading(false);
    }
  }, [settings.dataSource]);

  const handleManualPaste = useCallback((text: string) => {
    const parseResult = parser.parseManualInput(text);
    setSymbols(parseResult.symbols);
    setErrors(parseResult.errors);
    setLastUpdate(new Date().toLocaleString());
    setConnectionStatus('connected');
  }, []);

  useEffect(() => {
    if (settings.dataSource === 'api') {
      fetchGammaData();
      const interval = setInterval(() => {
        fetchGammaData();
      }, settings.apiPollingInterval * 1000);
      return () => clearInterval(interval);
    }
  }, [settings.dataSource, settings.apiPollingInterval, fetchGammaData]);

  const handleSettingsChange = useCallback((updates: Partial<GammaScannerSettings>) => {
    setSettings((prev) => ({ ...prev, ...updates }));
  }, []);

  return (
    <div style={styles.container}>
      {/* TradingView-Style Top Bar */}
      <div style={styles.topBar}>
        <div style={styles.topBarLeft}>
          <span style={styles.instrumentName}>GAMMA WALL SCANNER</span>
          <span style={styles.divider}>|</span>
          <span style={styles.metricLabel}>VIX</span>
          <span style={styles.metricValue}>{marketRegime.vix.toFixed(1)}</span>
          <span style={styles.divider}>|</span>
          <span style={styles.metricLabel}>Regime</span>
          <span style={{
            ...styles.regimeChip,
            backgroundColor: getRegimeColorDark(marketRegime.regime),
          }}>
            {marketRegime.regime}
          </span>
          <span style={styles.divider}>|</span>
          <span style={styles.metricLabel}>Updated</span>
          <span style={styles.metricValue}>{lastUpdate}</span>
        </div>
        <div style={styles.topBarRight}>
          <div style={styles.statusIndicator}>
            <span style={{
              ...styles.statusDot,
              backgroundColor: getStatusColor(connectionStatus),
            }} />
            <span style={styles.statusText}>
              {connectionStatus === 'connected' && 'Live'}
              {connectionStatus === 'disconnected' && 'Disconnected'}
              {connectionStatus === 'error' && 'Error'}
            </span>
          </div>
        </div>
      </div>

      {/* Main Workspace */}
      <div style={styles.workspace}>
        {/* Collapsible Sidebar */}
        <div style={{
          ...styles.sidebar,
          width: sidebarCollapsed ? '40px' : '280px',
        }}>
          <button
            onClick={() => setSidebarCollapsed(!sidebarCollapsed)}
            style={styles.collapseButton}
          >
            {sidebarCollapsed ? '▶' : '◀'}
          </button>
          {!sidebarCollapsed && (
            <GammaControlPanel
              settings={settings}
              onSettingsChange={handleSettingsChange}
              availableSymbols={symbols.map((s) => s.symbol)}
              onRefresh={fetchGammaData}
              loading={loading}
              onManualPaste={settings.dataSource === 'manual' ? handleManualPaste : undefined}
            />
          )}
        </div>

        {/* Main Chart Area */}
        <div style={styles.mainArea}>
          {symbols.length > 0 ? (
            <GammaChartCanvasV2
              symbols={symbols}
              settings={settings}
              marketRegime={marketRegime.regime}
            />
          ) : (
            <div style={styles.emptyState}>
              <div style={styles.emptyStateIcon}>📊</div>
              <div style={styles.emptyStateTitle}>No Data Available</div>
              <div style={styles.emptyStateText}>
                {settings.dataSource === 'api'
                  ? 'Waiting for data from API endpoint...'
                  : 'Open the control panel and paste level_data strings'}
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Error Toast */}
      {errors.length > 0 && (
        <div style={styles.errorToast}>
          <span style={styles.errorIcon}>⚠️</span>
          {errors.length} parse error(s) - Check debug console
        </div>
      )}
    </div>
  );
};

function getRegimeColor(regime: string): string {
  if (regime.includes('High Volatility')) return '#FF6B6B';
  if (regime.includes('Low Volatility')) return '#4ECDC4';
  return '#45B7D1';
}

function getRegimeColorDark(regime: string): string {
  if (regime.includes('High Volatility')) return 'rgba(255, 107, 107, 0.2)';
  if (regime.includes('Low Volatility')) return 'rgba(78, 205, 196, 0.2)';
  return 'rgba(69, 183, 209, 0.2)';
}

function getStatusColor(status: 'connected' | 'disconnected' | 'error'): string {
  switch (status) {
    case 'connected': return '#00C853';
    case 'disconnected': return '#666666';
    case 'error': return '#FF5252';
  }
}

const styles: Record<string, React.CSSProperties> = {
  container: {
    backgroundColor: '#131722',
    minHeight: '100vh',
    display: 'flex',
    flexDirection: 'column',
    fontFamily: '"Roboto", "Open Sans", "Arial", sans-serif',
    color: '#D1D4DC',
  },
  topBar: {
    backgroundColor: '#1E222D',
    height: '48px',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'space-between',
    padding: '0 16px',
    borderBottom: '1px solid #2A2E39',
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
  instrumentName: {
    fontSize: '14px',
    fontWeight: 600,
    color: '#FFFFFF',
    letterSpacing: '0.5px',
  },
  divider: {
    color: '#434651',
    fontSize: '12px',
  },
  metricLabel: {
    fontSize: '12px',
    color: '#787B86',
  },
  metricValue: {
    fontSize: '12px',
    color: '#D1D4DC',
    fontWeight: 500,
  },
  regimeChip: {
    fontSize: '11px',
    padding: '2px 8px',
    borderRadius: '3px',
    fontWeight: 500,
    color: '#FFFFFF',
  },
  statusIndicator: {
    display: 'flex',
    alignItems: 'center',
    gap: '6px',
  },
  statusDot: {
    width: '8px',
    height: '8px',
    borderRadius: '50%',
  },
  statusText: {
    fontSize: '12px',
    color: '#787B86',
  },
  workspace: {
    display: 'flex',
    flex: 1,
    overflow: 'hidden',
  },
  sidebar: {
    backgroundColor: '#1E222D',
    borderRight: '1px solid #2A2E39',
    transition: 'width 0.3s ease',
    overflow: 'hidden',
    position: 'relative',
  },
  collapseButton: {
    position: 'absolute',
    top: '8px',
    right: '8px',
    background: 'transparent',
    border: 'none',
    color: '#787B86',
    fontSize: '16px',
    cursor: 'pointer',
    padding: '4px',
    zIndex: 10,
  },
  mainArea: {
    flex: 1,
    backgroundColor: '#131722',
    overflow: 'auto',
  },
  emptyState: {
    display: 'flex',
    flexDirection: 'column',
    alignItems: 'center',
    justifyContent: 'center',
    height: '100%',
    padding: '40px',
  },
  emptyStateIcon: {
    fontSize: '64px',
    marginBottom: '16px',
    opacity: 0.3,
  },
  emptyStateTitle: {
    fontSize: '18px',
    fontWeight: 600,
    color: '#FFFFFF',
    marginBottom: '8px',
  },
  emptyStateText: {
    fontSize: '14px',
    color: '#787B86',
    textAlign: 'center',
  },
  errorToast: {
    position: 'fixed',
    bottom: '20px',
    right: '20px',
    backgroundColor: '#FF5252',
    color: '#FFFFFF',
    padding: '12px 20px',
    borderRadius: '4px',
    display: 'flex',
    alignItems: 'center',
    gap: '8px',
    fontSize: '14px',
    boxShadow: '0 4px 12px rgba(0,0,0,0.3)',
  },
  errorIcon: {
    fontSize: '18px',
  },
};
