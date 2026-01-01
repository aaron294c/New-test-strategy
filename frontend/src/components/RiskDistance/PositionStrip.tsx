/**
 * Position Strip - Visual bar showing price position relative to support levels
 * Compact, deterministic visualization with no subjective elements
 */

import React from 'react';
import { RiskDistanceOutput } from './types';
import { findClosestSupport } from './calculator';

interface PositionStripProps {
  data: RiskDistanceOutput;
  height?: number;
  lowerExtThresholdPct?: number;  // Visual proximity threshold for lower_ext (default: 20%)
  useAbsoluteDistance?: boolean;  // Use absolute value for threshold comparison (default: true)
  nwBandThresholdPct?: number;    // Visual proximity threshold for nw_lower_band (default: 20%)
}

export const PositionStrip: React.FC<PositionStripProps> = ({
  data,
  height = 40,
  lowerExtThresholdPct = 20,
  useAbsoluteDistance = true,
  nwBandThresholdPct = 20
}) => {
  const {
    price,
    st_put,
    lt_put,
    q_put,
    max_pain,
    lower_ext,
    pct_dist_lower_ext,
    nw_lower_band,
    pct_dist_nw_lower_band
  } = data;

  // Helper function to check if a level is within visual proximity threshold
  const isWithinProximity = (pctDist: number | null, threshold: number): boolean => {
    if (pctDist === null) return false;
    const dist = useAbsoluteDistance ? Math.abs(pctDist) : pctDist;
    return dist <= threshold;
  };

  // Collect all valid levels with proximity filtering
  const levels: Array<{ name: string; value: number; label: string; color: string }> = [];
  const hiddenLevels: Array<{ name: string; pctDist: number; reason: string }> = [];

  // Always show core PUT levels
  if (st_put !== null) {
    levels.push({ name: 'st_put', value: st_put, label: 'ST', color: '#26A69A' });
  }
  if (lt_put !== null) {
    levels.push({ name: 'lt_put', value: lt_put, label: 'LT', color: '#2962FF' });
  }
  if (q_put !== null) {
    levels.push({ name: 'q_put', value: q_put, label: 'Q', color: '#9C27B0' });
  }
  if (max_pain !== null) {
    levels.push({ name: 'max_pain', value: max_pain, label: 'MP', color: '#FF0080' });
  }

  // Conditionally show lower_ext based on proximity
  if (lower_ext !== null) {
    if (isWithinProximity(pct_dist_lower_ext, lowerExtThresholdPct)) {
      levels.push({ name: 'lower_ext', value: lower_ext, label: 'LE', color: '#2196F3' });
    } else {
      hiddenLevels.push({
        name: 'Lower Extension',
        pctDist: pct_dist_lower_ext || 0,
        reason: `> ${lowerExtThresholdPct}% from price`
      });
    }
  }

  // Conditionally show nw_lower_band based on proximity
  if (nw_lower_band !== null) {
    if (isWithinProximity(pct_dist_nw_lower_band, nwBandThresholdPct)) {
      levels.push({ name: 'nw_lower_band', value: nw_lower_band, label: 'NW', color: '#00BCD4' });
    } else {
      hiddenLevels.push({
        name: 'NW Band',
        pctDist: pct_dist_nw_lower_band || 0,
        reason: `> ${nwBandThresholdPct}% from price`
      });
    }
  }

  // Handle missing data
  if (price === null || levels.length === 0) {
    return (
      <div style={styles.container}>
        <div style={{ ...styles.strip, height }}>
          <div style={styles.naText}>N/A - Insufficient Data</div>
        </div>
      </div>
    );
  }

  // Find min and max for normalization
  const allValues = [...levels.map(l => l.value), price];
  const minValue = Math.min(...allValues);
  const maxValue = Math.max(...allValues);
  const range = maxValue - minValue;

  // Add 5% padding on each side
  const paddedMin = minValue - range * 0.05;
  const paddedMax = maxValue + range * 0.05;
  const paddedRange = paddedMax - paddedMin;

  // Normalize to 0-100 scale
  const normalize = (val: number) => ((val - paddedMin) / paddedRange) * 100;

  const pricePos = normalize(price);
  const closestSupport = findClosestSupport(data);

  return (
    <div style={styles.container}>
      <div style={{ ...styles.strip, height }}>
        {/* Background gradient */}
        <div style={styles.gradientBg} />

        {/* Support level markers */}
        {levels.map((level, idx) => {
          const pos = normalize(level.value);
          const isClosest = level.name === closestSupport;

          return (
            <div
              key={idx}
              style={{
                ...styles.levelMarker,
                left: `${pos}%`,
                borderColor: level.color,
                borderWidth: isClosest ? '3px' : '2px',
                opacity: isClosest ? 1.0 : 0.6,
              }}
              title={`${level.label}: $${level.value.toFixed(2)}`}
            >
              <div
                style={{
                  ...styles.levelLabel,
                  color: level.color,
                  fontWeight: isClosest ? 700 : 500,
                  fontSize: isClosest ? '11px' : '10px',
                }}
              >
                {level.label}
              </div>
            </div>
          );
        })}

        {/* Current price indicator */}
        <div
          style={{
            ...styles.priceIndicator,
            left: `${pricePos}%`,
          }}
          title={`Current Price: $${price.toFixed(2)}`}
        >
          <div style={styles.priceArrow}>▼</div>
          <div style={styles.priceLine} />
          <div style={styles.priceLabel}>${price.toFixed(0)}</div>
        </div>
      </div>

      {/* Legend */}
      <div style={styles.legend}>
        {levels.map((level, idx) => (
          <div key={idx} style={styles.legendItem}>
            <div style={{ ...styles.legendDot, backgroundColor: level.color }} />
            <span style={styles.legendText}>
              {level.label}: ${level.value.toFixed(0)}
            </span>
          </div>
        ))}
      </div>

      {/* Hidden Levels Indicator */}
      {hiddenLevels.length > 0 && (
        <div style={styles.hiddenIndicator} role="status" aria-live="polite">
          {hiddenLevels.map((hidden, idx) => (
            <span key={idx} style={styles.hiddenText} title={`${hidden.name} at ${hidden.pctDist.toFixed(1)}%`}>
              {hidden.name} not shown ({hidden.reason})
              {idx < hiddenLevels.length - 1 ? '; ' : ''}
            </span>
          ))}
        </div>
      )}
    </div>
  );
};

const styles: Record<string, React.CSSProperties> = {
  container: {
    width: '100%',
    padding: '8px 0',
  },
  strip: {
    position: 'relative',
    width: '100%',
    backgroundColor: '#1C2128',
    borderRadius: '6px',
    border: '1px solid #373E47',
    overflow: 'visible',
  },
  gradientBg: {
    position: 'absolute',
    top: 0,
    left: 0,
    right: 0,
    bottom: 0,
    background: 'linear-gradient(90deg, rgba(239, 83, 80, 0.05) 0%, rgba(38, 166, 154, 0.05) 100%)',
    borderRadius: '6px',
  },
  levelMarker: {
    position: 'absolute',
    top: '50%',
    transform: 'translateX(-50%) translateY(-50%)',
    width: '2px',
    height: '100%',
    borderLeft: '2px solid',
    pointerEvents: 'none' as const,
  },
  levelLabel: {
    position: 'absolute',
    top: '-20px',
    left: '50%',
    transform: 'translateX(-50%)',
    fontSize: '10px',
    fontWeight: 500,
    whiteSpace: 'nowrap' as const,
    backgroundColor: '#1C2128',
    padding: '2px 4px',
    borderRadius: '3px',
  },
  priceIndicator: {
    position: 'absolute',
    top: 0,
    bottom: 0,
    transform: 'translateX(-50%)',
    pointerEvents: 'none' as const,
  },
  priceArrow: {
    position: 'absolute',
    top: '-12px',
    left: '50%',
    transform: 'translateX(-50%)',
    fontSize: '12px',
    color: '#FFFFFF',
    textShadow: '0 0 4px rgba(0,0,0,0.5)',
  },
  priceLine: {
    position: 'absolute',
    top: 0,
    bottom: 0,
    left: '50%',
    width: '2px',
    backgroundColor: '#FFFFFF',
    transform: 'translateX(-50%)',
    boxShadow: '0 0 4px rgba(255,255,255,0.5)',
  },
  priceLabel: {
    position: 'absolute',
    bottom: '-20px',
    left: '50%',
    transform: 'translateX(-50%)',
    fontSize: '11px',
    fontWeight: 700,
    color: '#FFFFFF',
    backgroundColor: 'rgba(0,0,0,0.8)',
    padding: '2px 6px',
    borderRadius: '3px',
    whiteSpace: 'nowrap' as const,
  },
  legend: {
    display: 'flex',
    flexWrap: 'wrap' as const,
    gap: '12px',
    marginTop: '8px',
    fontSize: '10px',
  },
  legendItem: {
    display: 'flex',
    alignItems: 'center',
    gap: '4px',
  },
  legendDot: {
    width: '8px',
    height: '8px',
    borderRadius: '50%',
  },
  legendText: {
    color: '#8B949E',
  },
  hiddenIndicator: {
    marginTop: '4px',
    fontSize: '9px',
    color: '#6E7681',
    fontStyle: 'italic' as const,
    textAlign: 'center' as const,
  },
  hiddenText: {
    color: '#6E7681',
  },
  naText: {
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    height: '100%',
    color: '#8B949E',
    fontSize: '11px',
  },
};
