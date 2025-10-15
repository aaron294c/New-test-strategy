import React, { useEffect, useState } from 'react';
import axios from 'axios';

interface PercentileRange {
  min: number;
  p10?: number;
  p25: number;
  median: number;
  p75: number;
  p90?: number;
  max: number;
}

interface CategoryDistribution {
  count: number;
  daily_range: PercentileRange;
  '4h_range': PercentileRange;
  divergence_range: PercentileRange;
}

interface PerformanceByStrength {
  count: number;
  avg_return_d7: number;
  sharpe: number;
  win_rate: number;
}

interface OptimalThresholds {
  weak_threshold?: number;
  moderate_threshold?: number;
  strong_threshold?: number;
}

interface CategoryThresholds {
  count: number;
  daily_percentile_range: PercentileRange;
  '4h_percentile_range': PercentileRange;
  divergence_range: PercentileRange;
  optimal_thresholds: OptimalThresholds;
  performance_by_strength: {
    weak?: PerformanceByStrength;
    moderate?: PerformanceByStrength;
    strong?: PerformanceByStrength;
  };
  expectation: string;
}

interface DecisionMatrixRow {
  Daily_Range: string;
  '4H_Range': string;
  Avg_Divergence: number;
  Category: string;
  Recommended_Action: string;
  Sample_Size: number;
  Avg_Return_D7: number;
  Avg_Return_D14: number;
  Win_Rate_D7: number;
  Best_Return_D7: number;
  Worst_Return_D7: number;
}

interface GridAnalysisRow {
  daily_range: string;
  '4h_range': string;
  count: number;
  avg_divergence: number;
  primary_category: string;
  category_confidence: number;
  avg_return_d1: number;
  avg_return_d3: number;
  avg_return_d7: number;
  avg_return_d14: number;
  win_rate_d7: number;
  best_return_d7: number;
  worst_return_d7: number;
}

interface PercentileThresholdData {
  ticker: string;
  distributions: {
    daily_overall: PercentileRange;
    '4h_overall': PercentileRange;
    by_category: {
      '4h_overextended'?: CategoryDistribution;
      bullish_convergence?: CategoryDistribution;
      daily_overextended?: CategoryDistribution;
      bearish_convergence?: CategoryDistribution;
    };
  };
  optimal_thresholds: {
    '4h_overextended'?: CategoryThresholds;
    bullish_convergence?: CategoryThresholds;
    daily_overextended?: CategoryThresholds;
    bearish_convergence?: CategoryThresholds;
  };
  decision_matrix: DecisionMatrixRow[];
  grid_analysis: GridAnalysisRow[];
  timestamp: string;
}

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

export const PercentileThresholdAnalysis: React.FC<{ ticker: string }> = ({ ticker }) => {
  const [data, setData] = useState<PercentileThresholdData | null>(null);
  const [convergenceData, setConvergenceData] = useState<any>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchData = async () => {
      setLoading(true);
      setError(null);

      try {
        const [thresholdResponse, convergenceResponse] = await Promise.all([
          axios.get(`${API_BASE_URL}/api/percentile-thresholds/${ticker}`),
          axios.get(`${API_BASE_URL}/api/convergence-analysis/${ticker}`)
        ]);

        setData(thresholdResponse.data);
        setConvergenceData(convergenceResponse.data.convergence_analysis);
      } catch (err: any) {
        setError(err.response?.data?.detail || err.message || 'Failed to fetch data');
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, [ticker]);

  if (loading) {
    return (
      <div className="p-8 bg-gray-800 rounded-lg">
        <div className="text-center">
          <div className="animate-spin rounded-full h-16 w-16 border-b-4 border-blue-500 mx-auto"></div>
          <p className="mt-4 text-lg text-gray-300">Analyzing percentile thresholds...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="p-6 bg-red-900 rounded-lg border-2 border-red-700">
        <h3 className="text-2xl font-bold text-red-200 mb-2">⚠️ Error</h3>
        <p className="text-red-300">{error}</p>
      </div>
    );
  }

  if (!data) {
    return null;
  }

  const categoryInfo = {
    bullish_convergence: {
      name: '📈 Bullish Convergence',
      shortName: 'BUY SIGNAL',
      description: 'Both Daily & 4H oversold and aligned',
      action: '🎯 Buy/Add Position',
      color: 'from-green-900 to-green-800',
      borderColor: 'border-green-600',
      icon: '🟢'
    },
    '4h_overextended': {
      name: '⚠️ 4H Overextended',
      shortName: 'TAKE PROFIT',
      description: '4H spiked while Daily still low',
      action: '💰 Take Profits',
      color: 'from-orange-900 to-orange-800',
      borderColor: 'border-orange-600',
      icon: '🟠'
    },
    daily_overextended: {
      name: '🔴 Daily Overextended',
      shortName: 'REVERSAL',
      description: 'Daily high but 4H not confirming',
      action: '⬇️ Reduce/Exit',
      color: 'from-red-900 to-red-800',
      borderColor: 'border-red-600',
      icon: '🔴'
    },
    bearish_convergence: {
      name: '⛔ Bearish Convergence',
      shortName: 'EXIT SIGNAL',
      description: 'Both Daily & 4H overbought and aligned',
      action: '🚪 Exit All/Short',
      color: 'from-purple-900 to-purple-800',
      borderColor: 'border-purple-600',
      icon: '🟣'
    }
  };

  return (
    <div className="space-y-8 pb-8">
      {/* Hero Header */}
      <div className="bg-gradient-to-br from-blue-900 via-purple-900 to-indigo-900 p-8 rounded-xl shadow-2xl border-2 border-blue-700">
        <h2 className="text-4xl font-bold text-white mb-3">
          📊 Percentile Threshold Decision Matrix
        </h2>
        <div className="flex items-center justify-between">
          <div>
            <p className="text-xl text-gray-200 mb-2">
              {data.ticker} - Historical Analysis
            </p>
            <p className="text-sm text-gray-400">
              IF Daily = X% AND 4H = Y% → THEN Action (with historical performance)
            </p>
          </div>
          <div className="text-right">
            <div className="text-3xl font-bold text-yellow-400">
              {data.decision_matrix.length}
            </div>
            <div className="text-sm text-gray-300">Decision Rules</div>
          </div>
        </div>
      </div>

      {/* Convergence Prediction Section */}
      {convergenceData && convergenceData.current_state?.is_overextended && convergenceData.current_state?.prediction && (
        <div className="bg-gradient-to-br from-purple-900 via-blue-900 to-indigo-900 p-8 rounded-xl shadow-2xl border-2 border-purple-600 mb-8">
          <h3 className="text-3xl font-bold text-white mb-4 flex items-center gap-3">
            🔮 Convergence Prediction - Mid-Cycle Analysis
          </h3>
          <p className="text-gray-200 mb-6">
            System detected an <strong>overextension event</strong>. Predicting time to convergence based on {convergenceData.current_state.prediction.similar_historical_events} similar historical patterns.
          </p>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="bg-black bg-opacity-40 p-6 rounded-xl border border-purple-400">
              <div className="text-purple-300 text-sm mb-2 font-semibold">Current Divergence</div>
              <div className={`text-4xl font-bold ${convergenceData.current_state.current_divergence_pct > 0 ? 'text-red-400' : 'text-green-400'}`}>
                {convergenceData.current_state.current_divergence_pct > 0 ? '+' : ''}
                {convergenceData.current_state.current_divergence_pct.toFixed(1)}%
              </div>
              <div className="text-gray-300 text-xs mt-2">
                {convergenceData.current_state.direction === '4h_high' ? '4H above Daily' : '4H below Daily'}
              </div>
            </div>

            <div className="bg-black bg-opacity-40 p-6 rounded-xl border border-blue-400">
              <div className="text-blue-300 text-sm mb-2 font-semibold">Predicted Convergence Time</div>
              <div className="text-4xl font-bold text-blue-400">
                {convergenceData.current_state.prediction.predicted_hours_to_convergence.toFixed(0)}h
              </div>
              <div className="text-gray-300 text-xs mt-2">
                Confidence: {(convergenceData.current_state.prediction.confidence * 100).toFixed(0)}%
              </div>
            </div>

            <div className="bg-black bg-opacity-40 p-6 rounded-xl border border-yellow-400">
              <div className="text-yellow-300 text-sm mb-2 font-semibold">Stability Window</div>
              <div className="text-2xl font-bold text-yellow-400">
                {convergenceData.current_state.prediction.stability_window_hours[0].toFixed(0)}-
                {convergenceData.current_state.prediction.stability_window_hours[1].toFixed(0)}h
              </div>
              <div className="text-gray-300 text-xs mt-2">
                80% of events converge in this range
              </div>
            </div>
          </div>

          <div className="mt-6 bg-black bg-opacity-30 p-4 rounded-lg">
            <div className="text-white font-semibold mb-2">📊 Insights:</div>
            <ul className="space-y-1">
              {convergenceData.insights?.map((insight: string, idx: number) => (
                <li key={idx} className="text-gray-200 text-sm">• {insight}</li>
              ))}
            </ul>
          </div>
        </div>
      )}

      {/* Quick Reference Cards */}
      <div>
        <h3 className="text-2xl font-bold text-white mb-4 flex items-center gap-2">
          🎯 Quick Reference: What To Do Now
        </h3>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          {Object.entries(categoryInfo).map(([key, info]) => {
            const thresholds = data.optimal_thresholds[key as keyof typeof data.optimal_thresholds];
            if (!thresholds) return null;

            return (
              <div
                key={key}
                className={`bg-gradient-to-br ${info.color} p-5 rounded-xl shadow-lg border-2 ${info.borderColor} hover:scale-105 transition-transform`}
              >
                <div className="text-3xl mb-2">{info.icon}</div>
                <h4 className="text-lg font-bold text-white mb-1">{info.shortName}</h4>
                <p className="text-xs text-gray-300 mb-3">{info.description}</p>
                <div className="bg-black bg-opacity-30 p-3 rounded-lg mb-3">
                  <div className="text-xs text-gray-400 mb-1">Typical Daily Range:</div>
                  <div className="text-lg font-mono font-bold text-yellow-400">
                    {thresholds.daily_percentile_range.p25.toFixed(0)}-
                    {thresholds.daily_percentile_range.p75.toFixed(0)}%
                  </div>
                </div>
                <div className="text-sm font-semibold text-white text-center py-2 bg-black bg-opacity-40 rounded">
                  {info.action}
                </div>
                <div className="mt-3 text-xs text-center text-gray-400">
                  {thresholds.count} historical events
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* Decision Matrix - Main Section */}
      <div className="bg-gradient-to-br from-gray-900 to-gray-800 p-8 rounded-2xl shadow-2xl border border-gray-700">
        <h3 className="text-4xl font-bold text-white mb-8 flex items-center gap-4">
          📋 Complete Decision Matrix
          <span className="text-base font-normal text-gray-400 bg-gray-800 px-4 py-2 rounded-lg">(All Percentile Combinations)</span>
        </h3>

        <div className="space-y-8">
          {Object.entries(categoryInfo).map(([key, info]) => {
            const categoryData = data.decision_matrix.filter(
              (row) => row.Category === key
            );

            if (categoryData.length === 0) return null;

            return (
              <div
                key={key}
                className={`bg-gradient-to-br ${info.color} p-8 rounded-2xl shadow-2xl border-2 ${info.borderColor} hover:shadow-3xl transition-all duration-300`}
              >
                <div className="flex items-center justify-between mb-6 pb-6 border-b-2 border-white border-opacity-30">
                  <div className="flex items-center gap-4">
                    <div className="text-5xl">{info.icon}</div>
                    <div>
                      <h4 className="text-3xl font-bold text-white flex items-center gap-3">
                        {info.name}
                      </h4>
                      <p className="text-base text-gray-100 mt-2 font-medium">{info.description}</p>
                    </div>
                  </div>
                  <div className="text-right bg-black bg-opacity-30 px-6 py-4 rounded-xl">
                    <div className="text-3xl font-bold text-yellow-300">{info.action}</div>
                    <div className="text-sm text-gray-300 mt-2">{categoryData.length} scenarios available</div>
                  </div>
                </div>

                <div className="overflow-x-auto rounded-xl">
                  <table className="w-full">
                    <thead>
                      <tr className="bg-black bg-opacity-50 backdrop-blur">
                        <th className="text-left p-5 text-white font-bold text-base border-b-2 border-white border-opacity-20">
                          <div className="flex items-center gap-2">
                            <span className="text-blue-400">📊</span> IF: Daily %
                          </div>
                        </th>
                        <th className="text-left p-5 text-white font-bold text-base border-b-2 border-white border-opacity-20">
                          <div className="flex items-center gap-2">
                            <span className="text-purple-400">⏰</span> IF: 4H %
                          </div>
                        </th>
                        <th className="text-center p-5 text-white font-bold text-base border-b-2 border-white border-opacity-20">
                          <div className="flex items-center justify-center gap-2">
                            <span className="text-yellow-400">⚡</span> THEN: Action
                          </div>
                        </th>
                        <th className="text-right p-5 text-white font-bold text-base border-b-2 border-white border-opacity-20">
                          <div className="flex items-center justify-end gap-2">
                            <span className="text-green-400">💰</span> Avg Return
                          </div>
                          <div className="text-xs font-normal text-gray-300 mt-1">(after 7 days)</div>
                        </th>
                        <th className="text-right p-5 text-white font-bold text-base border-b-2 border-white border-opacity-20">
                          <div className="flex items-center justify-end gap-2">
                            <span className="text-blue-400">🎯</span> Win Rate
                          </div>
                          <div className="text-xs font-normal text-gray-300 mt-1">(% profitable)</div>
                        </th>
                        <th className="text-center p-5 text-white font-bold text-base border-b-2 border-white border-opacity-20">
                          <div className="flex items-center justify-center gap-2">
                            <span className="text-gray-400">📈</span> Sample
                          </div>
                          <div className="text-xs font-normal text-gray-300 mt-1">(# trades)</div>
                        </th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-white divide-opacity-10">
                      {categoryData.map((row, idx) => (
                        <tr
                          key={idx}
                          className="hover:bg-white hover:bg-opacity-10 transition-all duration-200"
                        >
                          <td className="p-5">
                            <div className="bg-blue-600 bg-opacity-40 px-5 py-3 rounded-xl inline-block border-2 border-blue-400 shadow-lg">
                              <div className="text-2xl font-mono font-bold text-white">{row.Daily_Range}</div>
                            </div>
                          </td>
                          <td className="p-5">
                            <div className="bg-purple-600 bg-opacity-40 px-5 py-3 rounded-xl inline-block border-2 border-purple-400 shadow-lg">
                              <div className="text-2xl font-mono font-bold text-white">{row['4H_Range']}</div>
                            </div>
                          </td>
                          <td className="p-5 text-center">
                            <div className="bg-yellow-500 px-5 py-3 rounded-xl inline-block shadow-xl border-2 border-yellow-400">
                              <div className="text-lg font-bold text-black">{row.Recommended_Action}</div>
                            </div>
                          </td>
                          <td className="p-5 text-right">
                            <div className={`text-4xl font-mono font-bold ${
                              row.Avg_Return_D7 > 0 ? 'text-green-300' : 'text-red-300'
                            }`}>
                              {row.Avg_Return_D7 > 0 ? '+' : ''}{row.Avg_Return_D7.toFixed(2)}%
                            </div>
                            <div className="text-sm text-gray-300 mt-2 font-medium">
                              Range: <span className="text-green-300 font-bold">+{row.Best_Return_D7.toFixed(1)}%</span> to <span className="text-red-300 font-bold">{row.Worst_Return_D7.toFixed(1)}%</span>
                            </div>
                          </td>
                          <td className="p-5 text-right">
                            <div className="text-4xl font-mono font-bold text-blue-300">
                              {row.Win_Rate_D7.toFixed(0)}%
                            </div>
                            <div className="text-sm mt-2 font-semibold">
                              {row.Win_Rate_D7 >= 60 ? (
                                <span className="text-green-300 bg-green-900 bg-opacity-30 px-3 py-1 rounded-full">✅ High Confidence</span>
                              ) : row.Win_Rate_D7 >= 40 ? (
                                <span className="text-yellow-300 bg-yellow-900 bg-opacity-30 px-3 py-1 rounded-full">⚠️ Medium</span>
                              ) : (
                                <span className="text-red-300 bg-red-900 bg-opacity-30 px-3 py-1 rounded-full">❌ Low</span>
                              )}
                            </div>
                          </td>
                          <td className="p-5 text-center">
                            <div className="text-3xl font-bold text-gray-200">{row.Sample_Size}</div>
                            <div className="text-sm text-gray-400 mt-1 font-medium">events</div>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* Top Performing Setups */}
      <div className="bg-gradient-to-br from-gray-900 to-gray-800 p-8 rounded-2xl shadow-2xl border border-gray-700">
        <h3 className="text-4xl font-bold text-white mb-8 flex items-center gap-4">
          ⭐ Top Performing Setups
          <span className="text-base font-normal text-gray-400 bg-gray-800 px-4 py-2 rounded-lg">(Highest Sample Size)</span>
        </h3>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {data.grid_analysis.slice(0, 9).map((row, idx) => {
            const info = categoryInfo[row.primary_category.replace(' ', '_') as keyof typeof categoryInfo];
            if (!info) return null;

            return (
              <div
                key={idx}
                className={`bg-gradient-to-br ${info.color} p-6 rounded-2xl border-2 ${info.borderColor} hover:scale-105 hover:shadow-2xl transition-all duration-300 shadow-xl`}
              >
                <div className="flex items-center justify-between mb-4">
                  <div className="text-4xl drop-shadow-lg">{info.icon}</div>
                  <div className="text-sm bg-black bg-opacity-50 px-3 py-2 rounded-lg text-gray-200 font-bold border border-white border-opacity-20">
                    n={row.count}
                  </div>
                </div>

                <div className="mb-4">
                  <div className="flex gap-2 mb-3">
                    <span className="bg-black bg-opacity-50 px-3 py-2 rounded-lg text-white font-mono text-base font-bold border border-blue-400">
                      D: {row.daily_range}
                    </span>
                    <span className="bg-black bg-opacity-50 px-3 py-2 rounded-lg text-white font-mono text-base font-bold border border-purple-400">
                      4H: {row['4h_range']}
                    </span>
                  </div>
                  <div className="text-sm text-gray-100 font-medium leading-relaxed">{info.description}</div>
                </div>

                <div className="bg-black bg-opacity-50 p-4 rounded-xl space-y-3 backdrop-blur border border-white border-opacity-10">
                  <div className="flex justify-between items-center">
                    <span className="text-gray-200 text-sm font-semibold">D7 Return:</span>
                    <span
                      className={`font-mono font-bold text-2xl ${
                        row.avg_return_d7 > 0 ? 'text-green-300' : 'text-red-300'
                      }`}
                    >
                      {row.avg_return_d7 > 0 ? '+' : ''}
                      {row.avg_return_d7.toFixed(2)}%
                    </span>
                  </div>
                  <div className="flex justify-between items-center">
                    <span className="text-gray-200 text-sm font-semibold">Win Rate:</span>
                    <span className="text-blue-300 font-mono font-bold text-xl">
                      {row.win_rate_d7.toFixed(1)}%
                    </span>
                  </div>
                  <div className="flex justify-between items-center">
                    <span className="text-gray-200 text-sm font-semibold">Confidence:</span>
                    <span className="text-yellow-300 font-bold text-xl">
                      {row.category_confidence.toFixed(0)}%
                    </span>
                  </div>
                </div>

                <div className="mt-4 text-center bg-black bg-opacity-30 py-3 rounded-xl">
                  <div className="text-xs text-gray-300 mb-2 font-semibold">Best / Worst Outcome</div>
                  <div className="flex justify-center gap-3 items-center">
                    <span className="text-green-300 font-mono text-base font-bold">
                      +{row.best_return_d7.toFixed(1)}%
                    </span>
                    <span className="text-gray-400 text-lg font-bold">/</span>
                    <span className="text-red-300 font-mono text-base font-bold">
                      {row.worst_return_d7.toFixed(1)}%
                    </span>
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
};
