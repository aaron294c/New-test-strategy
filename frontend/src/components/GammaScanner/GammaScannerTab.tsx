/**
 * Gamma Scanner Tab - Main Integration Component
 * Coordinates all sub-components and manages state
 */

import React, { useState, useEffect, useCallback } from 'react';
import { GammaChartCanvas } from './GammaChartCanvas';
import { GammaSettingsSidebar } from './GammaSettingsSidebar';
import { GammaSymbolTable } from './GammaSymbolTable';
import { GammaDebugConsole } from './GammaDebugConsole';
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

// Default settings
const DEFAULT_SETTINGS: GammaScannerSettings = {
  selectedSymbols: [],
  showSwingWalls: true,
  showLongWalls: true,
  showQuarterlyWalls: true,
  showGammaFlip: true,
  showSDBands: true,
  showLabels: true,
  showTable: true,
  wallOpacity: 0.7,
  colorScheme: 'default',
  dataSource: 'api',
  apiPollingInterval: 60,
  applyRegimeAdjustment: true,
  minStrength: 20,
  hideWeakWalls: false,
};

export const GammaScannerTab: React.FC = () => {
  // State
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

  const parser = new GammaDataParser();

  // Fetch data from API
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
      setErrors([
        {
          line: 0,
          symbol: 'API',
          message: `Failed to fetch data: ${error instanceof Error ? error.message : 'Unknown error'}`,
        },
      ]);
    } finally {
      setLoading(false);
    }
  }, [settings.dataSource]);

  // Parse manual input
  const handleManualPaste = useCallback((text: string) => {
    const parseResult = parser.parseManualInput(text);
    setSymbols(parseResult.symbols);
    setErrors(parseResult.errors);
    setLastUpdate(new Date().toLocaleString());
    setConnectionStatus('connected');
  }, []);

  // Polling effect for API data source
  useEffect(() => {
    if (settings.dataSource === 'api') {
      fetchGammaData(); // Initial fetch

      const interval = setInterval(() => {
        fetchGammaData();
      }, settings.apiPollingInterval * 1000);

      return () => clearInterval(interval);
    }
  }, [settings.dataSource, settings.apiPollingInterval, fetchGammaData]);

  // Settings update handler
  const handleSettingsChange = useCallback((updates: Partial<GammaScannerSettings>) => {
    setSettings((prev) => ({ ...prev, ...updates }));
  }, []);

  // Manual refresh handler
  const handleRefresh = () => {
    if (settings.dataSource === 'api') {
      fetchGammaData();
    }
  };

  // Get unique symbol list for selector
  const availableSymbols = symbols.map((s) => s.symbol);

  return (
    <div className="gamma-scanner-tab" style={styles.container}>
      {/* Header */}
      <div style={styles.header}>
        <div style={styles.headerLeft}>
          <h1 style={styles.title}>Gamma Wall Scanner</h1>
          <div style={styles.statusBar}>
            <span style={{ ...styles.statusDot, backgroundColor: getStatusColor(connectionStatus) }} />
            <span style={styles.statusText}>
              {connectionStatus === 'connected' && `Connected • Last update: ${lastUpdate}`}
              {connectionStatus === 'disconnected' && 'Disconnected'}
              {connectionStatus === 'error' && 'Connection Error'}
            </span>
          </div>
        </div>

        <div style={styles.headerRight}>
          <div style={styles.regimeIndicator}>
            <div style={styles.regimeLabel}>Market Regime</div>
            <div style={{ ...styles.regimeBadge, backgroundColor: marketRegime.bgColor }}>
              {marketRegime.regime}
            </div>
            <div style={styles.vixLabel}>VIX: {marketRegime.vix.toFixed(1)}</div>
          </div>
          <button onClick={handleRefresh} style={styles.refreshButton} disabled={loading}>
            {loading ? 'Loading...' : '↻ Refresh'}
          </button>
        </div>
      </div>

      {/* Main Content */}
      <div style={styles.mainContent}>
        {/* Sidebar */}
        <div style={styles.sidebar}>
          <GammaSettingsSidebar
            settings={settings}
            onSettingsChange={handleSettingsChange}
            availableSymbols={availableSymbols}
          />
        </div>

        {/* Chart Area */}
        <div style={styles.chartArea}>
          {symbols.length > 0 ? (
            <>
              <GammaChartCanvas
                symbols={symbols}
                settings={settings}
                marketRegime={marketRegime.regime}
              />
              {settings.showTable && <GammaSymbolTable symbols={symbols} />}
            </>
          ) : (
            <div style={styles.emptyState}>
              <h2>No Data Available</h2>
              <p>
                {settings.dataSource === 'api'
                  ? 'Waiting for data from API endpoint...'
                  : 'Paste level_data strings in the debug console below'}
              </p>
            </div>
          )}
        </div>
      </div>

      {/* Debug Console */}
      <GammaDebugConsole
        errors={errors}
        rawData={rawData}
        onManualPaste={settings.dataSource === 'manual' ? handleManualPaste : undefined}
      />
    </div>
  );
};

// Helper functions
function getRegimeColor(regime: string): string {
  if (regime.includes('High Volatility')) return '#FF6B6B';
  if (regime.includes('Low Volatility')) return '#4ECDC4';
  return '#45B7D1';
}

function getStatusColor(status: 'connected' | 'disconnected' | 'error'): string {
  switch (status) {
    case 'connected':
      return '#44FF44';
    case 'disconnected':
      return '#888888';
    case 'error':
      return '#FF4444';
  }
}

const styles: Record<string, React.CSSProperties> = {
  container: {
    backgroundColor: '#0d0d0d',
    minHeight: '100vh',
    padding: '20px',
    color: '#CCCCCC',
  },
  header: {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: '20px',
    paddingBottom: '15px',
    borderBottom: '2px solid #333333',
  },
  headerLeft: {
    display: 'flex',
    flexDirection: 'column',
    gap: '10px',
  },
  title: {
    fontSize: '32px',
    margin: 0,
    color: '#FFFFFF',
    fontWeight: 'bold',
  },
  statusBar: {
    display: 'flex',
    alignItems: 'center',
    gap: '8px',
  },
  statusDot: {
    width: '10px',
    height: '10px',
    borderRadius: '50%',
  },
  statusText: {
    fontSize: '14px',
    color: '#CCCCCC',
  },
  headerRight: {
    display: 'flex',
    alignItems: 'center',
    gap: '20px',
  },
  regimeIndicator: {
    display: 'flex',
    flexDirection: 'column',
    alignItems: 'flex-end',
    gap: '5px',
  },
  regimeLabel: {
    fontSize: '12px',
    color: '#888888',
  },
  regimeBadge: {
    padding: '8px 16px',
    borderRadius: '20px',
    fontSize: '14px',
    fontWeight: 'bold',
    color: '#FFFFFF',
  },
  vixLabel: {
    fontSize: '12px',
    color: '#CCCCCC',
  },
  refreshButton: {
    backgroundColor: '#4488FF',
    color: '#FFFFFF',
    border: 'none',
    padding: '12px 24px',
    borderRadius: '6px',
    fontSize: '14px',
    fontWeight: 'bold',
    cursor: 'pointer',
    transition: 'background-color 0.2s',
  },
  mainContent: {
    display: 'flex',
    gap: '20px',
    marginBottom: '20px',
  },
  sidebar: {
    flexShrink: 0,
  },
  chartArea: {
    flex: 1,
    minWidth: 0,
  },
  emptyState: {
    textAlign: 'center',
    padding: '100px 20px',
    backgroundColor: '#1a1a1a',
    borderRadius: '8px',
  },
};
