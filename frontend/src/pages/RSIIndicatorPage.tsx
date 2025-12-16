import { useEffect, useMemo, useRef, useState } from 'react';
import {
  Box,
  Button,
  Checkbox,
  CircularProgress,
  FormControlLabel,
  Paper,
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableRow,
  Typography,
} from '@mui/material';
import {
  createChart,
  IChartApi,
  ISeriesApi,
  LineData,
  LineStyle,
  PriceLineOptions,
  SeriesMarker,
  UTCTimestamp,
} from 'lightweight-charts';
import type { RSIChartData } from '@/types';

type Props = {
  data: RSIChartData | null;
  ticker: string;
  isLoading?: boolean;
  onRefresh?: () => void;
};

type Divergence = {
  startIndex: number;
  endIndex: number;
  type: 'bullish' | 'bearish';
};

function getRankColor(rank: number) {
  if (rank >= 95) return '#EF5350';
  if (rank >= 85) return '#FF9800';
  if (rank >= 75) return '#FFEB3B';
  if (rank >= 25) return '#D1D4DC';
  if (rank >= 15) return '#2962FF';
  if (rank >= 5) return '#AEEA00';
  return '#00C853';
}

function detectBuySellSignals(rsi: number[], times: UTCTimestamp[]) {
  const markers: SeriesMarker<UTCTimestamp>[] = [];
  for (let i = 1; i < rsi.length; i++) {
    if (rsi[i - 1] < 30 && rsi[i] >= 30) {
      markers.push({
        time: times[i],
        position: 'belowBar',
        color: '#2962FF',
        shape: 'arrowUp',
        text: 'BUY',
      });
    }
    if (rsi[i - 1] > 70 && rsi[i] <= 70) {
      markers.push({
        time: times[i],
        position: 'aboveBar',
        color: '#EF5350',
        shape: 'arrowDown',
        text: 'SELL',
      });
    }
  }
  return markers;
}

function findPeaks(values: number[], minDistance = 5) {
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
}

function findTroughs(values: number[], minDistance = 5) {
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
}

function detectDivergences(rsiMA: number[]) {
  const divergences: Divergence[] = [];
  const recentStart = Math.max(0, rsiMA.length - 120);
  const recent = rsiMA.slice(recentStart);
  const peaks = findPeaks(recent, 5).map(i => i + recentStart);
  const troughs = findTroughs(recent, 5).map(i => i + recentStart);

  for (let i = 1; i < peaks.length; i++) {
    const prev = peaks[i - 1];
    const curr = peaks[i];
    if (rsiMA[curr] < rsiMA[prev] && rsiMA[prev] > 60) {
      divergences.push({ startIndex: prev, endIndex: curr, type: 'bearish' });
    }
  }

  for (let i = 1; i < troughs.length; i++) {
    const prev = troughs[i - 1];
    const curr = troughs[i];
    if (rsiMA[curr] > rsiMA[prev] && rsiMA[prev] < 40) {
      divergences.push({ startIndex: prev, endIndex: curr, type: 'bullish' });
    }
  }

  return divergences;
}

function RSIChart(props: {
  data: RSIChartData;
  showPercentileLines: boolean;
  showSignals: boolean;
  showDivergences: boolean;
}) {
  const { data, showPercentileLines, showSignals, showDivergences } = props;

  const chartContainerRef = useRef<HTMLDivElement | null>(null);
  const chartRef = useRef<IChartApi | null>(null);
  const rsiSeriesRef = useRef<ISeriesApi<'Line'> | null>(null);
  const rsiMASeriesRef = useRef<ISeriesApi<'Line'> | null>(null);
  const percentileLinesRef = useRef<
    Array<{
      series: ISeriesApi<'Line'>;
      line: ReturnType<ISeriesApi<'Line'>['createPriceLine']>;
    }>
  >([]);
  const divergenceSeriesRef = useRef<ISeriesApi<'Line'>[]>([]);

  const times = useMemo(
    () => data.dates.map(d => (new Date(d).getTime() / 1000) as UTCTimestamp),
    [data.dates]
  );

  const currentRankColor = useMemo(() => getRankColor(data.current_percentile), [data.current_percentile]);

  useEffect(() => {
    const el = chartContainerRef.current;
    if (!el) return;

    const chart = createChart(el, {
      width: el.clientWidth,
      height: 520,
      layout: { background: { color: '#1a1a1a' }, textColor: '#d1d4dc' },
      grid: { vertLines: { color: '#2b2b43' }, horzLines: { color: '#2b2b43' } },
      rightPriceScale: { borderColor: '#485c7b' },
      timeScale: { borderColor: '#485c7b', timeVisible: true, secondsVisible: false },
      crosshair: { mode: 1 },
    });
    chartRef.current = chart;

    rsiMASeriesRef.current = chart.addLineSeries({
      color: currentRankColor,
      lineWidth: 2,
      title: 'RSI-MA (14)',
      autoscaleInfoProvider: () => ({ priceRange: { minValue: 0, maxValue: 100 } }),
    });

    rsiSeriesRef.current = chart.addLineSeries({
      color: 'rgba(41, 98, 255, 0.85)',
      lineWidth: 2,
      title: 'RSI (14)',
      autoscaleInfoProvider: () => ({ priceRange: { minValue: 0, maxValue: 100 } }),
    });

    // Fixed RSI reference lines (30/50/70)
    const baseLines: Array<{ price: number; title: string; color: string; opacity: number }> = [
      { price: 70, title: '70', color: 'rgba(239,83,80,0.6)', opacity: 1 },
      { price: 50, title: '50', color: 'rgba(120,123,134,0.6)', opacity: 1 },
      { price: 30, title: '30', color: 'rgba(0,200,83,0.6)', opacity: 1 },
    ];

    for (const l of baseLines) {
      const opts: PriceLineOptions = {
        price: l.price,
        title: l.title,
        color: l.color,
        lineWidth: 1,
        lineStyle: LineStyle.Dashed,
        axisLabelVisible: true,
      };
      rsiSeriesRef.current.createPriceLine(opts);
    }

    const handleResize = () => {
      const container = chartContainerRef.current;
      if (!container || !chartRef.current) return;
      chartRef.current.applyOptions({ width: container.clientWidth });
    };
    window.addEventListener('resize', handleResize);

    return () => {
      window.removeEventListener('resize', handleResize);
      chart.remove();
      chartRef.current = null;
      rsiSeriesRef.current = null;
      rsiMASeriesRef.current = null;
      percentileLinesRef.current = [];
      divergenceSeriesRef.current = [];
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  useEffect(() => {
    if (!rsiSeriesRef.current || !rsiMASeriesRef.current) return;

    rsiMASeriesRef.current.applyOptions({ color: currentRankColor });

    const rsiLine: LineData<UTCTimestamp>[] = data.rsi.map((v, i) => ({ time: times[i], value: v }));
    const rsiMALine: LineData<UTCTimestamp>[] = data.rsi_ma.map((v, i) => ({ time: times[i], value: v }));
    rsiSeriesRef.current.setData(rsiLine);
    rsiMASeriesRef.current.setData(rsiMALine);

    // Markers
    rsiSeriesRef.current.setMarkers(showSignals ? detectBuySellSignals(data.rsi, times) : []);

    // Clear percentile lines
    for (const { series, line } of percentileLinesRef.current) {
      try {
        series.removePriceLine(line);
      } catch {
        // ignore
      }
    }
    percentileLinesRef.current = [];

    if (showPercentileLines) {
      const add = (price: number, title: string, color: string, width: number, style: LineStyle) => {
        const opts: PriceLineOptions = {
          price,
          title,
          color,
          lineWidth: width,
          lineStyle: style,
          axisLabelVisible: true,
        };
        percentileLinesRef.current.push({ series: rsiMASeriesRef.current!, line: rsiMASeriesRef.current!.createPriceLine(opts) });
      };

      const p = data.percentile_thresholds;
      add(p.p5, 'p5', 'rgba(0,200,83,0.55)', 1, LineStyle.Dashed);
      add(p.p15, 'p15', 'rgba(174,234,0,0.55)', 1, LineStyle.Dashed);
      add(p.p25, 'p25', 'rgba(41,98,255,0.55)', 1, LineStyle.Dashed);
      add(p.p50, 'p50', 'rgba(120,123,134,0.55)', 2, LineStyle.Solid);
      add(p.p75, 'p75', 'rgba(255,235,59,0.55)', 1, LineStyle.Dashed);
      add(p.p85, 'p85', 'rgba(255,152,0,0.55)', 1, LineStyle.Dashed);
      add(p.p95, 'p95', 'rgba(239,83,80,0.55)', 1, LineStyle.Dashed);
    }

    // Clear divergence overlay series
    if (chartRef.current) {
      for (const s of divergenceSeriesRef.current) {
        try {
          chartRef.current.removeSeries(s);
        } catch {
          // ignore
        }
      }
    }
    divergenceSeriesRef.current = [];

    if (showDivergences && chartRef.current) {
      const divergences = detectDivergences(data.rsi_ma).slice(-6);
      for (const div of divergences) {
        const s = chartRef.current.addLineSeries({
          color: div.type === 'bullish' ? 'rgba(0,200,83,0.9)' : 'rgba(239,83,80,0.9)',
          lineWidth: 2,
          title: div.type === 'bullish' ? 'Bullish div' : 'Bearish div',
          autoscaleInfoProvider: () => ({ priceRange: { minValue: 0, maxValue: 100 } }),
        });
        s.setData([
          { time: times[div.startIndex], value: data.rsi_ma[div.startIndex] },
          { time: times[div.endIndex], value: data.rsi_ma[div.endIndex] },
        ]);
        divergenceSeriesRef.current.push(s);
      }
    }

    chartRef.current?.timeScale().fitContent();
  }, [currentRankColor, data, showDivergences, showPercentileLines, showSignals, times]);

  return <div ref={chartContainerRef} style={{ width: '100%' }} />;
}

export default function RSIIndicatorPage(props: Props) {
  const { data, ticker, isLoading, onRefresh } = props;

  const [showPercentileLines, setShowPercentileLines] = useState(true);
  const [showPercentileTable, setShowPercentileTable] = useState(true);
  const [showSignals, setShowSignals] = useState(true);
  const [showDivergences, setShowDivergences] = useState(true);

  const condition = useMemo(() => {
    const rsi = data?.current_rsi ?? 50;
    if (rsi < 30) return { label: 'Oversold', color: '#00C853' };
    if (rsi > 70) return { label: 'Overbought', color: '#EF5350' };
    return { label: 'Neutral', color: '#787B86' };
  }, [data?.current_rsi]);

  const rankColor = useMemo(() => getRankColor(data?.current_percentile ?? 50), [data?.current_percentile]);

  if (isLoading) {
    return (
      <Paper sx={{ p: 3, display: 'flex', justifyContent: 'center', alignItems: 'center', minHeight: 520 }}>
        <CircularProgress />
      </Paper>
    );
  }

  if (!data) {
    return (
      <Paper sx={{ p: 3 }}>
        <Typography>No RSI chart data available.</Typography>
      </Paper>
    );
  }

  return (
    <Box>
      <Paper elevation={3} sx={{ p: 3, mb: 3 }}>
        <Box sx={{ display: 'flex', alignItems: 'baseline', justifyContent: 'space-between', gap: 2, mb: 2 }}>
          <Box>
            <Typography variant="h6">RSI Indicator (Percentile-Colored RSI-MA)</Typography>
            <Typography variant="body2" color="text.secondary">
              Ticker: {ticker} • RSI on change of log returns • RSI-MA percentile rank drives line color.
            </Typography>
          </Box>
          <Box sx={{ display: 'flex', gap: 1, alignItems: 'center', flexWrap: 'wrap', justifyContent: 'flex-end' }}>
            <Box sx={{ textAlign: 'right' }}>
              <Typography variant="caption" color="text.secondary">
                RSI
              </Typography>
              <Typography variant="body2" sx={{ fontWeight: 700, color: '#2962FF' }}>
                {data.current_rsi.toFixed(2)}
              </Typography>
            </Box>
            <Box sx={{ textAlign: 'right' }}>
              <Typography variant="caption" color="text.secondary">
                RSI-MA
              </Typography>
              <Typography variant="body2" sx={{ fontWeight: 700, color: rankColor }}>
                {data.current_rsi_ma.toFixed(2)}
              </Typography>
            </Box>
            <Box sx={{ textAlign: 'right' }}>
              <Typography variant="caption" color="text.secondary">
                Percentile
              </Typography>
              <Typography variant="body2" sx={{ fontWeight: 700, color: rankColor }}>
                {data.current_percentile.toFixed(1)}%
              </Typography>
            </Box>
            <Box
              sx={{
                px: 1.25,
                py: 0.5,
                borderRadius: 1.5,
                border: `1px solid ${condition.color}`,
                color: condition.color,
                bgcolor: `${condition.color}18`,
                fontSize: '0.8rem',
                fontWeight: 700,
              }}
            >
              {condition.label}
            </Box>
            {onRefresh && (
              <Button variant="contained" onClick={onRefresh}>
                Refresh
              </Button>
            )}
          </Box>
        </Box>

        <Box sx={{ display: 'flex', gap: 2, flexWrap: 'wrap' }}>
          <FormControlLabel
            control={<Checkbox checked={showPercentileLines} onChange={(e) => setShowPercentileLines(e.target.checked)} />}
            label="Show percentile lines"
          />
          <FormControlLabel
            control={<Checkbox checked={showPercentileTable} onChange={(e) => setShowPercentileTable(e.target.checked)} />}
            label="Show percentile table"
          />
          <FormControlLabel
            control={<Checkbox checked={showSignals} onChange={(e) => setShowSignals(e.target.checked)} />}
            label="Show buy/sell markers"
          />
          <FormControlLabel
            control={<Checkbox checked={showDivergences} onChange={(e) => setShowDivergences(e.target.checked)} />}
            label="Show divergences"
          />
        </Box>
      </Paper>

      <Paper elevation={3} sx={{ p: 2, mb: 3 }}>
        <RSIChart
          data={data}
          showPercentileLines={showPercentileLines}
          showSignals={showSignals}
          showDivergences={showDivergences}
        />
      </Paper>

      {showPercentileTable && (
        <Paper elevation={3} sx={{ p: 3 }}>
          <Typography variant="h6" sx={{ mb: 1 }}>
            RSI-MA Percentiles
          </Typography>
          <Table size="small">
            <TableHead>
              <TableRow>
                <TableCell>Percentile</TableCell>
                <TableCell align="right">RSI-MA</TableCell>
                <TableCell align="right">Current</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {(
                [
                  ['5%', data.percentile_thresholds.p5],
                  ['15%', data.percentile_thresholds.p15],
                  ['25%', data.percentile_thresholds.p25],
                  ['50%', data.percentile_thresholds.p50],
                  ['75%', data.percentile_thresholds.p75],
                  ['85%', data.percentile_thresholds.p85],
                  ['95%', data.percentile_thresholds.p95],
                ] as const
              ).map(([label, value]) => (
                <TableRow key={label}>
                  <TableCell>{label}</TableCell>
                  <TableCell align="right">{Number.isFinite(value) ? value.toFixed(4) : '—'}</TableCell>
                  <TableCell align="right">{data.current_rsi_ma >= value ? '✓' : '✗'}</TableCell>
                </TableRow>
              ))}
              <TableRow>
                <TableCell>
                  <strong>Current Rank</strong>
                </TableCell>
                <TableCell align="right" sx={{ color: rankColor, fontWeight: 700 }}>
                  {data.current_percentile.toFixed(1)}%
                </TableCell>
                <TableCell align="right" sx={{ color: rankColor, fontWeight: 700 }}>
                  {data.current_rsi_ma.toFixed(4)}
                </TableCell>
              </TableRow>
            </TableBody>
          </Table>
        </Paper>
      )}
    </Box>
  );
}

