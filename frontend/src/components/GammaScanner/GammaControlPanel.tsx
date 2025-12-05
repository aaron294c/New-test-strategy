/**
 * Gamma Control Panel - TradingView-Inspired Sidebar
 * Clean, minimal controls with toggle switches
 */

import React, { useState } from 'react';
import { GammaScannerSettings } from './types';

interface GammaControlPanelProps {
  settings: GammaScannerSettings;
  onSettingsChange: (settings: Partial<GammaScannerSettings>) => void;
  availableSymbols: string[];
  onRefresh: () => void;
  loading: boolean;
  onManualPaste?: (text: string) => void;
}

export const GammaControlPanel: React.FC<GammaControlPanelProps> = ({
  settings,
  onSettingsChange,
  availableSymbols,
  onRefresh,
  loading,
  onManualPaste,
}) => {
  const [manualInput, setManualInput] = useState('');
  const [showManualInput, setShowManualInput] = useState(false);

  const handleManualSubmit = () => {
    if (onManualPaste && manualInput.trim()) {
      onManualPaste(manualInput);
      setManualInput('');
      setShowManualInput(false);
    }
  };

  return (
    <div style={styles.container}>
      {/* Header */}
      <div style={styles.header}>
        <div style={styles.headerTitle}>Controls</div>
        <button onClick={onRefresh} disabled={loading} style={styles.refreshButton}>
          {loading ? '⟳' : '↻'}
        </button>
      </div>

      {/* Symbol Selection */}
      <div style={styles.section}>
        <div style={styles.sectionTitle}>Symbols</div>
        <select
          multiple
          value={settings.selectedSymbols}
          onChange={(e) => {
            const selected = Array.from(e.target.selectedOptions, (o) => o.value);
            onSettingsChange({ selectedSymbols: selected });
          }}
          style={styles.multiSelect}
        >
          <option value="">All Symbols</option>
          {availableSymbols.map((symbol) => (
            <option key={symbol} value={symbol}>
              {symbol}
            </option>
          ))}
        </select>
        <div style={styles.hint}>Ctrl+Click to select multiple</div>
      </div>

      {/* Wall Display */}
      <div style={styles.section}>
        <div style={styles.sectionTitle}>Gamma Walls</div>
        <ToggleSwitch
          label="Swing Walls (14D)"
          checked={settings.showSwingWalls}
          onChange={(checked) => onSettingsChange({ showSwingWalls: checked })}
        />
        <ToggleSwitch
          label="Long Walls (30D)"
          checked={settings.showLongWalls}
          onChange={(checked) => onSettingsChange({ showLongWalls: checked })}
        />
        <ToggleSwitch
          label="Quarterly Walls (90D)"
          checked={settings.showQuarterlyWalls}
          onChange={(checked) => onSettingsChange({ showQuarterlyWalls: checked })}
        />
      </div>

      {/* Key Levels */}
      <div style={styles.section}>
        <div style={styles.sectionTitle}>Key Levels</div>
        <ToggleSwitch
          label="Gamma Flip Level"
          checked={settings.showGammaFlip}
          onChange={(checked) => onSettingsChange({ showGammaFlip: checked })}
        />
        <ToggleSwitch
          label="Standard Deviation Bands"
          checked={settings.showSDBands}
          onChange={(checked) => onSettingsChange({ showSDBands: checked })}
        />
      </div>

      {/* Display Options */}
      <div style={styles.section}>
        <div style={styles.sectionTitle}>Display</div>
        <ToggleSwitch
          label="Symbol Metrics Table"
          checked={settings.showTable}
          onChange={(checked) => onSettingsChange({ showTable: checked })}
        />
        <ToggleSwitch
          label="Wall Labels"
          checked={settings.showLabels}
          onChange={(checked) => onSettingsChange({ showLabels: checked })}
        />
      </div>

      {/* Wall Strength */}
      <div style={styles.section}>
        <div style={styles.sectionTitle}>Wall Strength</div>
        <SliderControl
          label="Opacity"
          value={settings.wallOpacity}
          min={0.1}
          max={1.0}
          step={0.1}
          onChange={(value) => onSettingsChange({ wallOpacity: value })}
        />
        <SliderControl
          label="Min Strength"
          value={settings.minStrength}
          min={0}
          max={100}
          step={5}
          onChange={(value) => onSettingsChange({ minStrength: value })}
        />
        <ToggleSwitch
          label="Hide Weak Walls (< 40)"
          checked={settings.hideWeakWalls}
          onChange={(checked) => onSettingsChange({ hideWeakWalls: checked })}
        />
      </div>

      {/* Market Regime */}
      <div style={styles.section}>
        <div style={styles.sectionTitle}>Market Regime</div>
        <ToggleSwitch
          label="Regime Adjustment"
          checked={settings.applyRegimeAdjustment}
          onChange={(checked) => onSettingsChange({ applyRegimeAdjustment: checked })}
        />
        <div style={styles.hint}>Boosts walls in high volatility</div>
      </div>

      {/* Data Source */}
      <div style={styles.section}>
        <div style={styles.sectionTitle}>Data Source</div>
        <div style={styles.radioGroup}>
          <RadioButton
            label="API Endpoint"
            checked={settings.dataSource === 'api'}
            onChange={() => onSettingsChange({ dataSource: 'api' })}
          />
          <RadioButton
            label="Manual Paste"
            checked={settings.dataSource === 'manual'}
            onChange={() => {
              onSettingsChange({ dataSource: 'manual' });
              setShowManualInput(true);
            }}
          />
        </div>
        {settings.dataSource === 'api' && (
          <SliderControl
            label="Polling Interval (s)"
            value={settings.apiPollingInterval}
            min={10}
            max={300}
            step={10}
            onChange={(value) => onSettingsChange({ apiPollingInterval: value })}
          />
        )}
      </div>

      {/* Manual Input */}
      {showManualInput && onManualPaste && (
        <div style={styles.section}>
          <div style={styles.sectionTitle}>Paste Data</div>
          <textarea
            value={manualInput}
            onChange={(e) => setManualInput(e.target.value)}
            placeholder="Paste level_data strings here..."
            style={styles.textarea}
          />
          <button onClick={handleManualSubmit} style={styles.submitButton}>
            Parse Data
          </button>
        </div>
      )}
    </div>
  );
};

// Toggle Switch Component
const ToggleSwitch: React.FC<{
  label: string;
  checked: boolean;
  onChange: (checked: boolean) => void;
}> = ({ label, checked, onChange }) => (
  <div style={toggleStyles.container} onClick={() => onChange(!checked)}>
    <div style={toggleStyles.label}>{label}</div>
    <div style={{ ...toggleStyles.switch, backgroundColor: checked ? '#2962FF' : '#434651' }}>
      <div
        style={{
          ...toggleStyles.slider,
          transform: checked ? 'translateX(18px)' : 'translateX(2px)',
        }}
      />
    </div>
  </div>
);

// Slider Control Component
const SliderControl: React.FC<{
  label: string;
  value: number;
  min: number;
  max: number;
  step: number;
  onChange: (value: number) => void;
}> = ({ label, value, min, max, step, onChange }) => (
  <div style={sliderStyles.container}>
    <div style={sliderStyles.label}>
      {label}: <span style={sliderStyles.value}>{value}</span>
    </div>
    <input
      type="range"
      min={min}
      max={max}
      step={step}
      value={value}
      onChange={(e) => onChange(parseFloat(e.target.value))}
      style={sliderStyles.slider}
    />
  </div>
);

// Radio Button Component
const RadioButton: React.FC<{
  label: string;
  checked: boolean;
  onChange: () => void;
}> = ({ label, checked, onChange }) => (
  <div style={radioStyles.container} onClick={onChange}>
    <div style={{ ...radioStyles.radio, borderColor: checked ? '#2962FF' : '#434651' }}>
      {checked && <div style={radioStyles.radioInner} />}
    </div>
    <div style={radioStyles.label}>{label}</div>
  </div>
);

const styles: Record<string, React.CSSProperties> = {
  container: {
    height: '100%',
    overflowY: 'auto',
    padding: '16px',
  },
  header: {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: '20px',
  },
  headerTitle: {
    fontSize: '16px',
    fontWeight: 600,
    color: '#FFFFFF',
  },
  refreshButton: {
    background: 'transparent',
    border: '1px solid #434651',
    color: '#D1D4DC',
    padding: '6px 12px',
    borderRadius: '4px',
    cursor: 'pointer',
    fontSize: '16px',
    transition: 'all 0.2s',
  },
  section: {
    marginBottom: '20px',
    paddingBottom: '16px',
    borderBottom: '1px solid #2A2E39',
  },
  sectionTitle: {
    fontSize: '12px',
    fontWeight: 600,
    color: '#787B86',
    textTransform: 'uppercase',
    letterSpacing: '0.5px',
    marginBottom: '12px',
  },
  multiSelect: {
    width: '100%',
    minHeight: '100px',
    backgroundColor: '#131722',
    color: '#D1D4DC',
    border: '1px solid #2A2E39',
    borderRadius: '4px',
    padding: '8px',
    fontSize: '13px',
  },
  hint: {
    fontSize: '11px',
    color: '#787B86',
    marginTop: '6px',
  },
  radioGroup: {
    display: 'flex',
    flexDirection: 'column',
    gap: '8px',
  },
  textarea: {
    width: '100%',
    minHeight: '120px',
    backgroundColor: '#131722',
    color: '#D1D4DC',
    border: '1px solid #2A2E39',
    borderRadius: '4px',
    padding: '8px',
    fontSize: '12px',
    fontFamily: 'monospace',
    resize: 'vertical',
  },
  submitButton: {
    width: '100%',
    marginTop: '8px',
    backgroundColor: '#2962FF',
    color: '#FFFFFF',
    border: 'none',
    padding: '10px',
    borderRadius: '4px',
    cursor: 'pointer',
    fontSize: '13px',
    fontWeight: 500,
    transition: 'background-color 0.2s',
  },
};

const toggleStyles: Record<string, React.CSSProperties> = {
  container: {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    padding: '8px 0',
    cursor: 'pointer',
    userSelect: 'none',
  },
  label: {
    fontSize: '13px',
    color: '#D1D4DC',
  },
  switch: {
    width: '40px',
    height: '20px',
    borderRadius: '10px',
    position: 'relative',
    transition: 'background-color 0.3s',
  },
  slider: {
    width: '16px',
    height: '16px',
    borderRadius: '50%',
    backgroundColor: '#FFFFFF',
    position: 'absolute',
    top: '2px',
    transition: 'transform 0.3s',
  },
};

const sliderStyles: Record<string, React.CSSProperties> = {
  container: {
    marginBottom: '12px',
  },
  label: {
    fontSize: '13px',
    color: '#D1D4DC',
    marginBottom: '6px',
    display: 'flex',
    justifyContent: 'space-between',
  },
  value: {
    color: '#2962FF',
    fontWeight: 500,
  },
  slider: {
    width: '100%',
    height: '4px',
    borderRadius: '2px',
    outline: 'none',
    WebkitAppearance: 'none',
    backgroundColor: '#2A2E39',
  },
};

const radioStyles: Record<string, React.CSSProperties> = {
  container: {
    display: 'flex',
    alignItems: 'center',
    gap: '8px',
    padding: '6px 0',
    cursor: 'pointer',
    userSelect: 'none',
  },
  radio: {
    width: '16px',
    height: '16px',
    borderRadius: '50%',
    border: '2px solid',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    transition: 'border-color 0.2s',
  },
  radioInner: {
    width: '8px',
    height: '8px',
    borderRadius: '50%',
    backgroundColor: '#2962FF',
  },
  label: {
    fontSize: '13px',
    color: '#D1D4DC',
  },
};
