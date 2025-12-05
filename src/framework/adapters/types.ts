/**
 * TypeScript interfaces matching Python backend API responses
 */

// ==================== BACKTEST API RESPONSES ====================

export interface BacktestResponse {
  ticker: string;
  source: 'cache' | 'fresh';
  data: BacktestData;
  timestamp: string;
}

export interface BacktestData {
  thresholds: Record<string, ThresholdData>;
  benchmark?: BenchmarkMetrics;
  summary?: BacktestSummary;
}

export interface ThresholdData {
  performance_matrix: PerformanceMatrix;
  events: number;
  win_rates: WinRateData;
  return_distributions: ReturnDistribution;
  optimal_exit_strategy?: OptimalExitStrategy;
  risk_metrics?: RiskMetrics;
  trend_analysis?: TrendAnalysis;
}

export interface PerformanceMatrix {
  [key: string]: {
    mean: number;
    median: number;
    std: number;
    win_rate: number;
    sample_size: number;
  };
}

export interface WinRateData {
  [day: string]: number;
}

export interface ReturnDistribution {
  [day: string]: {
    percentile_5: number;
    percentile_25: number;
    percentile_50: number;
    percentile_75: number;
    percentile_95: number;
  };
}

export interface OptimalExitStrategy {
  recommended_exit_day: number;
  expected_return: number;
  win_rate: number;
  sharpe_ratio: number;
  return_efficiency: number;
}

export interface RiskMetrics {
  max_drawdown: number;
  sharpe_ratio: number;
  sortino_ratio: number;
  calmar_ratio: number;
  volatility: number;
}

export interface TrendAnalysis {
  momentum_score: number;
  trend_strength: number;
  regime: 'momentum' | 'mean_reversion' | 'neutral';
}

export interface BenchmarkMetrics {
  buy_and_hold_return: number;
  strategy_return: number;
  outperformance: number;
}

export interface BacktestSummary {
  total_trades: number;
  winning_trades: number;
  losing_trades: number;
  win_rate: number;
  avg_win: number;
  avg_loss: number;
  expectancy: number;
}

// ==================== RSI CHART API RESPONSE ====================

export interface RSIChartResponse {
  ticker: string;
  chart_data: RSIChartData;
  timestamp: string;
}

export interface RSIChartData {
  dates: string[];
  prices: number[];
  rsi_values: number[];
  rsi_ma_values: number[];
  percentile_ranks: number[];
  percentile_thresholds: {
    p5: number[];
    p15: number[];
    p25: number[];
    p50: number[];
    p75: number[];
    p85: number[];
    p95: number[];
  };
  current: {
    price: number;
    rsi: number;
    rsi_ma: number;
    percentile: number;
  };
}

// ==================== PERCENTILE FORWARD MAPPING RESPONSE ====================

export interface PercentileForwardResponse {
  ticker: string;
  current_state: {
    current_percentile: number;
    current_rsi_ma: number;
  };
  prediction: PercentilePrediction;
  bin_stats: BinStatistics;
  transition_matrices: TransitionMatrices;
  backtest_results: BacktestResult[];
  accuracy_metrics: AccuracyMetrics;
  model_bin_mappings?: ModelBinMappings;
  timestamp: string;
  cached?: boolean;
  cache_age_hours?: number;
}

export interface PercentilePrediction {
  // Ensemble forecasts
  ensemble_forecast_1d?: number;
  ensemble_forecast_5d?: number;
  ensemble_forecast_10d?: number;
  ensemble_forecast_21d?: number;

  // Individual model forecasts
  empirical_forecast_1d?: number;
  linear_forecast_1d?: number;
  polynomial_forecast_1d?: number;
  quantile_forecast_1d?: number;
  kernel_forecast_1d?: number;

  // Bin statistics
  empirical_bin_stats?: {
    mean_return_1d: number;
    median_return_1d: number;
    std_return_1d: number;
    pct_5_return_1d: number;
    pct_95_return_1d: number;
  };
}

export interface BinStatistics {
  [binRange: string]: {
    mean_1d: number;
    median_1d: number;
    std_1d: number;
    sample_size: number;
    pct_5_1d: number;
    pct_95_1d: number;
  };
}

export interface TransitionMatrices {
  [horizon: string]: number[][];
}

export interface BacktestResult {
  date: string;
  actual_return: number;
  ensemble_forecast: number;
  error: number;
  hit: boolean;
}

export interface AccuracyMetrics {
  [horizon: string]: {
    hit_rate: number;
    sharpe: number;
    mae: number;
    rmse: number;
    information_ratio?: number;
  };
}

export interface ModelBinMappings {
  empirical?: Record<string, number>;
  linear?: Record<string, number>;
  polynomial?: Record<string, number>;
  quantile?: Record<string, number>;
  kernel?: Record<string, number>;
  ensemble?: Record<string, number>;
}

// ==================== MONTE CARLO SIMULATION RESPONSE ====================

export interface MonteCarloResponse {
  ticker: string;
  current_percentile: number;
  current_price: number;
  simulation_results: MonteCarloResults;
  timestamp: string;
}

export interface MonteCarloResults {
  simulations: SimulationPath[];
  statistics: {
    mean_path: number[];
    median_path: number[];
    percentile_5: number[];
    percentile_25: number[];
    percentile_75: number[];
    percentile_95: number[];
  };
  target_probabilities: {
    [targetPercentile: number]: {
      probability: number;
      avg_periods: number;
    };
  };
}

export interface SimulationPath {
  path_id: number;
  returns: number[];
  final_percentile: number;
  periods_to_target?: number;
}

// ==================== LIVE SIGNAL RESPONSE ====================

export interface LiveSignalResponse {
  ticker: string;
  current_state: {
    price: number;
    percentile: number;
    rsi_ma: number;
  };
  signal: {
    strength: 'strong_buy' | 'buy' | 'neutral' | 'avoid' | 'sell' | 'strong_sell';
    confidence: number;
    direction: 'long' | 'short' | 'none';
  };
  expected_returns: {
    '7d': number;
    '14d': number;
    '21d': number;
  };
  position_size: {
    recommended: number;
    max_risk: number;
  };
  reasoning: string[];
  risk_factors: string[];
  timestamp: string;
}

// ==================== MULTI-TIMEFRAME ANALYSIS RESPONSE ====================

export interface MultiTimeframeResponse {
  ticker: string;
  analysis: MultiTimeframeAnalysis;
  timestamp: string;
}

export interface MultiTimeframeAnalysis {
  current_divergence: {
    state: 'overextended_4h' | 'bullish_convergence' | 'overextended_daily' | 'bearish_convergence' | 'neutral';
    daily_percentile: number;
    fourh_percentile: number;
    gap: number;
    recommendation: string;
  };
  divergence_events: DivergenceEvent[];
  statistics_by_type: {
    [type: string]: DivergenceStatistics;
  };
}

export interface DivergenceEvent {
  date: string;
  type: string;
  daily_percentile: number;
  fourh_percentile: number;
  gap: number;
  forward_returns: {
    '1d': number;
    '2d': number;
    '7d': number;
  };
}

export interface DivergenceStatistics {
  count: number;
  avg_return_1d: number;
  avg_return_7d: number;
  win_rate_1d: number;
  sharpe_ratio?: number;
}

// ==================== ERROR RESPONSE ====================

export interface APIError {
  detail: string;
  status_code?: number;
}

// ==================== REQUEST TYPES ====================

export interface BacktestRequest {
  tickers?: string[];
  lookback_period?: number;
  rsi_length?: number;
  ma_length?: number;
  max_horizon?: number;
}

export interface MonteCarloRequest {
  ticker: string;
  num_simulations?: number;
  max_periods?: number;
  target_percentiles?: number[];
}

export interface ExitSignalRequest {
  ticker: string;
  entry_price: number;
  entry_date: string;
}
