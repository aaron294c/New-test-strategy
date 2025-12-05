/**
 * Proximity Settings - Configure visual proximity thresholds for support levels
 * Controls when Lower Extension and NW Band markers appear on the horizontal bar
 */

import React from 'react';

export interface ProximityConfig {
  lowerExtThresholdPct: number;
  nwBandThresholdPct: number;
  useAbsoluteDistance: boolean;
}

interface ProximitySettingsProps {
  config: ProximityConfig;
  onChange: (config: ProximityConfig) => void;
  isExpanded: boolean;
  onToggleExpanded: () => void;
}

export const ProximitySettings: React.FC<ProximitySettingsProps> = ({
  config,
  onChange,
  isExpanded,
  onToggleExpanded,
}) => {
  const handleLowerExtThresholdChange = (value: number) => {
    onChange({
      ...config,
      lowerExtThresholdPct: Math.max(0, Math.min(100, value)),
    });
  };

  const handleNwBandThresholdChange = (value: number) => {
    onChange({
      ...config,
      nwBandThresholdPct: Math.max(0, Math.min(100, value)),
    });
  };

  const handleAbsoluteDistanceToggle = () => {
    onChange({
      ...config,
      useAbsoluteDistance: !config.useAbsoluteDistance,
    });
  };

  return (
    <div style={styles.container}>
      <div style={styles.header} onClick={onToggleExpanded}>
        <div style={styles.headerLeft}>
          <span style={styles.headerIcon}>{isExpanded ? '▼' : '▶'}</span>
          <span style={styles.headerTitle}>Proximity Settings</span>
          <span style={styles.headerSubtitle}>
            Configure when levels appear on visual bar
          </span>
        </div>
        <div style={styles.headerRight}>
          <span style={styles.badge}>
            LE: {config.lowerExtThresholdPct}% | NW: {config.nwBandThresholdPct}%
          </span>
        </div>
      </div>

      {isExpanded && (
        <div style={styles.content}>
          {/* Lower Extension Threshold */}
          <div style={styles.settingRow}>
            <div style={styles.settingLabel}>
              <div style={{ ...styles.settingDot, backgroundColor: '#2196F3' }} />
              <span style={styles.settingName}>Lower Extension Threshold</span>
            </div>
            <div style={styles.settingControl}>
              <input
                type="range"
                min="0"
                max="100"
                step="1"
                value={config.lowerExtThresholdPct}
                onChange={(e) => handleLowerExtThresholdChange(Number(e.target.value))}
                style={styles.slider}
              />
              <input
                type="number"
                min="0"
                max="100"
                step="1"
                value={config.lowerExtThresholdPct}
                onChange={(e) => handleLowerExtThresholdChange(Number(e.target.value))}
                style={styles.numberInput}
              />
              <span style={styles.unit}>%</span>
            </div>
            <div style={styles.settingHelp}>
              Show Lower Extension marker only if within this % of price
            </div>
          </div>

          {/* Nadaraya-Watson Threshold */}
          <div style={styles.settingRow}>
            <div style={styles.settingLabel}>
              <div style={{ ...styles.settingDot, backgroundColor: '#00BCD4' }} />
              <span style={styles.settingName}>NW Band Threshold</span>
            </div>
            <div style={styles.settingControl}>
              <input
                type="range"
                min="0"
                max="100"
                step="1"
                value={config.nwBandThresholdPct}
                onChange={(e) => handleNwBandThresholdChange(Number(e.target.value))}
                style={styles.slider}
              />
              <input
                type="number"
                min="0"
                max="100"
                step="1"
                value={config.nwBandThresholdPct}
                onChange={(e) => handleNwBandThresholdChange(Number(e.target.value))}
                style={styles.numberInput}
              />
              <span style={styles.unit}>%</span>
            </div>
            <div style={styles.settingHelp}>
              Show NW Band marker only if within this % of price
            </div>
          </div>

          {/* Absolute Distance Toggle */}
          <div style={styles.settingRow}>
            <div style={styles.settingLabel}>
              <div style={{ ...styles.settingDot, backgroundColor: '#8B949E' }} />
              <span style={styles.settingName}>Use Absolute Distance</span>
            </div>
            <div style={styles.settingControl}>
              <label style={styles.toggleLabel}>
                <input
                  type="checkbox"
                  checked={config.useAbsoluteDistance}
                  onChange={handleAbsoluteDistanceToggle}
                  style={styles.checkbox}
                />
                <span style={styles.toggleText}>
                  {config.useAbsoluteDistance ? 'Enabled' : 'Disabled'}
                </span>
              </label>
            </div>
            <div style={styles.settingHelp}>
              {config.useAbsoluteDistance
                ? 'Threshold applies to |distance| (both above and below)'
                : 'Threshold applies to signed distance only'}
            </div>
          </div>

          {/* Info Box */}
          <div style={styles.infoBox}>
            <div style={styles.infoIcon}>ℹ️</div>
            <div style={styles.infoText}>
              <strong>How it works:</strong> Core PUT levels (ST, LT, Q, Max Pain) always
              appear on the bar. Lower Extension and NW Band markers only appear if their
              distance from price is within the configured threshold. Hidden levels remain
              visible in the detailed metrics table below.
            </div>
          </div>

          {/* Reset Button */}
          <div style={styles.footer}>
            <button
              onClick={() =>
                onChange({
                  lowerExtThresholdPct: 20,
                  nwBandThresholdPct: 20,
                  useAbsoluteDistance: true,
                })
              }
              style={styles.resetButton}
            >
              Reset to Defaults
            </button>
          </div>
        </div>
      )}
    </div>
  );
};

const styles: Record<string, React.CSSProperties> = {
  container: {
    backgroundColor: '#1C2128',
    border: '1px solid #373E47',
    borderRadius: '6px',
    marginBottom: '16px',
  },

  // Header
  header: {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    padding: '12px 16px',
    cursor: 'pointer',
    userSelect: 'none' as const,
    transition: 'background-color 0.2s',
  },
  headerLeft: {
    display: 'flex',
    alignItems: 'center',
    gap: '10px',
    flex: 1,
  },
  headerIcon: {
    fontSize: '10px',
    color: '#8B949E',
    width: '12px',
  },
  headerTitle: {
    fontSize: '13px',
    fontWeight: 600,
    color: '#D1D4DC',
  },
  headerSubtitle: {
    fontSize: '11px',
    color: '#6E7681',
    marginLeft: '4px',
  },
  headerRight: {
    display: 'flex',
    gap: '8px',
  },
  badge: {
    fontSize: '10px',
    fontWeight: 600,
    color: '#8B949E',
    backgroundColor: 'rgba(55, 62, 71, 0.5)',
    padding: '4px 8px',
    borderRadius: '4px',
    fontFamily: 'monospace',
  },

  // Content
  content: {
    padding: '16px',
    borderTop: '1px solid #373E47',
  },
  settingRow: {
    marginBottom: '20px',
  },
  settingLabel: {
    display: 'flex',
    alignItems: 'center',
    gap: '8px',
    marginBottom: '8px',
  },
  settingDot: {
    width: '8px',
    height: '8px',
    borderRadius: '50%',
    flexShrink: 0,
  },
  settingName: {
    fontSize: '12px',
    fontWeight: 600,
    color: '#D1D4DC',
  },
  settingControl: {
    display: 'flex',
    alignItems: 'center',
    gap: '12px',
    marginBottom: '6px',
  },
  slider: {
    flex: 1,
    height: '4px',
    borderRadius: '2px',
    background: '#373E47',
    outline: 'none',
    cursor: 'pointer',
  },
  numberInput: {
    width: '60px',
    padding: '6px 8px',
    fontSize: '12px',
    fontWeight: 600,
    color: '#D1D4DC',
    backgroundColor: '#0D1117',
    border: '1px solid #373E47',
    borderRadius: '4px',
    textAlign: 'right' as const,
    fontFamily: 'monospace',
  },
  unit: {
    fontSize: '12px',
    fontWeight: 600,
    color: '#8B949E',
    width: '20px',
  },
  settingHelp: {
    fontSize: '10px',
    color: '#6E7681',
    fontStyle: 'italic' as const,
    paddingLeft: '16px',
  },
  toggleLabel: {
    display: 'flex',
    alignItems: 'center',
    gap: '8px',
    cursor: 'pointer',
  },
  checkbox: {
    width: '16px',
    height: '16px',
    cursor: 'pointer',
  },
  toggleText: {
    fontSize: '12px',
    fontWeight: 600,
    color: '#D1D4DC',
  },

  // Info Box
  infoBox: {
    display: 'flex',
    gap: '10px',
    padding: '12px',
    backgroundColor: 'rgba(41, 98, 255, 0.08)',
    border: '1px solid rgba(41, 98, 255, 0.2)',
    borderRadius: '6px',
    marginTop: '16px',
  },
  infoIcon: {
    fontSize: '14px',
    flexShrink: 0,
  },
  infoText: {
    fontSize: '11px',
    color: '#D1D4DC',
    lineHeight: '1.5',
  },

  // Footer
  footer: {
    display: 'flex',
    justifyContent: 'flex-end',
    marginTop: '16px',
    paddingTop: '12px',
    borderTop: '1px solid #373E47',
  },
  resetButton: {
    padding: '6px 14px',
    fontSize: '11px',
    fontWeight: 600,
    color: '#D1D4DC',
    backgroundColor: 'transparent',
    border: '1px solid #373E47',
    borderRadius: '4px',
    cursor: 'pointer',
    transition: 'all 0.2s',
  },
};
