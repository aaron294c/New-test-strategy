/**
 * TradingView-Style RSI Indicator Component
 * Professional RSI visualization matching TradingView aesthetic and functionality
 */

import React, { useMemo } from 'react';
import Plot from 'react-plotly.js';
import { Paper, Typography, Box, Chip, CircularProgress } from '@mui/material';
import type { RSIChartData } from '@/types';

interface RSIPercentileChartProps {
  data: RSIChartData | null;
  ticker: string;
  isLoading?: boolean;
}

// TradingView color palette
const COLORS = {
  background: '#1E222D',
  gridLines: 'rgba(42, 46, 57, 0.3)',
  rsiLine: '#2962FF', // TradingView blue
  rsiMA: '#FFC107', // Gold/yellow for MA
  overbought: '#FF5252', // Red
  neutral: '#787B86', // Gray
  oversold: '#4CAF50', // Green
  buySignal: '#2196F3', // Bright blue
  sellSignal: '#F44336', // Bright red
  bullishDiv: '#4CAF50', // Green
  bearishDiv: '#FF6B9D', // Pink
  text: '#D1D4DC',
  textSecondary: '#787B86',
};

// Signal detection helper
interface Signal {
  date: string;
  value: number;
  type: 'buy' | 'sell';
  index: number;
}

interface Divergence {
  startIndex: number;
  endIndex: number;
  type: 'bullish' | 'bearish';
  startDate: string;
  endDate: string;
}

const detectBuySellSignals = (rsi: number[], dates: string[]): Signal[] => {
  const signals: Signal[] = [];
  
  for (let i = 1; i < rsi.length; i++) {
    // Buy signal: RSI crosses above 30 from below
    if (rsi[i - 1] < 30 && rsi[i] >= 30) {
      signals.push({
        date: dates[i],
        value: rsi[i],
        type: 'buy',
        index: i,
      });
    }
    
    // Sell signal: RSI crosses below 70 from above
    if (rsi[i - 1] > 70 && rsi[i] <= 70) {
      signals.push({
        date: dates[i],
        value: rsi[i],
        type: 'sell',
        index: i,
      });
    }
  }
  
  return signals;
};

// Find local peaks and troughs for divergence detection
const findPeaks = (values: number[], minDistance: number = 5): number[] => {
  const peaks: number[] = [];
  
  for (let i = minDistance; i < values.length - minDistance; i++) {
    let isPeak = true;
    for (let j = 1; j <= minDistance; j++) {
      if (values[i] <= values[i - j] || values[i] <= values[i + j]) {
        isPeak = false;
        break;
      }
    }
    if (isPeak) peaks.push(i);
  }
  
  return peaks;
};

const findTroughs = (values: number[], minDistance: number = 5): number[] => {
  const troughs: number[] = [];
  
  for (let i = minDistance; i < values.length - minDistance; i++) {
    let isTrough = true;
    for (let j = 1; j <= minDistance; j++) {
      if (values[i] >= values[i - j] || values[i] >= values[i + j]) {
        isTrough = false;
        break;
      }
    }
    if (isTrough) troughs.push(i);
  }
  
  return troughs;
};

const detectDivergences = (
  _rsi: number[],
  rsiMA: number[],
  dates: string[]
): Divergence[] => {
  const divergences: Divergence[] = [];
  
  // Use RSI-MA for smoother divergence detection
  const values = rsiMA;
  
  // Find recent peaks and troughs (last 60 data points for performance)
  const recentStart = Math.max(0, values.length - 60);
  const recentValues = values.slice(recentStart);
  const peaks = findPeaks(recentValues, 5).map(i => i + recentStart);
  const troughs = findTroughs(recentValues, 5).map(i => i + recentStart);
  
  // Detect bearish divergence (peaks)
  for (let i = 1; i < peaks.length; i++) {
    const prevPeak = peaks[i - 1];
    const currPeak = peaks[i];
    
    // RSI makes lower high while price would make higher high
    // We use RSI-MA value as proxy
    if (values[currPeak] < values[prevPeak] && values[prevPeak] > 60) {
      divergences.push({
        startIndex: prevPeak,
        endIndex: currPeak,
        type: 'bearish',
        startDate: dates[prevPeak],
        endDate: dates[currPeak],
      });
    }
  }
  
  // Detect bullish divergence (troughs)
  for (let i = 1; i < troughs.length; i++) {
    const prevTrough = troughs[i - 1];
    const currTrough = troughs[i];
    
    // RSI makes higher low while price would make lower low
    if (values[currTrough] > values[prevTrough] && values[prevTrough] < 40) {
      divergences.push({
        startIndex: prevTrough,
        endIndex: currTrough,
        type: 'bullish',
        startDate: dates[prevTrough],
        endDate: dates[currTrough],
      });
    }
  }
  
  return divergences;
};

const RSIPercentileChart: React.FC<RSIPercentileChartProps> = ({ data, ticker, isLoading }) => {
  const { signals, divergences, plotData } = useMemo(() => {
    if (!data) return { signals: [], divergences: [], plotData: [] };

    const { dates, rsi, rsi_ma } = data;
    
    // Detect signals and divergences
    const detectedSignals = detectBuySellSignals(rsi, dates);
    const detectedDivergences = detectDivergences(rsi, rsi_ma, dates);
    
    const buySignals = detectedSignals.filter(s => s.type === 'buy');
    const sellSignals = detectedSignals.filter(s => s.type === 'sell');

    const traces: any[] = [
      // Oversold zone (0-30) - subtle green tint
      {
        x: dates,
        y: Array(dates.length).fill(30),
        fill: 'tozeroy',
        fillcolor: 'rgba(76, 175, 80, 0.08)',
        line: { width: 0 },
        showlegend: false,
        hoverinfo: 'skip',
        type: 'scatter',
      },
      // Neutral zone (30-70) - no tint
      {
        x: dates,
        y: Array(dates.length).fill(70),
        fill: 'tonexty',
        fillcolor: 'rgba(30, 34, 45, 0)',
        line: { width: 0 },
        showlegend: false,
        hoverinfo: 'skip',
        type: 'scatter',
      },
      // Overbought zone (70-100) - subtle red tint
      {
        x: dates,
        y: Array(dates.length).fill(100),
        fill: 'tonexty',
        fillcolor: 'rgba(255, 82, 82, 0.08)',
        line: { width: 0 },
        showlegend: false,
        hoverinfo: 'skip',
        type: 'scatter',
      },
      // Reference lines
      {
        x: [dates[0], dates[dates.length - 1]],
        y: [70, 70],
        mode: 'lines',
        name: 'Overbought (70)',
        line: {
          color: COLORS.overbought,
          width: 1.5,
          dash: 'dash',
        },
        opacity: 0.5,
        hoverinfo: 'skip',
        type: 'scatter',
      },
      {
        x: [dates[0], dates[dates.length - 1]],
        y: [50, 50],
        mode: 'lines',
        name: 'Neutral (50)',
        line: {
          color: COLORS.neutral,
          width: 1.5,
          dash: 'dash',
        },
        opacity: 0.4,
        hoverinfo: 'skip',
        type: 'scatter',
      },
      {
        x: [dates[0], dates[dates.length - 1]],
        y: [30, 30],
        mode: 'lines',
        name: 'Oversold (30)',
        line: {
          color: COLORS.oversold,
          width: 1.5,
          dash: 'dash',
        },
        opacity: 0.5,
        hoverinfo: 'skip',
        type: 'scatter',
      },
      // RSI-MA line (golden/yellow)
      {
        x: dates,
        y: rsi_ma,
        mode: 'lines',
        name: 'RSI-MA (14)',
        line: {
          color: COLORS.rsiMA,
          width: 2,
        },
        opacity: 0.85,
        hovertemplate: '<b>Date:</b> %{x}<br><b>RSI-MA:</b> %{y:.2f}<extra></extra>',
        type: 'scatter',
      },
      // Main RSI line (bright cyan/blue)
      {
        x: dates,
        y: rsi,
        mode: 'lines',
        name: 'RSI (14)',
        line: {
          color: COLORS.rsiLine,
          width: 2.5,
        },
        hovertemplate: '<b>Date:</b> %{x}<br><b>RSI:</b> %{y:.2f}<extra></extra>',
        type: 'scatter',
      },
    ];

    // Add buy signals
    if (buySignals.length > 0) {
      traces.push({
        x: buySignals.map(s => s.date),
        y: buySignals.map(s => s.value - 5),
        mode: 'markers+text',
        name: 'Buy Signal',
        marker: {
          color: COLORS.buySignal,
          size: 12,
          symbol: 'triangle-up',
          line: {
            color: '#ffffff',
            width: 1.5,
          },
        },
        text: buySignals.map(() => 'BUY'),
        textposition: 'bottom center',
        textfont: {
          color: COLORS.buySignal,
          size: 10,
          family: 'Arial, sans-serif',
          weight: 600,
        },
        hovertemplate: '<b>Buy Signal</b><br>Date: %{x}<br>RSI: %{y:.2f}<extra></extra>',
        type: 'scatter',
      });
    }

    // Add sell signals
    if (sellSignals.length > 0) {
      traces.push({
        x: sellSignals.map(s => s.date),
        y: sellSignals.map(s => s.value + 5),
        mode: 'markers+text',
        name: 'Sell Signal',
        marker: {
          color: COLORS.sellSignal,
          size: 12,
          symbol: 'triangle-down',
          line: {
            color: '#ffffff',
            width: 1.5,
          },
        },
        text: sellSignals.map(() => 'SELL'),
        textposition: 'top center',
        textfont: {
          color: COLORS.sellSignal,
          size: 10,
          family: 'Arial, sans-serif',
          weight: 600,
        },
        hovertemplate: '<b>Sell Signal</b><br>Date: %{x}<br>RSI: %{y:.2f}<extra></extra>',
        type: 'scatter',
      });
    }

    // Add divergence lines
    detectedDivergences.forEach((div, idx) => {
      const color = div.type === 'bullish' ? COLORS.bullishDiv : COLORS.bearishDiv;
      traces.push({
        x: [dates[div.startIndex], dates[div.endIndex]],
        y: [rsi_ma[div.startIndex], rsi_ma[div.endIndex]],
        mode: 'lines',
        name: idx === 0 ? `${div.type === 'bullish' ? 'Bullish' : 'Bearish'} Divergence` : '',
        showlegend: idx === 0,
        line: {
          color: color,
          width: 2,
          dash: 'solid',
        },
        hovertemplate: `<b>${div.type === 'bullish' ? 'Bullish' : 'Bearish'} Divergence</b><br>%{x}<extra></extra>`,
        type: 'scatter',
      });
    });

    return {
      signals: detectedSignals,
      divergences: detectedDivergences,
      plotData: traces,
    };
  }, [data]);

  if (isLoading) {
    return (
      <Paper 
        sx={{ 
          p: 3, 
          display: 'flex', 
          justifyContent: 'center', 
          alignItems: 'center', 
          minHeight: 500,
          bgcolor: COLORS.background,
        }}
      >
        <CircularProgress sx={{ color: COLORS.rsiLine }} />
      </Paper>
    );
  }

  if (!data) {
    return (
      <Paper sx={{ p: 3, bgcolor: COLORS.background }}>
        <Typography variant="body1" sx={{ color: COLORS.text }}>
          No chart data available
        </Typography>
      </Paper>
    );
  }

  const currentRSI = data.current_rsi;
  const currentRSIMA = data.current_rsi_ma;
  
  // Determine current market condition
  const getMarketCondition = (rsi: number) => {
    if (rsi < 30) return { label: 'Oversold', color: COLORS.oversold };
    if (rsi > 70) return { label: 'Overbought', color: COLORS.overbought };
    return { label: 'Neutral', color: COLORS.neutral };
  };
  
  const condition = getMarketCondition(currentRSI);
  const recentBuySignals = signals.filter(s => s.type === 'buy').slice(-3);
  const recentSellSignals = signals.filter(s => s.type === 'sell').slice(-3);
  const recentDivergences = divergences.slice(-2);

  return (
    <Paper 
      sx={{ 
        p: 0, 
        bgcolor: COLORS.background,
        borderRadius: 2,
        overflow: 'hidden',
      }}
    >
      {/* Header with ticker and current values */}
      <Box 
        sx={{ 
          p: 2, 
          pb: 1,
          borderBottom: `1px solid ${COLORS.gridLines}`,
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          flexWrap: 'wrap',
          gap: 2,
        }}
      >
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
          <Typography 
            variant="h5" 
            sx={{ 
              color: COLORS.text,
              fontWeight: 600,
              letterSpacing: '0.5px',
            }}
          >
            {ticker}
          </Typography>
          <Chip
            label="RSI Indicator"
            size="small"
            sx={{
              bgcolor: 'rgba(41, 98, 255, 0.15)',
              color: COLORS.rsiLine,
              fontWeight: 600,
              border: `1px solid ${COLORS.rsiLine}`,
            }}
          />
        </Box>
        
        <Box sx={{ display: 'flex', gap: 1.5, flexWrap: 'wrap', alignItems: 'center' }}>
          <Box
            sx={{
              px: 2,
              py: 0.75,
              bgcolor: 'rgba(41, 98, 255, 0.2)',
              borderRadius: 2,
              border: `1px solid ${COLORS.rsiLine}`,
            }}
          >
            <Typography 
              variant="caption" 
              sx={{ 
                color: COLORS.textSecondary,
                display: 'block',
                fontSize: '0.7rem',
              }}
            >
              RSI
            </Typography>
            <Typography 
              variant="body1" 
              sx={{ 
                color: COLORS.rsiLine,
                fontWeight: 700,
                fontSize: '1.1rem',
              }}
            >
              {currentRSI.toFixed(2)}
            </Typography>
          </Box>
          
          <Box
            sx={{
              px: 2,
              py: 0.75,
              bgcolor: 'rgba(255, 193, 7, 0.15)',
              borderRadius: 2,
              border: `1px solid ${COLORS.rsiMA}`,
            }}
          >
            <Typography 
              variant="caption" 
              sx={{ 
                color: COLORS.textSecondary,
                display: 'block',
                fontSize: '0.7rem',
              }}
            >
              RSI-MA
            </Typography>
            <Typography 
              variant="body1" 
              sx={{ 
                color: COLORS.rsiMA,
                fontWeight: 700,
                fontSize: '1.1rem',
              }}
            >
              {currentRSIMA.toFixed(2)}
            </Typography>
          </Box>

          <Chip
            label={condition.label}
            size="small"
            sx={{
              bgcolor: `${condition.color}20`,
              color: condition.color,
              fontWeight: 600,
              border: `1.5px solid ${condition.color}`,
              px: 1,
            }}
          />
        </Box>
      </Box>

      {/* Chart */}
      <Box sx={{ p: 2, pt: 1 }}>
        <Plot
          data={plotData}
          layout={{
            autosize: true,
            height: 550,
            margin: { l: 60, r: 70, t: 20, b: 60 },
            xaxis: {
              title: { 
                text: '',
                font: { color: COLORS.text },
              },
              gridcolor: COLORS.gridLines,
              gridwidth: 1,
              showgrid: true,
              zeroline: false,
              tickfont: { 
                color: COLORS.textSecondary,
                size: 11,
              },
              showline: true,
              linecolor: COLORS.gridLines,
              linewidth: 1,
            },
            yaxis: {
              title: { 
                text: '',
                font: { color: COLORS.text },
              },
              gridcolor: COLORS.gridLines,
              gridwidth: 1,
              showgrid: true,
              zeroline: false,
              range: [0, 100],
              tickmode: 'array',
              tickvals: [0, 20, 30, 40, 50, 60, 70, 80, 100],
              tickfont: { 
                color: COLORS.textSecondary,
                size: 11,
              },
              showline: true,
              linecolor: COLORS.gridLines,
              linewidth: 1,
            },
            hovermode: 'x unified',
            showlegend: true,
            legend: {
              x: 0.01,
              y: 0.99,
              bgcolor: 'rgba(30, 34, 45, 0.95)',
              bordercolor: COLORS.gridLines,
              borderwidth: 1,
              font: {
                color: COLORS.text,
                size: 11,
              },
            },
            plot_bgcolor: COLORS.background,
            paper_bgcolor: COLORS.background,
            font: {
              color: COLORS.text,
              family: 'Arial, Helvetica, sans-serif',
            },
          }}
          config={{
            responsive: true,
            displayModeBar: true,
            displaylogo: false,
            modeBarButtonsToRemove: ['pan2d', 'lasso2d', 'select2d', 'autoScale2d'],
          }}
          style={{ width: '100%' }}
        />
      </Box>

      {/* Signal Summary */}
      <Box 
        sx={{ 
          p: 2, 
          pt: 1,
          borderTop: `1px solid ${COLORS.gridLines}`,
        }}
      >
        <Box sx={{ display: 'flex', gap: 3, flexWrap: 'wrap' }}>
          {/* Buy Signals */}
          {recentBuySignals.length > 0 && (
            <Box>
              <Typography 
                variant="caption" 
                sx={{ 
                  color: COLORS.textSecondary,
                  display: 'block',
                  mb: 0.5,
                  fontSize: '0.7rem',
                  fontWeight: 600,
                  textTransform: 'uppercase',
                  letterSpacing: '0.5px',
                }}
              >
                Recent Buy Signals ({recentBuySignals.length})
              </Typography>
              <Box sx={{ display: 'flex', gap: 0.5, flexWrap: 'wrap' }}>
                {recentBuySignals.map((signal, idx) => (
                  <Chip
                    key={idx}
                    label={signal.date}
                    size="small"
                    sx={{
                      bgcolor: `${COLORS.buySignal}20`,
                      color: COLORS.buySignal,
                      fontSize: '0.7rem',
                      height: '24px',
                    }}
                  />
                ))}
              </Box>
            </Box>
          )}

          {/* Sell Signals */}
          {recentSellSignals.length > 0 && (
            <Box>
              <Typography 
                variant="caption" 
                sx={{ 
                  color: COLORS.textSecondary,
                  display: 'block',
                  mb: 0.5,
                  fontSize: '0.7rem',
                  fontWeight: 600,
                  textTransform: 'uppercase',
                  letterSpacing: '0.5px',
                }}
              >
                Recent Sell Signals ({recentSellSignals.length})
              </Typography>
              <Box sx={{ display: 'flex', gap: 0.5, flexWrap: 'wrap' }}>
                {recentSellSignals.map((signal, idx) => (
                  <Chip
                    key={idx}
                    label={signal.date}
                    size="small"
                    sx={{
                      bgcolor: `${COLORS.sellSignal}20`,
                      color: COLORS.sellSignal,
                      fontSize: '0.7rem',
                      height: '24px',
                    }}
                  />
                ))}
              </Box>
            </Box>
          )}

          {/* Divergences */}
          {recentDivergences.length > 0 && (
            <Box>
              <Typography 
                variant="caption" 
                sx={{ 
                  color: COLORS.textSecondary,
                  display: 'block',
                  mb: 0.5,
                  fontSize: '0.7rem',
                  fontWeight: 600,
                  textTransform: 'uppercase',
                  letterSpacing: '0.5px',
                }}
              >
                Divergences Detected
              </Typography>
              <Box sx={{ display: 'flex', gap: 0.5, flexWrap: 'wrap' }}>
                {recentDivergences.map((div, idx) => (
                  <Chip
                    key={idx}
                    label={`${div.type === 'bullish' ? 'Bullish' : 'Bearish'}: ${div.endDate}`}
                    size="small"
                    sx={{
                      bgcolor: div.type === 'bullish' ? `${COLORS.bullishDiv}20` : `${COLORS.bearishDiv}20`,
                      color: div.type === 'bullish' ? COLORS.bullishDiv : COLORS.bearishDiv,
                      fontSize: '0.7rem',
                      height: '24px',
                      textTransform: 'capitalize',
                    }}
                  />
                ))}
              </Box>
            </Box>
          )}
        </Box>

        {/* Interpretation Guide */}
        <Box 
          sx={{ 
            mt: 2, 
            p: 1.5, 
            bgcolor: 'rgba(42, 46, 57, 0.4)', 
            borderRadius: 1,
            borderLeft: `3px solid ${COLORS.rsiLine}`,
          }}
        >
          <Typography 
            variant="caption" 
            sx={{ 
              color: COLORS.text, 
              display: 'block',
              fontSize: '0.75rem',
              lineHeight: 1.6,
            }}
          >
            <strong style={{ color: COLORS.rsiLine }}>Quick Guide:</strong>{' '}
            <span style={{ color: COLORS.oversold }}>RSI &lt; 30</span> = Oversold (potential buy) • {' '}
            <span style={{ color: COLORS.overbought }}>RSI &gt; 70</span> = Overbought (potential sell) • {' '}
            <span style={{ color: COLORS.bullishDiv }}>Bullish Divergence</span> = Higher lows in RSI vs price (bullish signal) • {' '}
            <span style={{ color: COLORS.bearishDiv }}>Bearish Divergence</span> = Lower highs in RSI vs price (bearish signal)
          </Typography>
        </Box>
      </Box>
    </Paper>
  );
};

export default RSIPercentileChart;
