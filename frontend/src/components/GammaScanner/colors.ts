/**
 * TradingView-Inspired Color Palette
 * Rich gradients and vibrant accents for professional visualization
 */

// Base Theme Colors
export const THEME_COLORS = {
  // Backgrounds (darker than v3)
  background: '#0D1117',
  surface: '#1C2128',
  surfaceElevated: '#22272E',
  surfaceHover: '#2D333B',

  // Borders & Grids
  border: '#373E47',
  gridLine: '#30363D',

  // Text
  text: '#8B949E',
  textBright: '#D1D4DC',
  textMuted: '#6E7681',

  // Accents
  blue: '#2962FF',
  blueLight: '#5E92F3',
  green: '#26A69A',
  red: '#EF5350',
  orange: '#FFA726',
  purple: '#9C27B0',
  magenta: '#FF0080',
} as const;

// Call Wall Gradients (Red/Orange)
export const CALL_WALL_COLORS = {
  strong: {
    start: 'rgba(255, 56, 56, 0.35)',
    mid: 'rgba(255, 107, 0, 0.45)',
    end: 'rgba(255, 56, 56, 0.35)',
    border: 'rgba(255, 56, 56, 0.8)',
  },
  medium: {
    start: 'rgba(255, 82, 82, 0.28)',
    mid: 'rgba(255, 142, 0, 0.35)',
    end: 'rgba(255, 82, 82, 0.28)',
    border: 'rgba(255, 82, 82, 0.6)',
  },
  weak: {
    start: 'rgba(255, 107, 107, 0.20)',
    mid: 'rgba(255, 142, 142, 0.25)',
    end: 'rgba(255, 107, 107, 0.20)',
    border: 'rgba(255, 107, 107, 0.4)',
  },
} as const;

// Put Wall Gradients (Green/Cyan)
export const PUT_WALL_COLORS = {
  strong: {
    start: 'rgba(0, 137, 123, 0.35)',
    mid: 'rgba(38, 166, 154, 0.45)',
    end: 'rgba(0, 137, 123, 0.35)',
    border: 'rgba(0, 137, 123, 0.8)',
  },
  medium: {
    start: 'rgba(38, 166, 154, 0.28)',
    mid: 'rgba(78, 205, 196, 0.35)',
    end: 'rgba(38, 166, 154, 0.28)',
    border: 'rgba(38, 166, 154, 0.6)',
  },
  weak: {
    start: 'rgba(78, 205, 196, 0.20)',
    mid: 'rgba(110, 231, 223, 0.25)',
    end: 'rgba(78, 205, 196, 0.20)',
    border: 'rgba(78, 205, 196, 0.4)',
  },
} as const;

// Timeframe Colors
export const TIMEFRAME_COLORS = {
  swing: {
    opacity: 0.35,
    borderWidth: 3,
    zIndex: 4,
  },
  longterm: {
    color: '#2962FF',
    opacity: 0.25,
    borderWidth: 2,
    zIndex: 3,
  },
  quarterly: {
    color: '#9C27B0',
    opacity: 0.15,
    borderWidth: 1,
    borderStyle: 'dash',
    zIndex: 2,
  },
} as const;

// Max Pain Styling
export const MAX_PAIN = {
  color: '#FF0080',
  width: 3,
  glow: '0 0 8px #FF0080, 0 0 16px rgba(255, 0, 128, 0.5)',
  labelBg: 'rgba(255, 0, 128, 0.95)',
  labelText: '#FFFFFF',
} as const;

// SD Bands
export const SD_BANDS = {
  color: '#787B86',
  opacity: {
    '2sd': 0.08,
    '1.5sd': 0.10,
    '1sd': 0.12,
  },
} as const;

// Helper Functions
export const getWallColors = (type: 'call' | 'put', strength: number) => {
  const colors = type === 'call' ? CALL_WALL_COLORS : PUT_WALL_COLORS;

  if (strength > 70) return colors.strong;
  if (strength > 40) return colors.medium;
  return colors.weak;
};

export const getTimeframeOpacity = (timeframe: '14D' | '30D' | '90D', strength: number): number => {
  const base = {
    '14D': 0.35,
    '30D': 0.25,
    '90D': 0.15,
  }[timeframe];

  // Strength multiplier
  const multiplier = strength < 40 ? 0.7 : strength > 70 ? 1.2 : 1.0;

  return Math.min(base * multiplier, 1.0);
};

export const getBorderWidth = (timeframe: '14D' | '30D' | '90D'): number => {
  return { '14D': 3, '30D': 2, '90D': 1 }[timeframe];
};

export const formatGEX = (gex: number): string => {
  const abs = Math.abs(gex);
  if (abs >= 1000) return `$${(gex / 1000).toFixed(1)}B`;
  return `$${gex.toFixed(1)}M`;
};

export const formatPrice = (price: number): string => {
  if (price >= 10000) return `$${(price / 1000).toFixed(1)}K`;
  if (price >= 1000) return `$${price.toLocaleString('en-US', { maximumFractionDigits: 0 })}`;
  return `$${price.toFixed(2)}`;
};
