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
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchData = async () => {
      setLoading(true);
      setError(null);

      try {
        const response = await axios.get(`${API_BASE_URL}/api/percentile-thresholds/${ticker}`);
        setData(response.data);
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
      <div className="bg-gray-800 p-6 rounded-xl shadow-xl border-2 border-gray-700">
        <h3 className="text-3xl font-bold text-white mb-6 flex items-center gap-3">
          📋 Complete Decision Matrix
          <span className="text-sm font-normal text-gray-400">(All Percentile Combinations)</span>
        </h3>

        {Object.entries(categoryInfo).map(([key, info]) => {
          const categoryData = data.decision_matrix.filter(
            (row) => row.Category === key
          );

          if (categoryData.length === 0) return null;

          return (
            <div
              key={key}
              className={`bg-gradient-to-r ${info.color} p-6 rounded-xl mb-6 shadow-lg border-2 ${info.borderColor}`}
            >
              <div className="flex items-center justify-between mb-4 pb-4 border-b border-white border-opacity-20">
                <div>
                  <h4 className="text-2xl font-bold text-white flex items-center gap-2">
                    {info.icon} {info.name}
                  </h4>
                  <p className="text-sm text-gray-200 mt-1">{info.description}</p>
                </div>
                <div className="text-right">
                  <div className="text-2xl font-bold text-yellow-300">{info.action}</div>
                  <div className="text-xs text-gray-300 mt-1">{categoryData.length} scenarios</div>
                </div>
              </div>

              <div className="overflow-x-auto">
                <table className="w-full">
                  <thead>
                    <tr className="bg-black bg-opacity-40">
                      <th className="text-left p-4 text-white font-bold">IF: Daily %</th>
                      <th className="text-left p-4 text-white font-bold">IF: 4H %</th>
                      <th className="text-center p-4 text-white font-bold">THEN: Action</th>
                      <th className="text-right p-4 text-white font-bold">
                        <div>Avg Return</div>
                        <div className="text-xs font-normal text-gray-400">(after 7 days)</div>
                      </th>
                      <th className="text-right p-4 text-white font-bold">
                        <div>Win Rate</div>
                        <div className="text-xs font-normal text-gray-400">(% profitable)</div>
                      </th>
                      <th className="text-center p-4 text-white font-bold">
                        <div>Sample</div>
                        <div className="text-xs font-normal text-gray-400">(# trades)</div>
                      </th>
                    </tr>
                  </thead>
                  <tbody>
                    {categoryData.map((row, idx) => (
                      <tr
                        key={idx}
                        className="border-b-2 border-white border-opacity-10 hover:bg-white hover:bg-opacity-5"
                      >
                        <td className="p-4">
                          <div className="bg-blue-600 bg-opacity-30 px-4 py-2 rounded-lg inline-block border border-blue-500">
                            <div className="text-2xl font-mono font-bold text-white">{row.Daily_Range}</div>
                          </div>
                        </td>
                        <td className="p-4">
                          <div className="bg-purple-600 bg-opacity-30 px-4 py-2 rounded-lg inline-block border border-purple-500">
                            <div className="text-2xl font-mono font-bold text-white">{row['4H_Range']}</div>
                          </div>
                        </td>
                        <td className="p-4 text-center">
                          <div className="bg-yellow-500 px-4 py-2 rounded-lg inline-block">
                            <div className="text-base font-bold text-black">{row.Recommended_Action}</div>
                          </div>
                        </td>
                        <td className="p-4 text-right">
                          <div className={`text-3xl font-mono font-bold ${
                            row.Avg_Return_D7 > 0 ? 'text-green-400' : 'text-red-400'
                          }`}>
                            {row.Avg_Return_D7 > 0 ? '+' : ''}{row.Avg_Return_D7.toFixed(2)}%
                          </div>
                          <div className="text-xs text-gray-400 mt-1">
                            Range: <span className="text-green-400">+{row.Best_Return_D7.toFixed(1)}%</span> to <span className="text-red-400">{row.Worst_Return_D7.toFixed(1)}%</span>
                          </div>
                        </td>
                        <td className="p-4 text-right">
                          <div className="text-3xl font-mono font-bold text-blue-400">
                            {row.Win_Rate_D7.toFixed(0)}%
                          </div>
                          <div className="text-xs mt-1">
                            {row.Win_Rate_D7 >= 60 ? (
                              <span className="text-green-400">✅ High</span>
                            ) : row.Win_Rate_D7 >= 40 ? (
                              <span className="text-yellow-400">⚠️ Medium</span>
                            ) : (
                              <span className="text-red-400">❌ Low</span>
                            )}
                          </div>
                        </td>
                        <td className="p-4 text-center">
                          <div className="text-2xl font-bold text-gray-300">{row.Sample_Size}</div>
                          <div className="text-xs text-gray-500">events</div>
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

      {/* Top Performing Setups */}
      <div className="bg-gray-800 p-6 rounded-xl shadow-xl border-2 border-gray-700">
        <h3 className="text-3xl font-bold text-white mb-6 flex items-center gap-3">
          ⭐ Top Performing Setups
          <span className="text-sm font-normal text-gray-400">(Highest Sample Size)</span>
        </h3>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {data.grid_analysis.slice(0, 9).map((row, idx) => {
            const info = categoryInfo[row.primary_category.replace(' ', '_') as keyof typeof categoryInfo];
            if (!info) return null;

            return (
              <div
                key={idx}
                className={`bg-gradient-to-br ${info.color} p-5 rounded-xl border-2 ${info.borderColor} hover:scale-105 transition-transform shadow-lg`}
              >
                <div className="flex items-center justify-between mb-3">
                  <div className="text-2xl">{info.icon}</div>
                  <div className="text-xs bg-black bg-opacity-40 px-2 py-1 rounded text-gray-300">
                    n={row.count}
                  </div>
                </div>

                <div className="mb-3">
                  <div className="flex gap-2 mb-2">
                    <span className="bg-black bg-opacity-40 px-2 py-1 rounded text-white font-mono text-sm">
                      D: {row.daily_range}
                    </span>
                    <span className="bg-black bg-opacity-40 px-2 py-1 rounded text-white font-mono text-sm">
                      4H: {row['4h_range']}
                    </span>
                  </div>
                  <div className="text-xs text-gray-300">{info.description}</div>
                </div>

                <div className="bg-black bg-opacity-40 p-3 rounded-lg space-y-2">
                  <div className="flex justify-between items-center">
                    <span className="text-gray-300 text-xs">D7 Return:</span>
                    <span
                      className={`font-mono font-bold text-lg ${
                        row.avg_return_d7 > 0 ? 'text-green-300' : 'text-red-300'
                      }`}
                    >
                      {row.avg_return_d7 > 0 ? '+' : ''}
                      {row.avg_return_d7.toFixed(2)}%
                    </span>
                  </div>
                  <div className="flex justify-between items-center">
                    <span className="text-gray-300 text-xs">Win Rate:</span>
                    <span className="text-blue-300 font-mono font-bold">
                      {row.win_rate_d7.toFixed(1)}%
                    </span>
                  </div>
                  <div className="flex justify-between items-center">
                    <span className="text-gray-300 text-xs">Confidence:</span>
                    <span className="text-yellow-300 font-semibold">
                      {row.category_confidence.toFixed(0)}%
                    </span>
                  </div>
                </div>

                <div className="mt-3 text-center">
                  <div className="text-xs text-gray-400 mb-1">Best/Worst</div>
                  <div className="flex justify-center gap-2">
                    <span className="text-green-300 font-mono text-xs">
                      +{row.best_return_d7.toFixed(1)}%
                    </span>
                    <span className="text-gray-500">/</span>
                    <span className="text-red-300 font-mono text-xs">
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
