/**
 * Performance Reporting and Visualization Utilities
 *
 * Generates detailed reports, charts, and exports for backtest results
 */

import {
  BacktestResults,
  PerformanceMetrics,
  Trade,
  EquityCurvePoint,
  RegimePerformance,
} from './Backtester';
import { RegimeType } from '../core/types';

/**
 * Report format options
 */
export enum ReportFormat {
  TEXT = 'text',
  JSON = 'json',
  HTML = 'html',
  CSV = 'csv',
  MARKDOWN = 'markdown',
}

/**
 * Chart data for visualization
 */
export interface ChartData {
  labels: string[];
  datasets: {
    label: string;
    data: number[];
    color?: string;
  }[];
}

/**
 * Performance Reporter
 */
export class PerformanceReporter {
  /**
   * Generate comprehensive text report
   */
  public static generateTextReport(results: BacktestResults): string {
    const { metrics } = results;
    let report = '';

    report += this.generateHeader(results);
    report += this.generatePerformanceSummary(metrics);
    report += this.generateTradeStatistics(metrics);
    report += this.generateRiskAnalysis(metrics);
    report += this.generateRegimeBreakdown(results);
    report += this.generateMonthlyPerformance(results);
    report += this.generateTopTrades(results);
    report += this.generateFooter();

    return report;
  }

  /**
   * Generate JSON report
   */
  public static generateJSONReport(results: BacktestResults): string {
    const report = {
      summary: {
        startDate: results.startDate,
        endDate: results.endDate,
        duration: results.durationDays,
        initialCapital: results.initialCapital,
        finalCapital: results.finalCapital,
        totalReturn: results.metrics.totalReturn,
        totalReturnPercent: results.metrics.totalReturnPercent,
      },
      performance: results.metrics,
      regimePerformance: Array.from(results.regimePerformance.entries()).map(
        ([regime, perf]) => ({
          regime,
          ...perf,
        })
      ),
      trades: results.trades.map(trade => ({
        ...trade,
        entryTime: trade.entryTime.toISOString(),
        exitTime: trade.exitTime?.toISOString(),
      })),
      equityCurve: results.equityCurve.map(point => ({
        ...point,
        timestamp: point.timestamp.toISOString(),
      })),
      monthlyReturns: Array.from(results.monthlyReturns.entries()).map(
        ([month, return_]) => ({
          month,
          return: return_,
        })
      ),
    };

    return JSON.stringify(report, null, 2);
  }

  /**
   * Generate Markdown report
   */
  public static generateMarkdownReport(results: BacktestResults): string {
    const { metrics } = results;
    let md = '';

    md += '# Backtest Results Report\n\n';
    md += `**Period:** ${results.startDate.toISOString().split('T')[0]} to ${results.endDate.toISOString().split('T')[0]}\n\n`;
    md += `**Duration:** ${results.durationDays} days\n\n`;
    md += `**Initial Capital:** $${results.initialCapital.toLocaleString()}\n\n`;
    md += `**Final Capital:** $${results.finalCapital.toLocaleString()}\n\n`;

    md += '## Performance Summary\n\n';
    md += '| Metric | Value |\n';
    md += '|--------|-------|\n';
    md += `| Total Return | $${metrics.totalReturn.toFixed(2)} (${metrics.totalReturnPercent.toFixed(2)}%) |\n`;
    md += `| CAGR | ${metrics.cagr.toFixed(2)}% |\n`;
    md += `| Sharpe Ratio | ${metrics.sharpeRatio.toFixed(2)} |\n`;
    md += `| Sortino Ratio | ${metrics.sortinoRatio.toFixed(2)} |\n`;
    md += `| Calmar Ratio | ${metrics.calmarRatio.toFixed(2)} |\n`;
    md += `| Max Drawdown | ${metrics.maxDrawdownPercent.toFixed(2)}% |\n`;
    md += `| Win Rate | ${(metrics.winRate * 100).toFixed(2)}% |\n`;
    md += `| Profit Factor | ${metrics.profitFactor.toFixed(2)} |\n\n`;

    md += '## Trade Statistics\n\n';
    md += '| Metric | Value |\n';
    md += '|--------|-------|\n';
    md += `| Total Trades | ${metrics.totalTrades} |\n`;
    md += `| Winning Trades | ${metrics.winningTrades} |\n`;
    md += `| Losing Trades | ${metrics.losingTrades} |\n`;
    md += `| Average Win | $${metrics.avgWin.toFixed(2)} (${metrics.avgWinPercent.toFixed(2)}%) |\n`;
    md += `| Average Loss | $${metrics.avgLoss.toFixed(2)} (${metrics.avgLossPercent.toFixed(2)}%) |\n`;
    md += `| Win/Loss Ratio | ${metrics.winLossRatio.toFixed(2)} |\n`;
    md += `| Expectancy | $${metrics.expectancy.toFixed(2)} |\n\n`;

    md += '## Regime Performance\n\n';
    md += '| Regime | Trades | Win Rate | Total PnL | Expectancy |\n';
    md += '|--------|--------|----------|-----------|------------|\n';

    results.regimePerformance.forEach((perf, regime) => {
      md += `| ${regime} | ${perf.trades} | ${(perf.winRate * 100).toFixed(2)}% | $${perf.totalPnL.toFixed(2)} | $${perf.metrics.expectancy.toFixed(2)} |\n`;
    });

    md += '\n## Monthly Returns\n\n';
    md += '| Month | Return |\n';
    md += '|-------|--------|\n';

    Array.from(results.monthlyReturns.entries())
      .sort(([a], [b]) => a.localeCompare(b))
      .forEach(([month, return_]) => {
        md += `| ${month} | ${return_.toFixed(2)}% |\n`;
      });

    return md;
  }

  /**
   * Generate CSV trade log
   */
  public static generateCSVTradeLog(results: BacktestResults): string {
    const headers = [
      'ID',
      'Instrument',
      'Direction',
      'Entry Time',
      'Entry Price',
      'Exit Time',
      'Exit Price',
      'Quantity',
      'Position Size',
      'PnL',
      'PnL %',
      'R-Multiple',
      'Holding Period',
      'Regime',
      'Score',
      'Exit Reason',
    ];

    let csv = headers.join(',') + '\n';

    results.trades.forEach(trade => {
      const row = [
        trade.id,
        trade.instrument,
        trade.direction,
        trade.entryTime.toISOString(),
        trade.entryPrice.toFixed(2),
        trade.exitTime?.toISOString() || '',
        trade.exitPrice?.toFixed(2) || '',
        trade.quantity.toFixed(4),
        trade.positionSize.toFixed(2),
        (trade.pnl ?? 0).toFixed(2),
        (trade.pnlPercent ?? 0).toFixed(2),
        (trade.rMultiple ?? 0).toFixed(2),
        trade.holdingPeriodBars || 0,
        trade.regime,
        trade.compositeScore.toFixed(2),
        `"${trade.exitReason || ''}"`,
      ];

      csv += row.join(',') + '\n';
    });

    return csv;
  }

  /**
   * Get equity curve data for charting
   */
  public static getEquityCurveData(results: BacktestResults): ChartData {
    return {
      labels: results.equityCurve.map(p => p.timestamp.toISOString().split('T')[0]),
      datasets: [
        {
          label: 'Equity',
          data: results.equityCurve.map(p => p.equity),
          color: '#4CAF50',
        },
        {
          label: 'Drawdown',
          data: results.equityCurve.map(p => -p.drawdown),
          color: '#F44336',
        },
      ],
    };
  }

  /**
   * Get monthly returns data for charting
   */
  public static getMonthlyReturnsData(results: BacktestResults): ChartData {
    const months = Array.from(results.monthlyReturns.keys()).sort();
    const returns = months.map(m => results.monthlyReturns.get(m) || 0);

    return {
      labels: months,
      datasets: [
        {
          label: 'Monthly Return %',
          data: returns,
          color: '#2196F3',
        },
      ],
    };
  }

  /**
   * Get regime performance data for charting
   */
  public static getRegimePerformanceData(results: BacktestResults): ChartData {
    const regimes = Array.from(results.regimePerformance.keys());
    const winRates = regimes.map(r => (results.regimePerformance.get(r)?.winRate || 0) * 100);
    const expectancies = regimes.map(r => results.regimePerformance.get(r)?.metrics.expectancy || 0);

    return {
      labels: regimes,
      datasets: [
        {
          label: 'Win Rate %',
          data: winRates,
          color: '#4CAF50',
        },
        {
          label: 'Expectancy $',
          data: expectancies,
          color: '#2196F3',
        },
      ],
    };
  }

  /**
   * Get trade distribution data
   */
  public static getTradeDistributionData(results: BacktestResults): ChartData {
    // Create PnL buckets
    const buckets: { [key: string]: number } = {
      '< -10%': 0,
      '-10% to -5%': 0,
      '-5% to -2%': 0,
      '-2% to 0%': 0,
      '0% to 2%': 0,
      '2% to 5%': 0,
      '5% to 10%': 0,
      '> 10%': 0,
    };

    results.trades.forEach(trade => {
      const pnlPercent = trade.pnlPercent || 0;

      if (pnlPercent < -10) buckets['< -10%']++;
      else if (pnlPercent < -5) buckets['-10% to -5%']++;
      else if (pnlPercent < -2) buckets['-5% to -2%']++;
      else if (pnlPercent < 0) buckets['-2% to 0%']++;
      else if (pnlPercent < 2) buckets['0% to 2%']++;
      else if (pnlPercent < 5) buckets['2% to 5%']++;
      else if (pnlPercent < 10) buckets['5% to 10%']++;
      else buckets['> 10%']++;
    });

    return {
      labels: Object.keys(buckets),
      datasets: [
        {
          label: 'Number of Trades',
          data: Object.values(buckets),
          color: '#9C27B0',
        },
      ],
    };
  }

  /**
   * Generate header section
   */
  private static generateHeader(results: BacktestResults): string {
    let header = '\n';
    header += '═══════════════════════════════════════════════════════════════\n';
    header += '                TRADING FRAMEWORK BACKTEST REPORT               \n';
    header += '═══════════════════════════════════════════════════════════════\n\n';
    header += `Period: ${results.startDate.toISOString().split('T')[0]} to ${results.endDate.toISOString().split('T')[0]}\n`;
    header += `Duration: ${results.durationDays} days (${(results.durationDays / 365.25).toFixed(2)} years)\n`;
    header += `Initial Capital: $${results.initialCapital.toLocaleString()}\n`;
    header += `Final Capital: $${results.finalCapital.toLocaleString()}\n\n`;

    return header;
  }

  /**
   * Generate performance summary section
   */
  private static generatePerformanceSummary(metrics: PerformanceMetrics): string {
    let summary = '';
    summary += '─────────────────────────────────────────────────────────────\n';
    summary += '  PERFORMANCE SUMMARY\n';
    summary += '─────────────────────────────────────────────────────────────\n';
    summary += `Total Return:        $${metrics.totalReturn.toFixed(2)} (${metrics.totalReturnPercent.toFixed(2)}%)\n`;
    summary += `CAGR:                ${metrics.cagr.toFixed(2)}%\n`;
    summary += `Sharpe Ratio:        ${metrics.sharpeRatio.toFixed(2)}\n`;
    summary += `Sortino Ratio:       ${metrics.sortinoRatio.toFixed(2)}\n`;
    summary += `Calmar Ratio:        ${metrics.calmarRatio.toFixed(2)}\n`;
    summary += `Profit Factor:       ${metrics.profitFactor.toFixed(2)}\n\n`;

    return summary;
  }

  /**
   * Generate trade statistics section
   */
  private static generateTradeStatistics(metrics: PerformanceMetrics): string {
    let stats = '';
    stats += '─────────────────────────────────────────────────────────────\n';
    stats += '  TRADE STATISTICS\n';
    stats += '─────────────────────────────────────────────────────────────\n';
    stats += `Total Trades:        ${metrics.totalTrades}\n`;
    stats += `Winning Trades:      ${metrics.winningTrades} (${(metrics.winRate * 100).toFixed(2)}%)\n`;
    stats += `Losing Trades:       ${metrics.losingTrades}\n`;
    stats += `Consecutive Wins:    ${metrics.maxConsecutiveWins}\n`;
    stats += `Consecutive Losses:  ${metrics.maxConsecutiveLosses}\n\n`;
    stats += `Average Win:         $${metrics.avgWin.toFixed(2)} (${metrics.avgWinPercent.toFixed(2)}%)\n`;
    stats += `Average Loss:        $${metrics.avgLoss.toFixed(2)} (${metrics.avgLossPercent.toFixed(2)}%)\n`;
    stats += `Win/Loss Ratio:      ${metrics.winLossRatio.toFixed(2)}\n`;
    stats += `Expectancy:          $${metrics.expectancy.toFixed(2)} (${metrics.expectancyPercent.toFixed(2)}%)\n\n`;
    stats += `Avg Holding Period:  ${metrics.avgHoldingPeriod.toFixed(1)} bars\n`;
    stats += `Avg Position Size:   $${metrics.avgPositionSize.toFixed(2)}\n`;
    stats += `Avg Risk Per Trade:  $${metrics.avgRiskPerTrade.toFixed(2)}\n\n`;

    return stats;
  }

  /**
   * Generate risk analysis section
   */
  private static generateRiskAnalysis(metrics: PerformanceMetrics): string {
    let risk = '';
    risk += '─────────────────────────────────────────────────────────────\n';
    risk += '  RISK ANALYSIS\n';
    risk += '─────────────────────────────────────────────────────────────\n';
    risk += `Max Drawdown:        $${metrics.maxDrawdown.toFixed(2)} (${metrics.maxDrawdownPercent.toFixed(2)}%)\n`;
    risk += `Max DD Duration:     ${metrics.maxDrawdownDuration} bars\n`;
    risk += `Avg Drawdown:        $${metrics.avgDrawdown.toFixed(2)}\n`;
    risk += `Recovery Factor:     ${metrics.recoveryFactor.toFixed(2)}\n`;
    risk += `Ulcer Index:         ${metrics.ulcerIndex.toFixed(2)}\n\n`;
    risk += `Avg MAE:             $${metrics.avgMAE.toFixed(2)}\n`;
    risk += `Avg MFE:             $${metrics.avgMFE.toFixed(2)}\n\n`;
    risk += `Std Deviation:       ${metrics.standardDeviation.toFixed(4)}\n`;
    risk += `Downside Deviation:  ${metrics.downSideDeviation.toFixed(4)}\n`;
    risk += `Skewness:            ${metrics.skewness.toFixed(4)}\n`;
    risk += `Kurtosis:            ${metrics.kurtosis.toFixed(4)}\n\n`;

    return risk;
  }

  /**
   * Generate regime breakdown section
   */
  private static generateRegimeBreakdown(results: BacktestResults): string {
    let regime = '';
    regime += '─────────────────────────────────────────────────────────────\n';
    regime += '  REGIME PERFORMANCE BREAKDOWN\n';
    regime += '─────────────────────────────────────────────────────────────\n';

    results.regimePerformance.forEach((perf, regimeType) => {
      regime += `\n${regimeType.toUpperCase()}:\n`;
      regime += `  Trades:            ${perf.trades}\n`;
      regime += `  Win Rate:          ${(perf.winRate * 100).toFixed(2)}%\n`;
      regime += `  Total PnL:         $${perf.totalPnL.toFixed(2)}\n`;
      regime += `  Expectancy:        $${perf.metrics.expectancy.toFixed(2)}\n`;
      regime += `  Avg Win:           $${perf.metrics.avgWin.toFixed(2)}\n`;
      regime += `  Avg Loss:          $${perf.metrics.avgLoss.toFixed(2)}\n`;
      regime += `  Sharpe Ratio:      ${perf.metrics.sharpeRatio.toFixed(2)}\n`;
    });

    regime += '\n';
    return regime;
  }

  /**
   * Generate monthly performance section
   */
  private static generateMonthlyPerformance(results: BacktestResults): string {
    let monthly = '';
    monthly += '─────────────────────────────────────────────────────────────\n';
    monthly += '  MONTHLY RETURNS\n';
    monthly += '─────────────────────────────────────────────────────────────\n';

    const months = Array.from(results.monthlyReturns.entries()).sort(([a], [b]) =>
      a.localeCompare(b)
    );

    months.forEach(([month, return_]) => {
      const sign = return_ >= 0 ? '+' : '';
      monthly += `${month}:  ${sign}${return_.toFixed(2)}%\n`;
    });

    monthly += '\n';
    return monthly;
  }

  /**
   * Generate top trades section
   */
  private static generateTopTrades(results: BacktestResults): string {
    let trades = '';
    trades += '─────────────────────────────────────────────────────────────\n';
    trades += '  TOP 5 WINNING TRADES\n';
    trades += '─────────────────────────────────────────────────────────────\n';

    const topWinners = [...results.trades]
      .sort((a, b) => (b.pnl || 0) - (a.pnl || 0))
      .slice(0, 5);

    topWinners.forEach((trade, index) => {
      trades += `${index + 1}. ${trade.instrument} ${trade.direction.toUpperCase()}: `;
      trades += `$${(trade.pnl || 0).toFixed(2)} (${(trade.pnlPercent || 0).toFixed(2)}%) `;
      trades += `${trade.regime}\n`;
    });

    trades += '\n─────────────────────────────────────────────────────────────\n';
    trades += '  TOP 5 LOSING TRADES\n';
    trades += '─────────────────────────────────────────────────────────────\n';

    const topLosers = [...results.trades]
      .sort((a, b) => (a.pnl || 0) - (b.pnl || 0))
      .slice(0, 5);

    topLosers.forEach((trade, index) => {
      trades += `${index + 1}. ${trade.instrument} ${trade.direction.toUpperCase()}: `;
      trades += `$${(trade.pnl || 0).toFixed(2)} (${(trade.pnlPercent || 0).toFixed(2)}%) `;
      trades += `${trade.regime}\n`;
    });

    trades += '\n';
    return trades;
  }

  /**
   * Generate footer section
   */
  private static generateFooter(): string {
    let footer = '';
    footer += '═══════════════════════════════════════════════════════════════\n';
    footer += `Generated: ${new Date().toISOString()}\n`;
    footer += '═══════════════════════════════════════════════════════════════\n\n';

    return footer;
  }

  /**
   * Export to file (requires filesystem access)
   */
  public static async exportToFile(
    results: BacktestResults,
    format: ReportFormat,
    filePath: string
  ): Promise<void> {
    let content: string;

    switch (format) {
      case ReportFormat.TEXT:
        content = this.generateTextReport(results);
        break;
      case ReportFormat.JSON:
        content = this.generateJSONReport(results);
        break;
      case ReportFormat.MARKDOWN:
        content = this.generateMarkdownReport(results);
        break;
      case ReportFormat.CSV:
        content = this.generateCSVTradeLog(results);
        break;
      default:
        throw new Error(`Unsupported format: ${format}`);
    }

    // In a real implementation, this would write to file
    // For now, just log the intent
    console.log(`Would export ${format} report to: ${filePath}`);
    console.log(`Content length: ${content.length} characters`);
  }
}
