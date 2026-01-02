import { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import {
  Alert,
  Box,
  Button,
  Checkbox,
  CircularProgress,
  FormControl,
  FormControlLabel,
  InputLabel,
  MenuItem,
  Paper,
  Select,
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
  UTCTimestamp,
} from 'lightweight-charts';

// Use environment variable for API base URL
const API_BASE_URL = import.meta.env.VITE_API_URL || '';

type Candle = {
  time: string;
  open: number;
  high: number;
  low: number;
  close: number;
};

type PercentileTarget = 'freq pass' | 'data' | 'DC component';

type Percentiles = {
  p5: number;
  p15: number;
  p25: number;
  p50: number;
  p75: number;
  p85: number;
  p95: number;
  currentRank: number;
  targetValue: number;
};

type WFTPoint = {
  time: UTCTimestamp;
  dataValue: number;
  freqPassValue: number;
  dcComponentValue: number;
  mainFreq: number | null;
  mainPeriod: number | null;
};

function ptd(value: number, lambda: number) {
  if (lambda === 0) return Math.log(value);
  return Math.pow(value, lambda);
}

function pti(value: number, lambda: number) {
  if (lambda === 0) return Math.exp(value);
  return Math.pow(value, 1 / lambda);
}

function avg(values: number[]) {
  if (values.length === 0) return 0;
  return values.reduce((a, b) => a + b, 0) / values.length;
}

function stdev(values: number[]) {
  if (values.length === 0) return 0;
  const mean = avg(values);
  const variance = avg(values.map(v => (v - mean) ** 2));
  return Math.sqrt(variance);
}

function solveLinearSystem(A: number[][], b: number[]) {
  const n = b.length;
  const M = A.map((row, i) => [...row, b[i]]);

  for (let col = 0; col < n; col++) {
    let pivot = col;
    for (let row = col + 1; row < n; row++) {
      if (Math.abs(M[row][col]) > Math.abs(M[pivot][col])) pivot = row;
    }
    if (Math.abs(M[pivot][col]) < 1e-12) return null;
    if (pivot !== col) [M[pivot], M[col]] = [M[col], M[pivot]];

    const div = M[col][col];
    for (let j = col; j <= n; j++) M[col][j] /= div;

    for (let row = 0; row < n; row++) {
      if (row === col) continue;
      const factor = M[row][col];
      for (let j = col; j <= n; j++) M[row][j] -= factor * M[col][j];
    }
  }

  return M.map(row => row[n]);
}

function wpolyregCurrent(data: number[], weights: number[], deg: number) {
  const len = data.length;
  const dim = deg + 1;

  const XTWX = Array.from({ length: dim }, () => Array.from({ length: dim }, () => 0));
  const XTWY = Array.from({ length: dim }, () => 0);

  for (let i = 0; i < len; i++) {
    const w = weights[i] ?? 0;
    const y = data[i] ?? 0;
    const x = len - i;
    const xPows = Array.from({ length: dim }, (_, j) => Math.pow(x, j));

    for (let j = 0; j < dim; j++) {
      XTWY[j] += w * xPows[j] * y;
      for (let m = 0; m < dim; m++) XTWX[j][m] += w * xPows[j] * xPows[m];
    }
  }

  const coeffs = solveLinearSystem(XTWX, XTWY);
  if (!coeffs) return 0;

  const x0 = len;
  return coeffs.reduce((acc, c, j) => acc + c * Math.pow(x0, j), 0);
}

function wdft(data: number[], weights: number[]) {
  const len = data.length;
  const Xreal = Array.from({ length: len }, () => 0);
  const Ximag = Array.from({ length: len }, () => 0);

  for (let k = 0; k < len; k++) {
    let sumReal = 0;
    let sumImag = 0;
    for (let n = 0; n < len; n++) {
      const angle = (2 * Math.PI * k * n) / len;
      const w = weights[n] ?? 0;
      const d = data[n] ?? 0;
      sumReal += w * d * Math.cos(angle);
      sumImag += -w * d * Math.sin(angle);
    }
    Xreal[k] = sumReal;
    Ximag[k] = sumImag;
  }

  return { Xreal, Ximag };
}

function iwdft(Xreal: number[], Ximag: number[], weights: number[]) {
  const len = Xreal.length;
  const data = Array.from({ length: len }, () => 0);

  for (let n = 0; n < len; n++) {
    let sumReal = 0;
    for (let k = 0; k < len; k++) {
      const angle = (2 * Math.PI * k * n) / len;
      sumReal += (Xreal[k] * Math.cos(angle) - Ximag[k] * Math.sin(angle)) / (weights[n] || 1);
    }
    data[n] = sumReal / len;
  }

  return data;
}

function ftfreq(n: number, d = 1) {
  const val = 1 / (n * d);
  const result = Array.from({ length: n }, () => 0);
  if (n === 1) return result;

  const N = Math.floor((n - 1) / 2 + 1);
  for (let i = 0; i < N; i++) result[i] = i * val;
  for (let i = N; i < n; i++) result[i] = (i - n) * val;
  return result;
}

function calcPercentile(sorted: number[], percentile: number) {
  if (sorted.length === 0) return NaN;
  const idx = Math.round((percentile / 100) * (sorted.length - 1));
  return sorted[Math.min(sorted.length - 1, Math.max(0, idx))];
}

function getRankColor(rank: number) {
  if (rank >= 95) return '#EF5350';
  if (rank >= 85) return '#FF9800';
  if (rank >= 75) return '#FFEB3B';
  if (rank >= 25) return '#D1D4DC';
  if (rank >= 15) return '#2962FF';
  if (rank >= 5) return '#AEEA00';
  return '#00C853';
}

function computeWFTSeries(params: {
  candles: Candle[];
  lambda: number;
  lengthInput: number;
  timeWeighting: boolean;
  ivWeighting: boolean;
  detrend: boolean;
  degree: number;
  kLevel: number;
  percentileTarget: PercentileTarget;
  percentileLookback: number;
}) {
  const {
    candles,
    lambda,
    lengthInput,
    timeWeighting,
    ivWeighting,
    detrend,
    degree,
    kLevel,
    percentileTarget,
    percentileLookback,
  } = params;

  const times = candles.map(c => (new Date(c.time).getTime() / 1000) as UTCTimestamp);
  const src = candles.map(c => ptd(c.close, lambda));

  const srcDetr: number[] = Array.from({ length: candles.length }, () => NaN);
  const points: WFTPoint[] = [];
  const reconWindow: LineData<UTCTimestamp>[] = [];

  for (let j = 0; j < candles.length; j++) {
    const lenRaw = lengthInput > 0 ? Math.min(lengthInput, 50) : Math.min(j + 1, 25);
    const len = Math.min(lenRaw, j + 1);
    const dataWindow = Array.from({ length: len }, () => 0);
    const weights = Array.from({ length: len }, () => 1);

    for (let i = 0; i < len; i++) {
      const idx = j - i;
      const wTime = timeWeighting ? len - i : 1;
      const wIv = ivWeighting ? Math.abs(candles[idx].close - candles[idx].open) : 1;
      weights[i] = wTime * wIv;
      dataWindow[i] = src[idx];
    }

    if (detrend) {
      const fittedCurrent = wpolyregCurrent(dataWindow, weights, Math.max(0, Math.min(3, degree)));
      srcDetr[j] = src[j] - fittedCurrent;
    }

    const analysisWindow = Array.from({ length: len }, () => 0);
    for (let i = 0; i < len; i++) {
      const idx = j - i;
      analysisWindow[i] = detrend ? (srcDetr[idx] ?? src[idx]) : src[idx];
    }

    const { Xreal, Ximag } = wdft(analysisWindow, weights);
    const xf = ftfreq(len, 1);

    const weightSum = weights.reduce((a, b) => a + b, 0);
    const power = Xreal.map((r, i) => Math.sqrt(r * r + Ximag[i] * Ximag[i]) / weightSum);
    const threshold = avg(power) + stdev(power) * kLevel;

    const filteredReal = Xreal.map((v, i) => {
      if (kLevel < 0) return v;
      return power[i] > threshold ? v : 0;
    });
    const filteredImag = Ximag.map((v, i) => {
      if (kLevel < 0) return v;
      return power[i] > threshold ? v : 0;
    });

    const recon = iwdft(filteredReal, filteredImag, weights);

    const halfLen = Math.ceil(len / 2);
    const halfFreq = xf.slice(0, halfLen);
    const halfPower = power.slice(0, halfLen);

    let mainFreq: number | null = null;
    let mainPeriod: number | null = null;
    if (j >= len - 1 && halfPower.length > 0) {
      let maxIdx = 0;
      for (let i = 1; i < halfPower.length; i++) if (halfPower[i] > halfPower[maxIdx]) maxIdx = i;
      mainFreq = halfFreq[maxIdx] ?? null;
      mainPeriod = mainFreq && mainFreq !== 0 ? Math.round(1 / mainFreq) : len;
    }

    const srcForValue = detrend ? srcDetr[j] : src[j];
    const dataValue = pti(srcForValue, lambda);
    const freqPassValue = pti(recon[0] ?? 0, lambda);
    const dcComponentValue = pti(power[0] ?? 0, lambda);

    points.push({
      time: times[j],
      dataValue,
      freqPassValue,
      dcComponentValue,
      mainFreq,
      mainPeriod,
    });

    if (j === candles.length - 1) {
      for (let i = len - 1; i >= 0; i--) {
        const idx = j - i;
        reconWindow.push({
          time: times[idx],
          value: pti(recon[i] ?? 0, lambda),
        });
      }
    }
  }

  const targetSeries = points.map((p) => {
    if (percentileTarget === 'data') return p.dataValue;
    if (percentileTarget === 'DC component') return p.dcComponentValue;
    return p.freqPassValue;
  });

  const lookback = Math.min(percentileLookback, targetSeries.length);
  const hist = targetSeries.slice(Math.max(0, targetSeries.length - lookback)).filter(v => Number.isFinite(v));
  const sorted = [...hist].sort((a, b) => a - b);

  const targetValue = targetSeries.at(-1) ?? NaN;
  const currentRank = sorted.length
    ? (sorted.filter(v => v < targetValue).length / sorted.length) * 100
    : NaN;

  const percentiles: Percentiles = {
    p5: calcPercentile(sorted, 5),
    p15: calcPercentile(sorted, 15),
    p25: calcPercentile(sorted, 25),
    p50: calcPercentile(sorted, 50),
    p75: calcPercentile(sorted, 75),
    p85: calcPercentile(sorted, 85),
    p95: calcPercentile(sorted, 95),
    currentRank,
    targetValue,
  };

  return { points, percentiles, reconWindow };
}

function WFTChart(props: {
  points: WFTPoint[];
  reconWindow: LineData<UTCTimestamp>[];
  percentileTarget: PercentileTarget;
  percentiles: Percentiles | null;
  showPercentileLines: boolean;
}) {
  const { points, reconWindow, percentileTarget, percentiles, showPercentileLines } = props;

  const chartContainerRef = useRef<HTMLDivElement | null>(null);
  const chartRef = useRef<IChartApi | null>(null);
  const dataSeriesRef = useRef<ISeriesApi<'Line'> | null>(null);
  const freqSeriesRef = useRef<ISeriesApi<'Line'> | null>(null);
  const dcSeriesRef = useRef<ISeriesApi<'Line'> | null>(null);
  const reconSeriesRef = useRef<ISeriesApi<'Line'> | null>(null);
  const priceLinesRef = useRef<
    Array<{
      series: ISeriesApi<'Line'>;
      line: ReturnType<ISeriesApi<'Line'>['createPriceLine']>;
    }>
  >([]);

  const rankColor = useMemo(() => {
    if (!percentiles || !Number.isFinite(percentiles.currentRank)) return '#9C27B0';
    return getRankColor(percentiles.currentRank);
  }, [percentiles]);

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

    dataSeriesRef.current = chart.addLineSeries({
      color: '#9C27B0',
      lineWidth: 2,
      title: 'data',
    });
    freqSeriesRef.current = chart.addLineSeries({
      color: '#9CA3AF',
      lineWidth: 2,
      title: 'freq pass',
    });
    dcSeriesRef.current = chart.addLineSeries({
      color: '#FF9800',
      lineWidth: 2,
      title: 'DC component',
    });
    reconSeriesRef.current = chart.addLineSeries({
      color: '#26A69A',
      lineWidth: 2,
      lineStyle: LineStyle.Dashed,
      title: 'recon (window)',
    });

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
      dataSeriesRef.current = null;
      freqSeriesRef.current = null;
      dcSeriesRef.current = null;
      reconSeriesRef.current = null;
      priceLinesRef.current = [];
    };
  }, []);

  useEffect(() => {
    if (!dataSeriesRef.current || !freqSeriesRef.current || !dcSeriesRef.current || !reconSeriesRef.current) return;

    const dataLine: LineData<UTCTimestamp>[] = points.map(p => ({ time: p.time, value: p.dataValue }));
    const freqLine: LineData<UTCTimestamp>[] = points.map(p => ({ time: p.time, value: p.freqPassValue }));
    const dcLine: LineData<UTCTimestamp>[] = points.map(p => ({ time: p.time, value: p.dcComponentValue }));

    dataSeriesRef.current.applyOptions({ color: percentileTarget === 'data' ? rankColor : '#9C27B0' });
    freqSeriesRef.current.applyOptions({ color: percentileTarget === 'freq pass' ? rankColor : '#9CA3AF' });
    dcSeriesRef.current.applyOptions({ color: percentileTarget === 'DC component' ? rankColor : '#FF9800' });

    dataSeriesRef.current.setData(dataLine);
    freqSeriesRef.current.setData(freqLine);
    dcSeriesRef.current.setData(dcLine);
    reconSeriesRef.current.setData(reconWindow);

    // Clear existing percentile price lines (lightweight-charts removes via series.removePriceLine)
    for (const { series, line } of priceLinesRef.current) {
      try {
        series.removePriceLine(line);
      } catch {
        // ignore (e.g. if series already disposed)
      }
    }
    priceLinesRef.current = [];

    if (showPercentileLines && percentiles && Number.isFinite(percentiles.p50)) {
      const targetSeries =
        percentileTarget === 'data'
          ? dataSeriesRef.current
          : percentileTarget === 'DC component'
            ? dcSeriesRef.current
            : freqSeriesRef.current;

      const addLine = (price: number, title: string, color: string, width: number, style: LineStyle) => {
        if (!Number.isFinite(price)) return;
        const opts: PriceLineOptions = {
          price,
          title,
          color,
          lineWidth: width,
          lineStyle: style,
          axisLabelVisible: true,
        };
        priceLinesRef.current.push({ series: targetSeries, line: targetSeries.createPriceLine(opts) });
      };

      addLine(percentiles.p5, '5%', 'rgba(0,200,83,0.55)', 1, LineStyle.Dashed);
      addLine(percentiles.p15, '15%', 'rgba(174,234,0,0.55)', 1, LineStyle.Dashed);
      addLine(percentiles.p25, '25%', 'rgba(41,98,255,0.55)', 1, LineStyle.Dashed);
      addLine(percentiles.p50, '50%', 'rgba(120,123,134,0.55)', 2, LineStyle.Solid);
      addLine(percentiles.p75, '75%', 'rgba(255,235,59,0.55)', 1, LineStyle.Dashed);
      addLine(percentiles.p85, '85%', 'rgba(255,152,0,0.55)', 1, LineStyle.Dashed);
      addLine(percentiles.p95, '95%', 'rgba(239,83,80,0.55)', 1, LineStyle.Dashed);
    }

    chartRef.current?.timeScale().fitContent();
  }, [percentileTarget, percentiles, points, rankColor, reconWindow, showPercentileLines]);

  return <div ref={chartContainerRef} style={{ width: '100%' }} />;
}

export default function WeightedFourierTransformPage(props: { ticker: string }) {
  const { ticker } = props;

  const [days, setDays] = useState<number>(365);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Inputs (mirrors Pine defaults, with practical UI constraints)
  const [lengthInput, setLengthInput] = useState<number>(25);
  const [lambda, setLambda] = useState<number>(1);
  const [timeWeighting, setTimeWeighting] = useState(true);
  const [ivWeighting, setIvWeighting] = useState(false);
  const [detrend, setDetrend] = useState(true);
  const [degree, setDegree] = useState<number>(1);
  const [kLevel, setKLevel] = useState<number>(1);

  const [percentileLookback, setPercentileLookback] = useState<number>(200);
  const [percentileTarget, setPercentileTarget] = useState<PercentileTarget>('freq pass');
  const [showPercentileLines, setShowPercentileLines] = useState(true);
  const [showPercentileTable, setShowPercentileTable] = useState(true);

  const [points, setPoints] = useState<WFTPoint[]>([]);
  const [reconWindow, setReconWindow] = useState<LineData<UTCTimestamp>[]>([]);
  const [percentiles, setPercentiles] = useState<Percentiles | null>(null);

  const latestStats = useMemo(() => {
    const last = points.at(-1);
    if (!last) return null;
    return {
      mainFreq: last.mainFreq,
      mainPeriod: last.mainPeriod,
      currentRank: percentiles?.currentRank ?? NaN,
      targetValue: percentiles?.targetValue ?? NaN,
    };
  }, [percentiles, points]);

  const fetchAndCompute = useCallback(async () => {
    setIsLoading(true);
    setError(null);

    try {
      const res = await fetch(`${API_BASE_URL}/api/lower-extension/candles/${encodeURIComponent(ticker)}?days=${days}`);
      if (!res.ok) throw new Error(`Failed to fetch candles for ${ticker}`);
      const json = (await res.json()) as { candles?: Candle[] };
      const candles = (json.candles ?? []).filter(c => c.time && Number.isFinite(c.close));
      if (candles.length < 10) throw new Error('Not enough candles returned');

      const computed = computeWFTSeries({
        candles,
        lambda,
        lengthInput,
        timeWeighting,
        ivWeighting,
        detrend,
        degree,
        kLevel,
        percentileTarget,
        percentileLookback,
      });

      setPoints(computed.points);
      setReconWindow(computed.reconWindow);
      setPercentiles(computed.percentiles);
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Failed to compute WFT');
    } finally {
      setIsLoading(false);
    }
  }, [
    days,
    degree,
    detrend,
    ivWeighting,
    kLevel,
    lambda,
    lengthInput,
    percentileLookback,
    percentileTarget,
    ticker,
    timeWeighting,
  ]);

  useEffect(() => {
    void fetchAndCompute();
  }, [fetchAndCompute]);

  return (
    <Box>
      <Paper elevation={3} sx={{ p: 3, mb: 3 }}>
        <Box sx={{ display: 'flex', alignItems: 'baseline', justifyContent: 'space-between', gap: 2, mb: 2 }}>
          <Box>
            <Typography variant="h6">Weighted Fourier Transform (Spectral Gating + Percentiles)</Typography>
            <Typography variant="body2" color="text.secondary">
              Ticker: {ticker} • Plots `data`, `freq pass`, `DC component`, main frequency/period, and percentile bands.
            </Typography>
          </Box>
          <Box sx={{ display: 'flex', gap: 1, alignItems: 'center' }}>
            {isLoading && <CircularProgress size={22} />}
            <Button variant="contained" onClick={fetchAndCompute} disabled={isLoading}>
              Update
            </Button>
          </Box>
        </Box>

        <Box sx={{ display: 'grid', gap: 2, gridTemplateColumns: { xs: '1fr', md: 'repeat(6, 1fr)' } }}>
          <FormControl fullWidth>
            <InputLabel>Days</InputLabel>
            <Select value={days} label="Days" onChange={(e) => setDays(Number(e.target.value))}>
              <MenuItem value={180}>180</MenuItem>
              <MenuItem value={365}>365</MenuItem>
              <MenuItem value={750}>750</MenuItem>
            </Select>
          </FormControl>

          <FormControl fullWidth>
            <InputLabel>Length</InputLabel>
            <Select value={lengthInput} label="Length" onChange={(e) => setLengthInput(Number(e.target.value))}>
              <MenuItem value={0}>0 (expanding, cap 25)</MenuItem>
              <MenuItem value={10}>10</MenuItem>
              <MenuItem value={25}>25</MenuItem>
              <MenuItem value={40}>40</MenuItem>
              <MenuItem value={50}>50</MenuItem>
            </Select>
          </FormControl>

          <FormControl fullWidth>
            <InputLabel>Lambda</InputLabel>
            <Select value={lambda} label="Lambda" onChange={(e) => setLambda(Number(e.target.value))}>
              <MenuItem value={1}>1 (none)</MenuItem>
              <MenuItem value={0}>0 (ln/exp)</MenuItem>
            </Select>
          </FormControl>

          <FormControl fullWidth>
            <InputLabel>Detrend Degree</InputLabel>
            <Select value={degree} label="Detrend Degree" onChange={(e) => setDegree(Number(e.target.value))}>
              <MenuItem value={0}>0</MenuItem>
              <MenuItem value={1}>1</MenuItem>
              <MenuItem value={2}>2</MenuItem>
              <MenuItem value={3}>3</MenuItem>
            </Select>
          </FormControl>

          <FormControl fullWidth>
            <InputLabel>Gating Level (k)</InputLabel>
            <Select value={kLevel} label="Gating Level (k)" onChange={(e) => setKLevel(Number(e.target.value))}>
              <MenuItem value={-1}>-1 (no gating)</MenuItem>
              <MenuItem value={0}>0 (mild)</MenuItem>
              <MenuItem value={1}>1 (default)</MenuItem>
            </Select>
          </FormControl>

          <FormControl fullWidth>
            <InputLabel>Percentile Target</InputLabel>
            <Select
              value={percentileTarget}
              label="Percentile Target"
              onChange={(e) => setPercentileTarget(e.target.value as PercentileTarget)}
            >
              <MenuItem value="freq pass">freq pass</MenuItem>
              <MenuItem value="data">data</MenuItem>
              <MenuItem value="DC component">DC component</MenuItem>
            </Select>
          </FormControl>
        </Box>

        <Box sx={{ display: 'flex', gap: 2, alignItems: 'center', flexWrap: 'wrap', mt: 2 }}>
          <FormControlLabel
            control={<Checkbox checked={timeWeighting} onChange={(e) => setTimeWeighting(e.target.checked)} />}
            label="Time weighting"
          />
          <FormControlLabel
            control={<Checkbox checked={ivWeighting} onChange={(e) => setIvWeighting(e.target.checked)} />}
            label="Inferred volume weighting"
          />
          <FormControlLabel
            control={<Checkbox checked={detrend} onChange={(e) => setDetrend(e.target.checked)} />}
            label="Detrend"
          />
          <FormControlLabel
            control={
              <Checkbox
                checked={showPercentileLines}
                onChange={(e) => setShowPercentileLines(e.target.checked)}
              />
            }
            label="Show percentile lines"
          />
          <FormControlLabel
            control={
              <Checkbox
                checked={showPercentileTable}
                onChange={(e) => setShowPercentileTable(e.target.checked)}
              />
            }
            label="Show percentile table"
          />
        </Box>

        <Box sx={{ display: 'grid', gap: 2, gridTemplateColumns: { xs: '1fr', md: 'repeat(2, 1fr)' }, mt: 2 }}>
          <FormControl fullWidth>
            <InputLabel>Percentile Lookback</InputLabel>
            <Select
              value={percentileLookback}
              label="Percentile Lookback"
              onChange={(e) => setPercentileLookback(Number(e.target.value))}
            >
              <MenuItem value={50}>50</MenuItem>
              <MenuItem value={100}>100</MenuItem>
              <MenuItem value={200}>200</MenuItem>
              <MenuItem value={400}>400</MenuItem>
            </Select>
          </FormControl>

          {latestStats && (
            <Paper variant="outlined" sx={{ p: 2 }}>
              <Typography variant="subtitle2" color="text.secondary">
                Latest
              </Typography>
              <Typography variant="body2">
                Main freq: {latestStats.mainFreq ?? '—'} • Main period: {latestStats.mainPeriod ?? '—'}
              </Typography>
              <Typography variant="body2">
                Rank: {Number.isFinite(latestStats.currentRank) ? `${latestStats.currentRank.toFixed(1)}%` : '—'} •
                Target: {Number.isFinite(latestStats.targetValue) ? latestStats.targetValue.toFixed(4) : '—'}
              </Typography>
            </Paper>
          )}
        </Box>

        {error && (
          <Box sx={{ mt: 2 }}>
            <Alert severity="error">{error}</Alert>
          </Box>
        )}
      </Paper>

      <Paper elevation={3} sx={{ p: 2, mb: 3 }}>
        {points.length === 0 && !isLoading ? (
          <Box sx={{ py: 6, textAlign: 'center' }}>
            <Typography color="text.secondary">No data yet.</Typography>
          </Box>
        ) : (
          <WFTChart
            points={points}
            reconWindow={reconWindow}
            percentileTarget={percentileTarget}
            percentiles={percentiles}
            showPercentileLines={showPercentileLines}
          />
        )}
      </Paper>

      {showPercentileTable && percentiles && (
        <Paper elevation={3} sx={{ p: 3 }}>
          <Typography variant="h6" sx={{ mb: 1 }}>
            {percentileTarget} Percentiles
          </Typography>

          <Table size="small">
            <TableHead>
              <TableRow>
                <TableCell>Percentile</TableCell>
                <TableCell align="right">Value</TableCell>
                <TableCell align="right">Current</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {[
                ['5%', percentiles.p5],
                ['15%', percentiles.p15],
                ['25%', percentiles.p25],
                ['50%', percentiles.p50],
                ['75%', percentiles.p75],
                ['85%', percentiles.p85],
                ['95%', percentiles.p95],
              ].map(([label, value]) => (
                <TableRow key={label as string}>
                  <TableCell>{label}</TableCell>
                  <TableCell align="right">{Number.isFinite(value as number) ? (value as number).toFixed(4) : '—'}</TableCell>
                  <TableCell align="right">
                    {Number.isFinite(value as number) && Number.isFinite(percentiles.targetValue)
                      ? percentiles.targetValue >= (value as number)
                        ? '✓'
                        : '✗'
                      : '—'}
                  </TableCell>
                </TableRow>
              ))}
              <TableRow>
                <TableCell>
                  <strong>Current Rank</strong>
                </TableCell>
                <TableCell align="right">
                  {Number.isFinite(percentiles.currentRank) ? `${percentiles.currentRank.toFixed(1)}%` : '—'}
                </TableCell>
                <TableCell align="right">{Number.isFinite(percentiles.targetValue) ? percentiles.targetValue.toFixed(4) : '—'}</TableCell>
              </TableRow>
            </TableBody>
          </Table>
        </Paper>
      )}
    </Box>
  );
}
