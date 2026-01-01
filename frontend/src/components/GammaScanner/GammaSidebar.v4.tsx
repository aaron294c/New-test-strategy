/**
 * Gamma Sidebar v4.0 - Compact TradingView-Style Control Panel
 * Preset buttons, collapsible sections, professional styling
 */

import React, { useState } from 'react';
import { GammaScannerSettings } from './types';
import { THEME_COLORS } from './colors';

interface GammaSidebarV4Props {
  settings: GammaScannerSettings;
  onSettingsChange: (updates: Partial<GammaScannerSettings>) => void;
  symbols: string[];
  onRefresh: () => void;
  loading: boolean;
  onManualPaste?: (text: string) => void;
}

type Preset = 'dayTrader' | 'swingTrader' | 'optionsSeller' | 'custom';

export const GammaSidebarV4: React.FC<GammaSidebarV4Props> = ({
  settings,
  onSettingsChange,
  symbols,
  onRefresh,
  loading,
  onManualPaste,
}) => {
  const [activePreset, setActivePreset] = useState<Preset>('custom');
  const [visualExpanded, setVisualExpanded] = useState(false);
  const [advancedExpanded, setAdvancedExpanded] = useState(false);
  const [manualInputVisible, setManualInputVisible] = useState(false);
  const [manualText, setManualText] = useState('');

  const applyPreset = (preset: Preset) => {
    setActivePreset(preset);

    const presets: Record<Preset, Partial<GammaScannerSettings>> = {
      dayTrader: {
        showSwingWalls: true,
        showLongWalls: false,
        showQuarterlyWalls: false,
        minStrength: 50,
        hideWeakWalls: true,
        wallOpacity: 0.9,
        showGammaFlip: true,
        showSDBands: false,
      },
      swingTrader: {
        showSwingWalls: true,
        showLongWalls: true,
        showQuarterlyWalls: false,
        minStrength: 30,
        hideWeakWalls: false,
        wallOpacity: 0.8,
        showGammaFlip: true,
        showSDBands: true,
      },
      optionsSeller: {
        showSwingWalls: true,
        showLongWalls: true,
        showQuarterlyWalls: true,
        minStrength: 20,
        hideWeakWalls: false,
        wallOpacity: 0.7,
        showGammaFlip: true,
        showSDBands: true,
      },
      custom: {}, // No changes
    };

    if (preset !== 'custom') {
      onSettingsChange(presets[preset]);
    }
  };

  const handleManualSubmit = () => {
    if (onManualPaste && manualText.trim()) {
      onManualPaste(manualText);
      setManualText('');
      setManualInputVisible(false);
    }
  };

  return (
    <div style={styles.container}>
      {/* HEADER */}
      <div style={styles.header}>
        <div style={styles.headerTitle}>CONTROLS</div>
        <button onClick={onRefresh} disabled={loading} style={styles.refreshButton}>
          {loading ? '⟳' : '↻'}
        </button>
      </div>

      {/* QUICK PRESETS */}
      <div style={styles.section}>
        <div style={styles.sectionHeader}>
          <span style={styles.sectionIcon}>⚡</span>
          <span>QUICK PRESETS</span>
        </div>

        <button
          onClick={() => applyPreset('dayTrader')}
          style={{
            ...styles.presetButton,
            ...(activePreset === 'dayTrader' ? styles.presetButtonActive : {}),
          }}
        >
          <div style={styles.presetTitle}>Day Trader</div>
          <div style={styles.presetDesc}>14D walls only, high strength</div>
        </button>

        <button
          onClick={() => applyPreset('swingTrader')}
          style={{
            ...styles.presetButton,
            ...(activePreset === 'swingTrader' ? styles.presetButtonActive : {}),
          }}
        >
          <div style={styles.presetTitle}>Swing Trader</div>
          <div style={styles.presetDesc}>14D + 30D walls, balanced</div>
        </button>

        <button
          onClick={() => applyPreset('optionsSeller')}
          style={{
            ...styles.presetButton,
            ...(activePreset === 'optionsSeller' ? styles.presetButtonActive : {}),
          }}
        >
          <div style={styles.presetTitle}>Options Seller</div>
          <div style={styles.presetDesc}>All timeframes, max pain focus</div>
        </button>
      </div>

      {/* WALL DISPLAY */}
      <div style={styles.section}>
        <div style={styles.sectionHeader}>
          <span style={styles.sectionIcon}>📊</span>
          <span>WALL DISPLAY</span>
        </div>

        <ToggleSwitch
          label="14D Swing Walls"
          checked={settings.showSwingWalls}
          onChange={(checked) => {
            onSettingsChange({ showSwingWalls: checked });
            setActivePreset('custom');
          }}
          icon="⚡"
        />
        <ToggleSwitch
          label="30D Long-term Walls"
          checked={settings.showLongWalls}
          onChange={(checked) => {
            onSettingsChange({ showLongWalls: checked });
            setActivePreset('custom');
          }}
          icon="📈"
        />
        <ToggleSwitch
          label="90D Quarterly Walls"
          checked={settings.showQuarterlyWalls}
          onChange={(checked) => {
            onSettingsChange({ showQuarterlyWalls: checked });
            setActivePreset('custom');
          }}
          icon="📅"
        />
      </div>

      {/* KEY LEVELS */}
      <div style={styles.section}>
        <div style={styles.sectionHeader}>
          <span style={styles.sectionIcon}>🎯</span>
          <span>KEY LEVELS</span>
        </div>

        <ToggleSwitch
          label="Gamma Flip Level"
          checked={settings.showGammaFlip}
          onChange={(checked) => onSettingsChange({ showGammaFlip: checked })}
          icon="🔄"
        />
        <ToggleSwitch
          label="SD Bands (±1σ, ±2σ)"
          checked={settings.showSDBands}
          onChange={(checked) => onSettingsChange({ showSDBands: checked })}
          icon="📏"
        />
        <ToggleSwitch
          label="Strike Labels"
          checked={settings.showLabels}
          onChange={(checked) => onSettingsChange({ showLabels: checked })}
          icon="🏷️"
        />
      </div>

      {/* VISUAL SETTINGS (Collapsible) */}
      <div style={styles.section}>
        <div
          style={styles.sectionHeaderCollapsible}
          onClick={() => setVisualExpanded(!visualExpanded)}
        >
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <span style={styles.sectionIcon}>🎨</span>
            <span>VISUAL</span>
          </div>
          <span style={styles.expandIcon}>{visualExpanded ? '▼' : '▸'}</span>
        </div>

        {visualExpanded && (
          <div style={styles.collapsibleContent}>
            <SliderControl
              label="Wall Opacity"
              value={settings.wallOpacity}
              min={0}
              max={1}
              step={0.1}
              onChange={(value) => onSettingsChange({ wallOpacity: value })}
            />
            <SliderControl
              label="Min Strength"
              value={settings.minStrength}
              min={0}
              max={100}
              step={10}
              onChange={(value) => onSettingsChange({ minStrength: value })}
            />
            <ToggleSwitch
              label="Hide Weak Walls (<40)"
              checked={settings.hideWeakWalls}
              onChange={(checked) => onSettingsChange({ hideWeakWalls: checked })}
              icon="👁️"
            />
          </div>
        )}
      </div>

      {/* ADVANCED (Collapsible) */}
      <div style={styles.section}>
        <div
          style={styles.sectionHeaderCollapsible}
          onClick={() => setAdvancedExpanded(!advancedExpanded)}
        >
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <span style={styles.sectionIcon}>⚙️</span>
            <span>ADVANCED</span>
          </div>
          <span style={styles.expandIcon}>{advancedExpanded ? '▼' : '▸'}</span>
        </div>

        {advancedExpanded && (
          <div style={styles.collapsibleContent}>
            <ToggleSwitch
              label="Regime Adjustment"
              checked={settings.applyRegimeAdjustment}
              onChange={(checked) => onSettingsChange({ applyRegimeAdjustment: checked })}
              icon="📊"
            />

            <div style={styles.dataSourceSection}>
              <div style={styles.label}>Data Source</div>
              <select
                value={settings.dataSource}
                onChange={(e) => onSettingsChange({ dataSource: e.target.value as any })}
                style={styles.select}
              >
                <option value="api">Live API</option>
                <option value="manual">Manual Paste</option>
              </select>

              {settings.dataSource === 'manual' && (
                <>
                  <button
                    onClick={() => setManualInputVisible(!manualInputVisible)}
                    style={styles.manualButton}
                  >
                    {manualInputVisible ? 'Cancel' : 'Paste Data'}
                  </button>

                  {manualInputVisible && (
                    <div style={styles.manualInputContainer}>
                      <textarea
                        value={manualText}
                        onChange={(e) => setManualText(e.target.value)}
                        placeholder="Paste level_data strings..."
                        style={styles.textarea}
                        rows={6}
                      />
                      <button onClick={handleManualSubmit} style={styles.submitButton}>
                        Submit
                      </button>
                    </div>
                  )}
                </>
              )}
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

// Toggle Switch Component
interface ToggleSwitchProps {
  label: string;
  checked: boolean;
  onChange: (checked: boolean) => void;
  icon?: string;
}

const ToggleSwitch: React.FC<ToggleSwitchProps> = ({ label, checked, onChange, icon }) => (
  <div style={styles.toggleContainer} onClick={() => onChange(!checked)}>
    <div style={styles.toggleLabel}>
      {icon && <span style={styles.toggleIcon}>{icon}</span>}
      {label}
    </div>
    <div style={{ ...styles.toggleTrack, backgroundColor: checked ? THEME_COLORS.blue : THEME_COLORS.border }}>
      <div style={{ ...styles.toggleThumb, transform: checked ? 'translateX(18px)' : 'translateX(2px)' }} />
    </div>
  </div>
);

// Slider Control Component
interface SliderControlProps {
  label: string;
  value: number;
  min: number;
  max: number;
  step: number;
  onChange: (value: number) => void;
}

const SliderControl: React.FC<SliderControlProps> = ({ label, value, min, max, step, onChange }) => (
  <div style={styles.sliderContainer}>
    <div style={styles.sliderHeader}>
      <span style={styles.sliderLabel}>{label}</span>
      <span style={styles.sliderValue}>{value}</span>
    </div>
    <input
      type="range"
      min={min}
      max={max}
      step={step}
      value={value}
      onChange={(e) => onChange(parseFloat(e.target.value))}
      style={styles.slider}
    />
  </div>
);

const styles: Record<string, React.CSSProperties> = {
  container: {
    height: '100%',
    overflowY: 'auto',
    overflowX: 'hidden',
    backgroundColor: THEME_COLORS.surface,
  },

  // Header
  header: {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    padding: '10px 14px',
    borderBottom: `1px solid ${THEME_COLORS.border}`,
    position: 'sticky',
    top: 0,
    backgroundColor: THEME_COLORS.surface,
    zIndex: 10,
  },
  headerTitle: {
    fontSize: '11px',
    fontWeight: 700,
    letterSpacing: '0.8px',
    color: THEME_COLORS.textBright,
  },
  refreshButton: {
    padding: '6px 10px',
    fontSize: '14px',
    color: THEME_COLORS.text,
    backgroundColor: 'transparent',
    border: `1px solid ${THEME_COLORS.border}`,
    borderRadius: '4px',
    cursor: 'pointer',
    transition: 'all 0.2s',
  },

  // Section
  section: {
    padding: '12px 14px',
    borderBottom: `1px solid ${THEME_COLORS.border}`,
  },
  sectionHeader: {
    display: 'flex',
    alignItems: 'center',
    gap: '8px',
    fontSize: '10px',
    fontWeight: 700,
    letterSpacing: '0.8px',
    textTransform: 'uppercase' as const,
    color: THEME_COLORS.text,
    marginBottom: '12px',
  },
  sectionHeaderCollapsible: {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    fontSize: '10px',
    fontWeight: 700,
    letterSpacing: '0.8px',
    textTransform: 'uppercase' as const,
    color: THEME_COLORS.text,
    marginBottom: '8px',
    cursor: 'pointer',
    userSelect: 'none' as const,
    padding: '6px 0',
    borderRadius: '4px',
  },
  sectionIcon: {
    fontSize: '12px',
  },
  expandIcon: {
    fontSize: '10px',
    color: THEME_COLORS.text,
  },
  collapsibleContent: {
    marginTop: '8px',
  },

  // Preset Buttons
  presetButton: {
    width: '100%',
    padding: '10px 12px',
    marginBottom: '8px',
    background: `linear-gradient(135deg, ${THEME_COLORS.surface} 0%, ${THEME_COLORS.surfaceElevated} 100%)`,
    border: `1px solid ${THEME_COLORS.border}`,
    borderRadius: '6px',
    textAlign: 'left' as const,
    cursor: 'pointer',
    transition: 'all 0.2s',
    position: 'relative' as const,
  },
  presetButtonActive: {
    background: `linear-gradient(135deg, #1E3A8A 0%, ${THEME_COLORS.blue} 100%)`,
    borderColor: THEME_COLORS.blue,
    boxShadow: `0 0 12px rgba(41, 98, 255, 0.4)`,
  },
  presetTitle: {
    fontSize: '11px',
    fontWeight: 600,
    color: THEME_COLORS.textBright,
    marginBottom: '4px',
  },
  presetDesc: {
    fontSize: '9px',
    color: THEME_COLORS.text,
    lineHeight: '1.3',
  },

  // Toggle Switch
  toggleContainer: {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    padding: '8px 0',
    cursor: 'pointer',
    userSelect: 'none' as const,
  },
  toggleLabel: {
    fontSize: '11px',
    color: THEME_COLORS.textBright,
    display: 'flex',
    alignItems: 'center',
    gap: '6px',
  },
  toggleIcon: {
    fontSize: '13px',
  },
  toggleTrack: {
    width: '38px',
    height: '20px',
    borderRadius: '10px',
    position: 'relative' as const,
    transition: 'background-color 0.2s',
  },
  toggleThumb: {
    position: 'absolute' as const,
    top: '2px',
    width: '16px',
    height: '16px',
    borderRadius: '50%',
    backgroundColor: '#FFFFFF',
    boxShadow: '0 2px 4px rgba(0, 0, 0, 0.3)',
    transition: 'transform 0.2s',
  },

  // Slider
  sliderContainer: {
    padding: '8px 0',
  },
  sliderHeader: {
    display: 'flex',
    justifyContent: 'space-between',
    marginBottom: '6px',
  },
  sliderLabel: {
    fontSize: '11px',
    color: THEME_COLORS.textBright,
  },
  sliderValue: {
    fontSize: '11px',
    fontWeight: 600,
    color: THEME_COLORS.blue,
  },
  slider: {
    width: '100%',
    height: '4px',
    borderRadius: '2px',
    outline: 'none',
    backgroundColor: THEME_COLORS.border,
  },

  // Data Source
  dataSourceSection: {
    marginTop: '12px',
  },
  label: {
    fontSize: '11px',
    color: THEME_COLORS.textBright,
    marginBottom: '6px',
    display: 'block',
  },
  select: {
    width: '100%',
    padding: '8px',
    fontSize: '11px',
    color: THEME_COLORS.textBright,
    backgroundColor: THEME_COLORS.surfaceElevated,
    border: `1px solid ${THEME_COLORS.border}`,
    borderRadius: '4px',
    outline: 'none',
  },
  manualButton: {
    width: '100%',
    padding: '8px',
    marginTop: '8px',
    fontSize: '11px',
    fontWeight: 600,
    color: THEME_COLORS.textBright,
    backgroundColor: THEME_COLORS.surfaceElevated,
    border: `1px solid ${THEME_COLORS.border}`,
    borderRadius: '4px',
    cursor: 'pointer',
    transition: 'all 0.2s',
  },
  manualInputContainer: {
    marginTop: '8px',
  },
  textarea: {
    width: '100%',
    padding: '8px',
    fontSize: '10px',
    fontFamily: 'monospace',
    color: THEME_COLORS.textBright,
    backgroundColor: THEME_COLORS.background,
    border: `1px solid ${THEME_COLORS.border}`,
    borderRadius: '4px',
    resize: 'vertical' as const,
    outline: 'none',
  },
  submitButton: {
    width: '100%',
    padding: '8px',
    marginTop: '8px',
    fontSize: '11px',
    fontWeight: 600,
    color: '#FFFFFF',
    backgroundColor: THEME_COLORS.blue,
    border: 'none',
    borderRadius: '4px',
    cursor: 'pointer',
    transition: 'all 0.2s',
  },
};
