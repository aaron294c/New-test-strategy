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

export interface ThresholdData {
  events: number;
  performance_matrix: PerformanceMatrix;
  risk_metrics: RiskMetrics;
  win_rates: { [day: number]: number };
  return_distributions: { [day: number]: ReturnDistribution };
  percentile_movements: PercentileMovements;
  trend_analysis: TrendAnalysis;
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
