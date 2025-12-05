/**
 * Gamma Settings Sidebar Component
 * User controls for visualization, data source, and filters
 */

import React from 'react';
import { GammaScannerSettings, ColorScheme } from './types';

interface GammaSettingsSidebarProps {
  settings: GammaScannerSettings;
  onSettingsChange: (settings: Partial<GammaScannerSettings>) => void;
  availableSymbols: string[];
}

export const GammaSettingsSidebar: React.FC<GammaSettingsSidebarProps> = ({
  settings,
  onSettingsChange,
  availableSymbols,
}) => {
  return (
    <div className="gamma-settings-sidebar" style={styles.container}>
      <h3 style={styles.heading}>Settings</h3>

      {/* Symbol Selection */}
      <div style={styles.section}>
        <h4 style={styles.subheading}>Symbols</h4>
        <select
          multiple
          value={settings.selectedSymbols}
          onChange={(e) => {
            const selected = Array.from(e.target.selectedOptions, option => option.value);
            onSettingsChange({ selectedSymbols: selected });
          }}
          style={styles.multiSelect}
        >
          {availableSymbols.map(symbol => (
            <option key={symbol} value={symbol}>{symbol}</option>
          ))}
        </select>
        <small style={styles.hint}>Hold Ctrl/Cmd to select multiple</small>
      </div>

      {/* Wall Display Toggles */}
      <div style={styles.section}>
        <h4 style={styles.subheading}>Wall Display</h4>
        {[
          { key: 'showSwingWalls', label: 'Swing Walls (14D)' },
          { key: 'showLongWalls', label: 'Long Walls (30D)' },
          { key: 'showQuarterlyWalls', label: 'Quarterly Walls (90D)' },
          { key: 'showGammaFlip', label: 'Gamma Flip Level' },
          { key: 'showSDBands', label: 'Standard Deviation Bands' },
        ].map(({ key, label }) => (
          <label key={key} style={styles.checkbox}>
            <input
              type="checkbox"
              checked={settings[key as keyof GammaScannerSettings] as boolean}
              onChange={(e) => onSettingsChange({ [key]: e.target.checked })}
            />
            {label}
          </label>
        ))}
      </div>

      {/* Visual Options */}
      <div style={styles.section}>
        <h4 style={styles.subheading}>Visual Options</h4>

        <label style={styles.checkbox}>
          <input
            type="checkbox"
            checked={settings.showLabels}
            onChange={(e) => onSettingsChange({ showLabels: e.target.checked })}
          />
          Show Labels
        </label>

        <label style={styles.checkbox}>
          <input
            type="checkbox"
            checked={settings.showTable}
            onChange={(e) => onSettingsChange({ showTable: e.target.checked })}
          />
          Show Table
        </label>

        <div style={styles.slider}>
          <label>Wall Opacity: {settings.wallOpacity.toFixed(2)}</label>
          <input
            type="range"
            min="0.1"
            max="1.0"
            step="0.1"
            value={settings.wallOpacity}
            onChange={(e) => onSettingsChange({ wallOpacity: parseFloat(e.target.value) })}
            style={{ width: '100%' }}
          />
        </div>

        <div style={styles.dropdown}>
          <label>Color Scheme:</label>
          <select
            value={settings.colorScheme}
            onChange={(e) => onSettingsChange({ colorScheme: e.target.value as ColorScheme })}
            style={styles.select}
          >
            <option value="default">Default</option>
            <option value="high-contrast">High Contrast</option>
            <option value="colorblind">Colorblind Friendly</option>
          </select>
        </div>
      </div>

      {/* Data Source */}
      <div style={styles.section}>
        <h4 style={styles.subheading}>Data Source</h4>

        <div style={styles.radioGroup}>
          <label style={styles.radio}>
            <input
              type="radio"
              checked={settings.dataSource === 'api'}
              onChange={() => onSettingsChange({ dataSource: 'api' })}
            />
            API Endpoint
          </label>
          <label style={styles.radio}>
            <input
              type="radio"
              checked={settings.dataSource === 'manual'}
              onChange={() => onSettingsChange({ dataSource: 'manual' })}
            />
            Manual Paste
          </label>
        </div>

        {settings.dataSource === 'api' && (
          <div style={styles.slider}>
            <label>Polling Interval: {settings.apiPollingInterval}s</label>
            <input
              type="range"
              min="10"
              max="300"
              step="10"
              value={settings.apiPollingInterval}
              onChange={(e) => onSettingsChange({ apiPollingInterval: parseInt(e.target.value) })}
              style={{ width: '100%' }}
            />
          </div>
        )}
      </div>

      {/* Regime Adjustment */}
      <div style={styles.section}>
        <h4 style={styles.subheading}>Regime Adjustment</h4>

        <label style={styles.checkbox}>
          <input
            type="checkbox"
            checked={settings.applyRegimeAdjustment}
            onChange={(e) => onSettingsChange({ applyRegimeAdjustment: e.target.checked })}
          />
          Apply Regime-Based Adjustment
        </label>
        <small style={styles.hint}>
          Boosts wall strength in high volatility regimes
        </small>
      </div>

      {/* Filters */}
      <div style={styles.section}>
        <h4 style={styles.subheading}>Filters</h4>

        <div style={styles.slider}>
          <label>Min Strength: {settings.minStrength}</label>
          <input
            type="range"
            min="0"
            max="100"
            step="5"
            value={settings.minStrength}
            onChange={(e) => onSettingsChange({ minStrength: parseInt(e.target.value) })}
            style={{ width: '100%' }}
          />
        </div>

        <label style={styles.checkbox}>
          <input
            type="checkbox"
            checked={settings.hideWeakWalls}
            onChange={(e) => onSettingsChange({ hideWeakWalls: e.target.checked })}
          />
          Hide Walls Below 40 Strength
        </label>
      </div>
    </div>
  );
};

const styles: Record<string, React.CSSProperties> = {
  container: {
    backgroundColor: '#1a1a1a',
    padding: '20px',
    borderRadius: '8px',
    color: '#CCCCCC',
    maxHeight: '800px',
    overflowY: 'auto',
    width: '300px',
  },
  heading: {
    fontSize: '20px',
    marginBottom: '20px',
    color: '#FFFFFF',
    borderBottom: '2px solid #333333',
    paddingBottom: '10px',
  },
  subheading: {
    fontSize: '14px',
    marginBottom: '10px',
    color: '#FFFFFF',
    fontWeight: 'bold',
  },
  section: {
    marginBottom: '20px',
    paddingBottom: '15px',
    borderBottom: '1px solid #333333',
  },
  multiSelect: {
    width: '100%',
    minHeight: '100px',
    backgroundColor: '#2a2a2a',
    color: '#CCCCCC',
    border: '1px solid #444444',
    borderRadius: '4px',
    padding: '5px',
  },
  checkbox: {
    display: 'block',
    marginBottom: '8px',
    cursor: 'pointer',
  },
  radio: {
    display: 'block',
    marginBottom: '8px',
    cursor: 'pointer',
  },
  radioGroup: {
    marginBottom: '10px',
  },
  slider: {
    marginTop: '10px',
  },
  dropdown: {
    marginTop: '10px',
  },
  select: {
    width: '100%',
    backgroundColor: '#2a2a2a',
    color: '#CCCCCC',
    border: '1px solid #444444',
    borderRadius: '4px',
    padding: '8px',
    marginTop: '5px',
  },
  hint: {
    display: 'block',
    marginTop: '5px',
    fontSize: '11px',
    color: '#888888',
    fontStyle: 'italic',
  },
};
