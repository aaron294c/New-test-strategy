/**
 * Type definitions for RSI-MA Performance Analytics Dashboard
 */

export interface PerformanceCell {
  day: number;
  percentile_range: string;
  sample_size: number;
  expected_cumulative_return: number;
  expected_success_rate: number;
  p25_return: number;
  p75_return: number;
  confidence_level: 'VH' | 'H' | 'M' | 'L' | 'VL';
}

export interface PerformanceMatrix {
  [percentileRange: string]: {
    [day: number]: PerformanceCell;
  };
}

export interface RiskMetrics {
  median_drawdown: number;
  p90_drawdown: number;
  median_recovery_days: number;
  recovery_rate: number;
  max_consecutive_losses: number;
  avg_loss_magnitude: number;
}

export interface ReturnDistribution {
  median: number;
  std: number;
  minus_2sd: number;
  minus_1sd: number;
  plus_1sd: number;
  plus_2sd: number;
  sample_size: number;
}

export interface PercentileMovementDay {
  median_percentile: number;
  mean_percentile: number;
  p25_percentile: number;
  p75_percentile: number;
  median_change_from_entry: number;
  upward_movement_rate: number;
  strong_upward_rate: number;
  sample_size: number;
}

export interface PercentileMovements {
  percentile_by_day: {
    [day: number]: PercentileMovementDay;
  };
  reversion_analysis: {
    median_final_percentile: number;
    median_peak_percentile: number;
    reversion_from_peak: number;
    complete_reversion_rate: number;
  };
}

export interface TrendAnalysis {
  trend_correlation: number;
  trend_p_value: number;
  trend_direction: 'Upward' | 'Downward';
  trend_strength: number;
  peak_day: number;
  peak_return: number;
  early_vs_late_p_value: number;
  early_vs_late_significance: string;
  returns_by_day: {
    [day: number]: number;
  };
}

export interface OptimalExitStrategy {
  optimal_day: number;
  optimal_efficiency: number;
  target_return: number;
  exit_percentile_target: {
    percentile_range: string;
    actual_return: number;
    sample_size: number;
    success_rate: number;
    confidence: string;
  };
  efficiency_rankings: Array<{
    day: number;
    efficiency: number;
    total_return: number;
  }>;
}

export interface TradeManagementRule {
  type: 'Exit Timing' | 'Trend Following' | 'Early Exit Signal' | 'Reversion Protection';
  rule: string;
  confidence: 'High' | 'Medium' | 'Low';
}

export interface ThresholdData {
  events: number;
  performance_matrix: PerformanceMatrix;
  risk_metrics: RiskMetrics;
  win_rates: { [day: number]: number };
  return_distributions: { [day: number]: ReturnDistribution };
  percentile_movements: PercentileMovements;
  trend_analysis: TrendAnalysis;
  trade_management_rules: TradeManagementRule[];
  optimal_exit_strategy: OptimalExitStrategy;
}

export interface MarketBenchmark {
  ticker: string;
  individual_daily_returns: { [day: number]: number };
  cumulative_returns: { [day: number]: number };
  volatility: number;
}

export interface BacktestData {
  ticker: string;
  data_points: number;
  benchmark: MarketBenchmark;
  thresholds: {
    [threshold: string]: ThresholdData;
  };
  verification: {
    last_close: number;
    daily_return_pct: number;
    last_rsi_ma: number;
  };
}

export interface MonteCarloResults {
  ticker: string;
  current_percentile: number;
  current_price: number;
  simulation_results: {
    percentile_paths: number[][];
    percentile_statistics: {
      [day: number]: {
        median: number;
        mean: number;
        std: number;
        p10: number;
        p25: number;
        p75: number;
        p90: number;
        min: number;
        max: number;
      };
    };
    parameters: {
      drift: number;
      volatility: number;
      current_percentile: number;
      current_price: number;
      num_simulations: number;
      max_periods: number;
    };
  };
  first_passage_times: {
    [percentile: string]: {
      target_percentile: number;
      median_days: number;
      p25_days: number;
      p75_days: number;
      probability: number;
    };
  };
  fan_chart: {
    days: number[];
    median: number[];
    bands: {
      [ci: number]: {
        lower: number[];
        upper: number[];
      };
    };
  };
}

export interface ComparisonData {
  [ticker: string]: {
    events: number;
    risk_metrics: RiskMetrics;
    optimal_exit: OptimalExitStrategy;
    win_rates: { [day: number]: number };
    benchmark: MarketBenchmark;
  };
}

// RSI Percentile Chart Data
export interface RSIChartData {
  dates: string[];
  rsi: number[];
  rsi_ma: number[];
  percentile_rank: number[];
  percentile_thresholds: {
    p5: number;
    p15: number;
    p25: number;
    p50: number;
    p75: number;
    p85: number;
    p95: number;
  };
  current_rsi: number;
  current_rsi_ma: number;
  current_percentile: number;
}

// Dashboard state types
export type ThresholdFilter = 5 | 10 | 15;
export type TimeHorizonRange = 'D1-D7' | 'D8-D14' | 'D15-D21' | 'All';
export type ConfidenceLevel = 'VL' | 'L' | 'M' | 'H' | 'VH' | 'All';
export type ChartType = 'heatmap' | 'distribution' | 'percentile' | 'montecarlo';

// Risk Distance Types (v2 - PineScript-inspired calculations)
export interface RiskDistanceLevel {
  strike: number;
  distance_pct: number;     // Positive = above price, Negative = below
  distance_pts: number;
  strength: number;          // 0-95% based on GEX concentration
  dte: number;
  gex_value?: number;        // Raw GEX at this strike
  iv_at_strike?: number;     // IV% at this strike
}

export interface MaxPainData {
  strike: number;
  distance_pct: number;
  distance_pts: number;
  total_pain_value: number;
  call_pain: number;
  put_pain: number;
  timeframe: string;
  pin_risk?: 'HIGH' | 'MEDIUM' | 'LOW';  // Pin risk assessment
  pain_ratio?: number;                    // call_pain / put_pain
}

export interface WeightedWallData {
  max_gex_wall: number;
  weighted_centroid: number;
  cumulative_threshold: number;
  recommended_wall: number;
  method_used: string;
  confidence: 'high' | 'medium' | 'low';
  gex_concentration?: number;  // How concentrated the GEX is at the wall
}

export interface GammaFlipData {
  strike: number;
  distance_pct: number;
  distance_pts: number;
  net_gex_above?: number;   // Net GEX above flip (positive = bullish)
  net_gex_below?: number;   // Net GEX below flip
}

// Daily Trend Scanner (PDH/PDL + PMH/PML)
export interface DailyTrendLevels {
  pmh: number | null;
  pml: number | null;
  pdh: number | null;
  pdl: number | null;
  orb_high?: number | null;
  orb_low?: number | null;
}

export interface DailyTrendCandle {
  time: string; // ISO timestamp
  open: number | null;
  high: number | null;
  low: number | null;
  close: number | null;
  volume: number | null;
}

export interface DailyTrendSymbolData {
  symbol: string;
  as_of: string;
  timezone: string;
  interval: string;
  days: number;
  data_source: string;
  price: number | null;
  prev_close: number | null;
  chg_pct: number | null;
  levels: DailyTrendLevels;
  candles?: DailyTrendCandle[];
}

export interface DailyTrendBatchResponse {
  data: Record<string, DailyTrendSymbolData>;
  errors: Record<string, string>;
  as_of: string;
}

export interface MarketRegime {
  regime: 'High Volatility' | 'Low Volatility' | 'Normal Volatility';
  vix_value: number;
  is_estimated?: boolean;
  strength_multiplier?: number;
}

export interface SDLevels {
  lower_1sd: number;
  upper_1sd: number;
  lower_1_5sd: number;
  upper_1_5sd: number;
  lower_2sd: number;
  upper_2sd: number;
  iv_used: number;
  dte: number;
}

export interface RiskDistanceSummary {
  nearest_support_pct: number;
  nearest_resistance_pct: number;
  risk_reward_ratio: number;
  position_in_range: 'near_support' | 'mid_range' | 'near_resistance';
  recommendation: string;
}

export interface SymbolRiskDistanceData {
  symbol: string;
  current_price: number;
  timestamp: string;
  put_walls: Record<string, RiskDistanceLevel>;
  call_walls: Record<string, RiskDistanceLevel>;
  max_pain: Record<string, MaxPainData>;
  weighted_walls: {
    put?: WeightedWallData;
    call?: WeightedWallData;
  };
  gamma_flip: GammaFlipData | null;
  sd_levels: SDLevels | null;
  regime?: MarketRegime;  // v2: Market regime detection
  summary: RiskDistanceSummary;
}

export interface RiskDistanceSummaryResponse {
  symbol: string;
  current_price: number;
  timestamp: string;
  nearest_support: {
    level: number;
    distance_pct: number;
    strength: number;
    gex_value?: number;
  };
  nearest_resistance: {
    level: number;
    distance_pct: number;
    strength: number;
    gex_value?: number;
  };
  max_pain: Record<
    string,
    {
      strike: number;
      distance_pct: number;
      pin_risk?: 'HIGH' | 'MEDIUM' | 'LOW';
    }
  >;
  gamma_flip: {
    strike: number;
    distance_pct: number;
    net_gex_above?: number;
    net_gex_below?: number;
  };
  weighted_support: {
    recommended_wall: number;
    method_used: string;
    confidence: 'high' | 'medium' | 'low';
  };
  weighted_resistance: {
    recommended_wall: number;
    method_used: string;
    confidence: 'high' | 'medium' | 'low';
  };
  regime: string;
  vix: number;
  sd_levels: SDLevels | null;
  position: string;
  risk_reward: number;
  recommendation: string;
}
