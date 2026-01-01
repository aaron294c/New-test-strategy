import React from 'react';
import { LowerExtMetrics } from '../../utils/lowerExtensionCalculations';
import Sparkline from './Sparkline';

interface SymbolCardProps {
  metrics: LowerExtMetrics;
  historicalPrices?: Array<{ timestamp: string | number; price: number }>;
  onExportJSON: () => void;
}

const SymbolCard: React.FC<SymbolCardProps> = ({ metrics, historicalPrices, onExportJSON }) => {
  const formatNumber = (num: number, decimals: number = 2): string => {
    return num.toFixed(decimals);
  };

  const formatPercent = (num: number, decimals: number = 2): string => {
    return `${num >= 0 ? '+' : ''}${formatNumber(num, decimals)}%`;
  };

  return (
    <div
      style={{
        background: '#1f2937',
        borderRadius: '12px',
        padding: '24px',
        color: 'white',
        boxShadow: '0 4px 12px rgba(0,0,0,0.3)',
      }}
    >
      {/* Header */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px' }}>
        <div>
          <h2 style={{ fontSize: '28px', fontWeight: '700', margin: '0 0 4px 0' }}>{metrics.symbol}</h2>
          <div style={{ fontSize: '14px', color: '#9ca3af' }}>
            Last updated: {metrics.last_update}
            {metrics.stale_data && (
              <span
                style={{
                  marginLeft: '8px',
                  padding: '2px 8px',
                  background: '#ef4444',
                  borderRadius: '4px',
                  fontSize: '12px',
                }}
              >
                Stale Data
              </span>
            )}
          </div>
        </div>
        <button
          onClick={onExportJSON}
          style={{
            background: '#3b82f6',
            color: 'white',
            border: 'none',
            padding: '10px 20px',
            borderRadius: '8px',
            fontSize: '14px',
            fontWeight: '600',
            cursor: 'pointer',
            transition: 'background 0.2s',
          }}
          onMouseOver={(e) => (e.currentTarget.style.background = '#2563eb')}
          onMouseOut={(e) => (e.currentTarget.style.background = '#3b82f6')}
        >
          Export JSON
        </button>
      </div>

      {/* Price & Lower Extension */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: '16px', marginBottom: '24px' }}>
        <div>
          <div style={{ fontSize: '12px', color: '#9ca3af', marginBottom: '4px' }}>Current Price</div>
          <div style={{ fontSize: '24px', fontWeight: '700' }}>${formatNumber(metrics.price)}</div>
        </div>
        <div>
          <div style={{ fontSize: '12px', color: '#9ca3af', marginBottom: '4px' }}>Lower Extension</div>
          <div style={{ fontSize: '24px', fontWeight: '700', color: '#2962ff' }}>
            ${formatNumber(metrics.lower_ext)}
          </div>
        </div>
        <div>
          <div style={{ fontSize: '12px', color: '#9ca3af', marginBottom: '4px' }}>Distance Status</div>
          <div
            style={{
              fontSize: '18px',
              fontWeight: '700',
              color: metrics.is_below_lower_ext ? '#22c55e' : '#6b7280',
              display: 'flex',
              alignItems: 'center',
              gap: '8px',
            }}
          >
            {metrics.is_below_lower_ext ? (
              <>
                <span style={{ fontSize: '24px' }}>↓</span> Below
              </>
            ) : (
              <>
                <span style={{ fontSize: '24px' }}>↑</span> Above
              </>
            )}
          </div>
        </div>
      </div>

      {/* Distance Metrics */}
      <div style={{ marginBottom: '24px', padding: '16px', background: '#111827', borderRadius: '8px' }}>
        <div style={{ fontSize: '14px', fontWeight: '600', marginBottom: '12px' }}>Distance Metrics</div>
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px' }}>
          <div>
            <div style={{ fontSize: '12px', color: '#9ca3af' }}>Signed Distance</div>
            <div
              style={{
                fontSize: '20px',
                fontWeight: '700',
                color: metrics.pct_dist_lower_ext < 0 ? '#22c55e' : '#6b7280',
              }}
            >
              {formatPercent(metrics.pct_dist_lower_ext)}
            </div>
          </div>
          <div>
            <div style={{ fontSize: '12px', color: '#9ca3af' }}>Absolute Distance</div>
            <div style={{ fontSize: '20px', fontWeight: '700' }}>{formatPercent(metrics.abs_pct_dist_lower_ext)}</div>
          </div>
        </div>
      </div>

      {/* 30-Day Metrics */}
      <div style={{ marginBottom: '24px', padding: '16px', background: '#111827', borderRadius: '8px' }}>
        <div style={{ fontSize: '14px', fontWeight: '600', marginBottom: '12px' }}>30-Day Lookback Metrics</div>
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px', marginBottom: '12px' }}>
          <div>
            <div style={{ fontSize: '12px', color: '#9ca3af' }}>Min Distance (Deepest Breach)</div>
            <div
              style={{
                fontSize: '18px',
                fontWeight: '600',
                color: metrics.min_pct_dist_30d < 0 ? '#22c55e' : '#6b7280',
              }}
            >
              {formatPercent(metrics.min_pct_dist_30d)}
            </div>
          </div>
          <div>
            <div style={{ fontSize: '12px', color: '#9ca3af' }}>Median Abs Distance</div>
            <div style={{ fontSize: '18px', fontWeight: '600' }}>{formatPercent(metrics.median_abs_pct_dist_30d)}</div>
          </div>
          <div>
            <div style={{ fontSize: '12px', color: '#9ca3af' }}>Breach Count</div>
            <div style={{ fontSize: '18px', fontWeight: '600' }}>{metrics.breach_count_30d} days</div>
          </div>
          <div>
            <div style={{ fontSize: '12px', color: '#9ca3af' }}>Breach Rate</div>
            <div style={{ fontSize: '18px', fontWeight: '600' }}>
              {formatPercent(metrics.breach_rate_30d * 100, 1)}
            </div>
          </div>
        </div>

        <div style={{ marginTop: '12px' }}>
          <div style={{ fontSize: '12px', color: '#9ca3af', marginBottom: '4px' }}>Recently Breached (Last 5)</div>
          <div
            style={{
              display: 'inline-block',
              padding: '4px 12px',
              borderRadius: '6px',
              fontSize: '14px',
              fontWeight: '600',
              background: metrics.recent_breached ? '#22c55e' : '#6b7280',
              color: 'white',
            }}
          >
            {metrics.recent_breached ? 'Yes' : 'No'}
          </div>
        </div>
      </div>

      {/* Proximity Score */}
      <div style={{ marginBottom: '24px', padding: '16px', background: '#111827', borderRadius: '8px' }}>
        <div
          style={{
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
            marginBottom: '8px',
          }}
        >
          <div style={{ fontSize: '14px', fontWeight: '600' }}>Proximity Score (0-1)</div>
          <div style={{ fontSize: '20px', fontWeight: '700' }}>{formatNumber(metrics.proximity_score_30d, 3)}</div>
        </div>
        <div style={{ width: '100%', height: '12px', background: '#374151', borderRadius: '6px', overflow: 'hidden' }}>
          <div
            style={{
              width: `${metrics.proximity_score_30d * 100}%`,
              height: '100%',
              background: `linear-gradient(to right, #ef4444, #f59e0b, #22c55e)`,
              transition: 'width 0.3s ease',
            }}
          />
        </div>
        <div style={{ fontSize: '12px', color: '#9ca3af', marginTop: '4px' }}>
          Higher score = closer historically (less risky)
        </div>
      </div>

      {/* Sparkline */}
      {historicalPrices && historicalPrices.length > 0 && (
        <div style={{ padding: '16px', background: '#111827', borderRadius: '8px' }}>
          <div style={{ fontSize: '14px', fontWeight: '600', marginBottom: '12px' }}>30-Day Price History</div>
          <Sparkline data={historicalPrices} lowerExt={metrics.lower_ext} />
        </div>
      )}
    </div>
  );
};

export default SymbolCard;
