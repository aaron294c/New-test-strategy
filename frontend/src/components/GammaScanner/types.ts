/**
 * Type definitions for Gamma Wall Scanner
 * Matches the Python script output format and TradingView indicator structure
 */

// Field index mapping from Python script (36 fields total)
export const FIELD_MAPPING = {
  ST_PUT_WALL: 0,           // Short-term put wall strike
  ST_CALL_WALL: 1,          // Short-term call wall strike
  LT_PUT_WALL: 2,           // Long-term put wall strike
  LT_CALL_WALL: 3,          // Long-term call wall strike
  LOWER_1SD: 4,             // Lower 1 standard deviation
  UPPER_1SD: 5,             // Upper 1 standard deviation
  GAMMA_SUPPORT: 6,         // Gamma support level (duplicate ST_PUT_WALL)
  GAMMA_RESISTANCE: 7,      // Gamma resistance level (duplicate ST_CALL_WALL)
  GAMMA_FLIP: 8,            // Real gamma flip point
  SWING_IV: 9,              // Swing timeframe IV %
  CP_RATIO: 10,             // Call/Put ratio
  TREND: 11,                // Trend indicator
  ACTIVITY_SCORE: 12,       // Activity score (0-5)
  ST_PUT_WALL_DUP: 13,      // Duplicate
  ST_CALL_WALL_DUP: 14,     // Duplicate
  LOWER_1_5SD: 15,          // Lower 1.5 standard deviation
  UPPER_1_5SD: 16,          // Upper 1.5 standard deviation
  LOWER_2SD: 17,            // Lower 2 standard deviation
  UPPER_2SD: 18,            // Upper 2 standard deviation
  Q_PUT_WALL: 19,           // Quarterly put wall
  Q_CALL_WALL: 20,          // Quarterly call wall
  ST_PUT_STRENGTH: 21,      // Short-term put strength (0-100)
  ST_CALL_STRENGTH: 22,     // Short-term call strength (0-100)
  LT_PUT_STRENGTH: 23,      // Long-term put strength (0-100)
  LT_CALL_STRENGTH: 24,     // Long-term call strength (0-100)
  Q_PUT_STRENGTH: 25,       // Quarterly put strength (0-100)
  Q_CALL_STRENGTH: 26,      // Quarterly call strength (0-100)
  ST_DTE: 27,               // Short-term days to expiration
  LT_DTE: 28,               // Long-term days to expiration
  Q_DTE: 29,                // Quarterly days to expiration
  ST_PUT_GEX: 30,           // Short-term put GEX (millions)
  ST_CALL_GEX: 31,          // Short-term call GEX (millions)
  LT_PUT_GEX: 32,           // Long-term put GEX (millions)
  LT_CALL_GEX: 33,          // Long-term call GEX (millions)
  Q_PUT_GEX: 34,            // Quarterly put GEX (millions)
  Q_CALL_GEX: 35,           // Quarterly call GEX (millions)
} as const;

export interface GammaWall {
  strike: number;
  strength: number;
  gex: number;
  dte: number;
  type: 'put' | 'call';
  timeframe: 'swing' | 'long' | 'quarterly';
}

export interface StandardDeviationBands {
  lower_1sd: number;
  upper_1sd: number;
  lower_1_5sd: number;
  upper_1_5sd: number;
  lower_2sd: number;
  upper_2sd: number;
}

export interface ParsedSymbolData {
  symbol: string;
  displayName: string;
  currentPrice: number;

  // Gamma walls
  walls: GammaWall[];

  // Standard deviation bands
  sdBands: StandardDeviationBands;

  // Gamma flip point
  gammaFlip: number;

  // Market metrics
  swingIV: number;      // IV percentage for swing timeframe
  longIV?: number;      // Calculated based on DTE
  quarterlyIV?: number; // Calculated based on DTE
  cpRatio: number;
  trend: number;
  activityScore: number;

  // Days to expiration
  stDte: number;
  ltDte: number;
  qDte: number;
}

export interface GammaDataResponse {
  level_data: string[];
  last_update: string;
  market_regime: string;
  current_vix: number;
  regime_adjustment_enabled: boolean;
}

export interface ParseError {
  line: number;
  symbol: string;
  message: string;
  fieldIndex?: number;
}

export interface GammaScannerSettings {
  // Symbol selection
  selectedSymbols: string[];

  // Wall display toggles
  showSwingWalls: boolean;
  showLongWalls: boolean;
  showQuarterlyWalls: boolean;
  showGammaFlip: boolean;
  showSDBands: boolean;

  // Visual options
  showLabels: boolean;
  showTable: boolean;
  wallOpacity: number;
  colorScheme: 'default' | 'high-contrast' | 'colorblind';

  // Data source
  dataSource: 'api' | 'manual';
  apiPollingInterval: number; // seconds

  // Regime adjustment
  applyRegimeAdjustment: boolean;

  // Filters
  minStrength: number;
  hideWeakWalls: boolean;
}

export interface MarketRegime {
  regime: string;
  vix: number;
  bgColor: string;
  adjustmentEnabled: boolean;
}

export interface ChartDataPoint {
  timestamp: number;
  price: number;
  symbol: string;
}

// Color scheme definitions
export const COLOR_SCHEMES = {
  default: {
    swingPut: '#FF4444',
    swingCall: '#44FF44',
    longPut: '#FF8844',
    longCall: '#4488FF',
    quarterlyPut: '#BB44FF',
    quarterlyCall: '#FFBB44',
    gammaFlip: '#FF8800',
    sdBands: '#888888',
  },
  'high-contrast': {
    swingPut: '#FF0000',
    swingCall: '#00FF00',
    longPut: '#FF6600',
    longCall: '#0066FF',
    quarterlyPut: '#9900FF',
    quarterlyCall: '#FFAA00',
    gammaFlip: '#FF6600',
    sdBands: '#666666',
  },
  colorblind: {
    swingPut: '#E69F00',
    swingCall: '#56B4E9',
    longPut: '#F0E442',
    longCall: '#0072B2',
    quarterlyPut: '#D55E00',
    quarterlyCall: '#CC79A7',
    gammaFlip: '#009E73',
    sdBands: '#999999',
  },
} as const;

export type ColorScheme = keyof typeof COLOR_SCHEMES;
