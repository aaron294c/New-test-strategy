/**
 * Symbol Card - Compact display of risk distance metrics
 * Shows distances, boolean flags, and visual position strip
 */

import React from 'react';
import { RiskDistanceOutput } from './types';
import { PositionStrip } from './PositionStrip';
import { formatDistance, formatPrice } from './calculator';

interface SymbolCardProps {
  data: RiskDistanceOutput;
  selected?: boolean;
  onSelect?: (symbol: string) => void;
  lowerExtThresholdPct?: number;
  nwBandThresholdPct?: number;
  useAbsoluteDistance?: boolean;
}

export const SymbolCard: React.FC<SymbolCardProps> = ({
  data,
  selected = false,
  onSelect,
  lowerExtThresholdPct = 20,
  nwBandThresholdPct = 20,
  useAbsoluteDistance = true,
}) => {
  const {
    symbol,
    price,
    st_put,
    pct_dist_st_put,
    is_below_st_put,
    lt_put,
    pct_dist_lt_put,
    is_below_lt_put,
    q_put,
    pct_dist_q_put,
    is_below_q_put,
    max_pain,
    pct_dist_max_pain,
    is_below_max_pain,
    lower_ext,
    pct_dist_lower_ext,
    is_below_lower_ext,
    nw_lower_band,
    pct_dist_nw_lower_band,
    is_below_nw_lower_band,
    last_update,
  } = data;

  const handleCardClick = () => {
    if (onSelect) {
      onSelect(symbol);
    }
  };

  return (
    <div
      style={{
        ...styles.card,
        ...(selected ? styles.cardSelected : {}),
      }}
      onClick={handleCardClick}
    >
      {/* Header */}
      <div style={styles.header}>
        <div style={styles.symbolInfo}>
          <span style={styles.symbol}>{symbol}</span>
          <span style={styles.price}>{formatPrice(price)}</span>
        </div>
        <div style={styles.timestamp}>{last_update}</div>
      </div>

      {/* Visual Strip */}
      <PositionStrip
        data={data}
        height={36}
        lowerExtThresholdPct={lowerExtThresholdPct}
        nwBandThresholdPct={nwBandThresholdPct}
        useAbsoluteDistance={useAbsoluteDistance}
      />

      {/* Metrics Grid */}
      <div style={styles.metricsGrid}>
        {/* ST Put */}
        <MetricRow
          label="ST Put"
          levelValue={st_put}
          pctDist={pct_dist_st_put}
          isBelow={is_below_st_put}
          color="#26A69A"
        />

        {/* LT Put */}
        <MetricRow
          label="LT Put"
          levelValue={lt_put}
          pctDist={pct_dist_lt_put}
          isBelow={is_below_lt_put}
          color="#2962FF"
        />

        {/* Q Put */}
        <MetricRow
          label="Q Put"
          levelValue={q_put}
          pctDist={pct_dist_q_put}
          isBelow={is_below_q_put}
          color="#9C27B0"
        />

        {/* Max Pain */}
        <MetricRow
          label="Max Pain"
          levelValue={max_pain}
          pctDist={pct_dist_max_pain}
          isBelow={is_below_max_pain}
          color="#FF0080"
        />

        {/* Lower Extension (MBAD Blue Line) */}
        <MetricRow
          label="Lower Ext"
          levelValue={lower_ext}
          pctDist={pct_dist_lower_ext}
          isBelow={is_below_lower_ext}
          color="#2196F3"
        />

        {/* Nadaraya-Watson Lower Band */}
        <MetricRow
          label="NW Band"
          levelValue={nw_lower_band}
          pctDist={pct_dist_nw_lower_band}
          isBelow={is_below_nw_lower_band}
          color="#00BCD4"
        />
      </div>
    </div>
  );
};

interface MetricRowProps {
  label: string;
  levelValue: number | null;
  pctDist: number | null;
  isBelow: boolean | null;
  color: string;
}

const MetricRow: React.FC<MetricRowProps> = ({ label, levelValue, pctDist, isBelow, color }) => {
  return (
    <div style={styles.metricRow}>
      <div style={styles.metricLabel}>
        <div style={{ ...styles.metricDot, backgroundColor: color }} />
        {label}
      </div>
      <div style={styles.metricValue}>{formatPrice(levelValue)}</div>
      <div
        style={{
          ...styles.metricDistance,
          color: pctDist === null ? '#8B949E' : pctDist < 0 ? '#EF5350' : '#26A69A',
        }}
      >
        {formatDistance(pctDist)}
      </div>
      <div style={styles.metricFlag}>
        {isBelow === null ? (
          <span style={styles.flagNA}>N/A</span>
        ) : isBelow ? (
          <span style={styles.flagBelow}>BELOW</span>
        ) : (
          <span style={styles.flagAbove}>ABOVE</span>
        )}
      </div>
    </div>
  );
};

const styles: Record<string, React.CSSProperties> = {
  card: {
    backgroundColor: '#1C2128',
    border: '1px solid #373E47',
    borderRadius: '8px',
    padding: '14px',
    cursor: 'pointer',
    transition: 'all 0.2s',
  },
  cardSelected: {
    borderColor: '#2962FF',
    boxShadow: '0 0 0 2px rgba(41, 98, 255, 0.2)',
  },

  // Header
  header: {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: '12px',
    paddingBottom: '10px',
    borderBottom: '1px solid #373E47',
  },
  symbolInfo: {
    display: 'flex',
    alignItems: 'baseline',
    gap: '10px',
  },
  symbol: {
    fontSize: '15px',
    fontWeight: 700,
    color: '#D1D4DC',
  },
  price: {
    fontSize: '13px',
    fontWeight: 600,
    color: '#FFFFFF',
  },
  timestamp: {
    fontSize: '9px',
    color: '#6E7681',
  },

  // Metrics Grid
  metricsGrid: {
    display: 'flex',
    flexDirection: 'column',
    gap: '8px',
    marginTop: '12px',
  },
  metricRow: {
    display: 'grid',
    gridTemplateColumns: '100px 90px 80px 70px',
    gap: '8px',
    alignItems: 'center',
    padding: '6px 8px',
    backgroundColor: 'rgba(55, 62, 71, 0.3)',
    borderRadius: '4px',
    fontSize: '11px',
  },
  metricLabel: {
    display: 'flex',
    alignItems: 'center',
    gap: '6px',
    color: '#D1D4DC',
    fontWeight: 500,
  },
  metricDot: {
    width: '8px',
    height: '8px',
    borderRadius: '50%',
    flexShrink: 0,
  },
  metricValue: {
    color: '#8B949E',
    fontFamily: 'monospace',
  },
  metricDistance: {
    fontWeight: 600,
    fontFamily: 'monospace',
    textAlign: 'right' as const,
  },
  metricFlag: {
    textAlign: 'center' as const,
  },
  flagBelow: {
    display: 'inline-block',
    padding: '2px 6px',
    fontSize: '9px',
    fontWeight: 700,
    color: '#EF5350',
    backgroundColor: 'rgba(239, 83, 80, 0.15)',
    borderRadius: '3px',
  },
  flagAbove: {
    display: 'inline-block',
    padding: '2px 6px',
    fontSize: '9px',
    fontWeight: 700,
    color: '#26A69A',
    backgroundColor: 'rgba(38, 166, 154, 0.15)',
    borderRadius: '3px',
  },
  flagNA: {
    display: 'inline-block',
    padding: '2px 6px',
    fontSize: '9px',
    fontWeight: 700,
    color: '#8B949E',
    backgroundColor: 'rgba(139, 148, 158, 0.15)',
    borderRadius: '3px',
  },
};
