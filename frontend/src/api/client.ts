/**
 * API Client for RSI-MA Performance Analytics Backend
 */

import axios from 'axios';
import type {
  BacktestData,
  MonteCarloResults,
  ComparisonData,
  PerformanceMatrix,
  OptimalExitStrategy,
  RSIChartData,
  SymbolRiskDistanceData,
  RiskDistanceSummaryResponse,
  DailyTrendBatchResponse,
  DailyTrendSymbolData,
} from '@/types';

// Default to same-origin so:
// - in dev: Vite proxies `/api` to the backend (see `vite.config.ts`)
// - in prod: you can deploy frontend+backend under the same domain
// If your backend is on a different host, set `VITE_API_URL`.
const API_BASE_URL = import.meta.env.VITE_API_URL || '';

// Debug log (remove after confirming it works)
console.log('API_BASE_URL:', API_BASE_URL);

const apiClient = axios.create({
  baseURL: API_BASE_URL,
  timeout: 120000, // 2 minutes for long-running backtests
  headers: {
    'Content-Type': 'application/json',
  },
});

export interface BacktestRequest {
  tickers: string[];
  lookback_period?: number;
  rsi_length?: number;
  ma_length?: number;
  max_horizon?: number;
}

export interface MonteCarloRequest {
  num_simulations?: number;
  max_periods?: number;
  target_percentiles?: number[];
}

export interface ComparisonRequest {
  tickers: string[];
  threshold: number;
}

/**
 * Backtest API calls
 */
export const backtestApi = {
  /**
   * Get backtest results for a single ticker
   */
  getBacktestResults: async (ticker: string, forceRefresh = false): Promise<BacktestData> => {
    const response = await apiClient.get(`/api/backtest/${ticker}`, {
      params: { force_refresh: forceRefresh },
    });
    return response.data.data;
  },

  /**
   * Run batch backtest for multiple tickers
   */
  runBatchBacktest: async (request: BacktestRequest): Promise<Record<string, BacktestData>> => {
    const response = await apiClient.post('/api/backtest/batch', request);
    return response.data.results;
  },

  /**
   * Get performance matrix for specific ticker and threshold
   */
  getPerformanceMatrix: async (ticker: string, threshold: number): Promise<{
    matrix: PerformanceMatrix;
    events: number;
    win_rates: { [day: number]: number };
    return_distributions: any;
  }> => {
    const response = await apiClient.get(`/api/performance-matrix/${ticker}/${threshold}`);
    return response.data;
  },

  /**
   * Get optimal exit strategy
   */
  getOptimalExitStrategy: async (ticker: string, threshold: number): Promise<{
    optimal_exit_strategy: OptimalExitStrategy;
    risk_metrics: any;
    trend_analysis: any;
  }> => {
    const response = await apiClient.get(`/api/optimal-exit/${ticker}/${threshold}`);
    return response.data;
  },

  /**
   * Get RSI percentile chart data
   */
  getRSIChartData: async (ticker: string, days: number = 252): Promise<RSIChartData> => {
    const response = await apiClient.get(`/api/rsi-chart/${ticker}`, {
      params: { days },
    });
    return response.data.chart_data;
  },
};

/**
 * Monte Carlo simulation API calls
 */
export const monteCarloApi = {
  /**
   * Run Monte Carlo simulation
   */
  runSimulation: async (ticker: string, request: MonteCarloRequest = {}): Promise<MonteCarloResults> => {
    const response = await apiClient.post(`/api/monte-carlo/${ticker}`, request);
    return response.data;
  },
};

/**
 * Comparison API calls
 */
export const comparisonApi = {
  /**
   * Compare multiple tickers
   */
  compareTickers: async (request: ComparisonRequest): Promise<ComparisonData> => {
    const response = await apiClient.post('/api/compare', request);
    return response.data.comparison;
  },
};

/**
 * Utility API calls
 */
export const utilityApi = {
  /**
   * Get available tickers
   */
  getAvailableTickers: async (): Promise<{
    default_tickers: string[];
    cached_tickers: string[];
  }> => {
    const response = await apiClient.get('/api/tickers');
    return response.data;
  },

  /**
   * Health check
   */
  healthCheck: async (): Promise<boolean> => {
    try {
      const response = await apiClient.get('/api/health');
      return response.data.status === 'healthy';
    } catch {
      return false;
    }
  },
};

/**
 * Risk distance API calls
 */
export const riskDistanceApi = {
  /**
   * Get comprehensive risk distance data for a symbol
   */
  getRiskDistance: async (symbol: string): Promise<SymbolRiskDistanceData> => {
    const response = await apiClient.get(`/api/risk-distance/${symbol}`);
    return response.data.data;
  },

  /**
   * Get risk distance data for multiple symbols
   */
  getBatchRiskDistances: async (
    symbols: string[]
  ): Promise<Record<string, SymbolRiskDistanceData>> => {
    const response = await apiClient.post('/api/risk-distance/batch', { symbols });
    return response.data.data;
  },

  /**
   * Get condensed risk distance summary for a symbol
   */
  getRiskDistanceSummary: async (symbol: string): Promise<RiskDistanceSummaryResponse> => {
    const response = await apiClient.get(`/api/risk-distance/${symbol}/summary`);
    return response.data.data;
  },
};

/**
 * Daily Trend Scanner API calls
 */
export const dailyTrendApi = {
  getDailyTrend: async (
    symbol: string,
    params: {
      interval?: string;
      days?: number;
      orb_minutes?: number;
      include_candles?: boolean;
    } = {}
  ): Promise<DailyTrendSymbolData> => {
    const response = await apiClient.get(`/api/daily-trend/${encodeURIComponent(symbol)}`, { params });
    return response.data;
  },

  getDailyTrendBatch: async (request: {
    symbols: string[];
    interval?: string;
    days?: number;
    orb_minutes?: number;
  }): Promise<DailyTrendBatchResponse> => {
    const response = await apiClient.post('/api/daily-trend/batch', request);
    return response.data;
  },
};

export default apiClient;
