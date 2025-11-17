import React from 'react';
import { CalculationSettings } from '../../utils/lowerExtensionCalculations';

interface SettingsPanelProps {
  settings: CalculationSettings;
  onSettingsChange: (settings: CalculationSettings) => void;
  autoRefresh: boolean;
  onAutoRefreshChange: (enabled: boolean) => void;
  refreshInterval: number;
  onRefreshIntervalChange: (interval: number) => void;
  onManualRefresh: () => void;
}

const SettingsPanel: React.FC<SettingsPanelProps> = ({
  settings,
  onSettingsChange,
  autoRefresh,
  onAutoRefreshChange,
  refreshInterval,
  onRefreshIntervalChange,
  onManualRefresh,
}) => {
  const handleChange = (key: keyof CalculationSettings, value: any) => {
    onSettingsChange({
      ...settings,
      [key]: value,
    });
  };

  return (
    <div
      style={{
        background: '#1f2937',
        borderRadius: '12px',
        padding: '20px',
        color: 'white',
        boxShadow: '0 4px 12px rgba(0,0,0,0.3)',
      }}
    >
      <h3 style={{ fontSize: '18px', fontWeight: '700', marginBottom: '20px', margin: '0 0 20px 0' }}>
        Settings & Controls
      </h3>

      {/* Calculation Settings */}
      <div style={{ marginBottom: '24px' }}>
        <div style={{ fontSize: '14px', fontWeight: '600', marginBottom: '12px' }}>Calculation Settings</div>

        <div style={{ display: 'grid', gap: '16px' }}>
          {/* Lookback Days */}
          <div>
            <label style={{ display: 'block', fontSize: '12px', color: '#9ca3af', marginBottom: '6px' }}>
              Lookback Days (30-day window)
            </label>
            <input
              type="number"
              min="1"
              max="365"
              value={settings.lookback_days}
              onChange={(e) => handleChange('lookback_days', parseInt(e.target.value))}
              style={{
                width: '100%',
                padding: '8px 12px',
                background: '#111827',
                border: '1px solid #374151',
                borderRadius: '6px',
                color: 'white',
                fontSize: '14px',
              }}
            />
          </div>

          {/* Recent N */}
          <div>
            <label style={{ display: 'block', fontSize: '12px', color: '#9ca3af', marginBottom: '6px' }}>
              Recent N (days to check for recent breach)
            </label>
            <input
              type="number"
              min="1"
              max="30"
              value={settings.recent_N}
              onChange={(e) => handleChange('recent_N', parseInt(e.target.value))}
              style={{
                width: '100%',
                padding: '8px 12px',
                background: '#111827',
                border: '1px solid #374151',
                borderRadius: '6px',
                color: 'white',
                fontSize: '14px',
              }}
            />
          </div>

          {/* Proximity Threshold */}
          <div>
            <label style={{ display: 'block', fontSize: '12px', color: '#9ca3af', marginBottom: '6px' }}>
              Proximity Threshold (%) for score calculation
            </label>
            <input
              type="number"
              min="0.1"
              max="20"
              step="0.1"
              value={settings.proximity_threshold}
              onChange={(e) => handleChange('proximity_threshold', parseFloat(e.target.value))}
              style={{
                width: '100%',
                padding: '8px 12px',
                background: '#111827',
                border: '1px solid #374151',
                borderRadius: '6px',
                color: 'white',
                fontSize: '14px',
              }}
            />
            <div style={{ fontSize: '11px', color: '#6b7280', marginTop: '4px' }}>
              Default: 5.0%. Higher = more lenient scoring
            </div>
          </div>

          {/* Price Source */}
          <div>
            <label style={{ display: 'block', fontSize: '12px', color: '#9ca3af', marginBottom: '6px' }}>
              Price Source (candle data)
            </label>
            <select
              value={settings.price_source}
              onChange={(e) => handleChange('price_source', e.target.value)}
              style={{
                width: '100%',
                padding: '8px 12px',
                background: '#111827',
                border: '1px solid #374151',
                borderRadius: '6px',
                color: 'white',
                fontSize: '14px',
              }}
            >
              <option value="close">Close</option>
              <option value="wick">Wick (Low)</option>
              <option value="high">High</option>
              <option value="low">Low</option>
            </select>
          </div>
        </div>
      </div>

      {/* Refresh Settings */}
      <div style={{ marginBottom: '24px' }}>
        <div style={{ fontSize: '14px', fontWeight: '600', marginBottom: '12px' }}>Refresh Settings</div>

        <div style={{ display: 'grid', gap: '16px' }}>
          {/* Auto Refresh Toggle */}
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
            <label style={{ fontSize: '14px', color: '#d1d5db' }}>Auto Refresh</label>
            <button
              onClick={() => onAutoRefreshChange(!autoRefresh)}
              style={{
                padding: '6px 12px',
                background: autoRefresh ? '#22c55e' : '#6b7280',
                border: 'none',
                borderRadius: '6px',
                color: 'white',
                fontSize: '14px',
                fontWeight: '600',
                cursor: 'pointer',
                transition: 'background 0.2s',
              }}
            >
              {autoRefresh ? 'ON' : 'OFF'}
            </button>
          </div>

          {/* Refresh Interval */}
          {autoRefresh && (
            <div>
              <label style={{ display: 'block', fontSize: '12px', color: '#9ca3af', marginBottom: '6px' }}>
                Refresh Interval (seconds)
              </label>
              <input
                type="number"
                min="5"
                max="300"
                step="5"
                value={refreshInterval}
                onChange={(e) => onRefreshIntervalChange(parseInt(e.target.value))}
                style={{
                  width: '100%',
                  padding: '8px 12px',
                  background: '#111827',
                  border: '1px solid #374151',
                  borderRadius: '6px',
                  color: 'white',
                  fontSize: '14px',
                }}
              />
            </div>
          )}

          {/* Manual Refresh Button */}
          <button
            onClick={onManualRefresh}
            style={{
              width: '100%',
              padding: '10px',
              background: '#3b82f6',
              border: 'none',
              borderRadius: '8px',
              color: 'white',
              fontSize: '14px',
              fontWeight: '600',
              cursor: 'pointer',
              transition: 'background 0.2s',
            }}
            onMouseOver={(e) => (e.currentTarget.style.background = '#2563eb')}
            onMouseOut={(e) => (e.currentTarget.style.background = '#3b82f6')}
          >
            Manual Refresh Now
          </button>
        </div>
      </div>

      {/* Visual Settings */}
      <div>
        <div style={{ fontSize: '14px', fontWeight: '600', marginBottom: '12px' }}>Visual Settings</div>
        <div style={{ fontSize: '12px', color: '#9ca3af' }}>
          Chart annotations and shading are controlled per-chart component
        </div>
      </div>
    </div>
  );
};

export default SettingsPanel;
