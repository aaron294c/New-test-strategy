import { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import {
  Alert,
  Box,
  Button,
  CircularProgress,
  FormControl,
  InputLabel,
  MenuItem,
  Paper,
  Select,
  Snackbar,
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableRow,
  TextField,
  Typography,
} from '@mui/material';
import { CandlestickData, createChart, IChartApi, ISeriesApi, LineData, UTCTimestamp } from 'lightweight-charts';

const PINE_SCRIPT = String.raw`//@version=6
indicator('Index Construction Tool - Normalized', 'ICT-Norm', precision = 4)
//by gorx1, modified for balanced exposure
// dependencies........................................................................................................
ivd(cl, op, tick_size, multi = 256) => multi * (cl - op) / tick_size
iv(cl, lo, hi, op, tick_size, multi = 256) => 
    hc = math.abs(hi - cl)
    lc = math.abs(lo - cl)
    iv = cl > op ? (op - lo) + (hi - lo) + (hi - cl) :
         cl < op ? (hi - op) + (hi - lo) + (cl - lo) :
         hc < lc ? (op - lo) + (hi - lo) + (hi - cl) :
         hc > lc ? (hi - op) + (hi - lo) + (cl - lo) :
         (op - lo) + (hi - lo) + (hi - cl)
    multi * iv / tick_size + 1
itc(hi, lo, tick_size, multi = 256) => multi * (hi - lo) / tick_size + 1
ch_mean_weights(arr) =>
    sum = arr.sum()
    out = array.new_float(arr.size())
    for [i, v] in arr
        out.set(i, v / sum)
    out
// dependencies........................................................................................................
// data................................................................................................................
LIST_INIT = 'NASDAQ:NVDA\nNASDAQ:AAPL\nNASDAQ:MSFT\nNASDAQ:AMZN\nNASDAQ:GOOGL\nNASDAQ:META\nNASDAQ:AVGO\nNASDAQ:TSLA\nNYSE:LLY\nNASDAQ:NFLX\nNYSE:BRK.B'
list = input.text_area(LIST_INIT, 'symbols')
lookback = input.int(1, 'Normalization lookback bars (0 = no normalization, original absolute prices)')
exp = array.from(open, high, low, close, hl2, hl2,
                 ivd(close, open, syminfo.mintick),
                 iv(close, low, high, open, syminfo.mintick),
                 itc(high, low, syminfo.mintick),
                 syminfo.mintick, syminfo.pointvalue, syminfo.mincontract)
symbols = str.split(str.trim(list), '\n')
fields = exp.size()
legs = symbols.size()
data = matrix.new<float>(legs, fields)
base_close = array.new_float(legs)
for i = 0 to legs - 1
    sec_exp = request.security(symbols.get(i), timeframe.period, exp)
    data.add_row(i, sec_exp)
    if lookback > 0
        base_close.set(i, request.security(symbols.get(i), timeframe.period, close[lookback]))
    else
        base_close.set(i, 1.0)  // no division
// Normalize data if lookback > 0
if lookback > 0
    for i = 0 to legs - 1
        bc = base_close.get(i)
        if bc != 0
            for f = 0 to 8  // only normalize price fields (0-8), not mintick/pv etc.
                data.set(i, f, data.get(i, f) / bc)
// data................................................................................................................
// main................................................................................................................
mode = input.string('addition', 'Index construction by', ['addition', 'subtraction'])
weights = matrix.new<float>(legs, fields)
for f = 0 to fields - 1
    w = ch_mean_weights(data.col(f))
    for i = 0 to legs - 1
        weights.set(i, f, w.get(i))
// construct bars (same as original)
bar = array.new_float(fields)
for f = 0 to fields - 1
    acc = 0.
    for i = 0 to legs - 1
        w = weights.get(i, f)
        dw = data.get(i, f) * w
        if i == 0
            acc := dw
        else
            switch mode
                'addition' => acc += dw
                'subtraction' => acc -= dw
    bar.set(f, acc)
op = bar.get(0)
hi = bar.get(1)
lo = bar.get(2)
cl = bar.get(3)
bt = bar.get(4)
st = bar.get(5)
ivd = bar.get(6)
iv = bar.get(7)
itc = bar.get(8)
mp = (op * 1 + hi * 2 + lo * 2 + cl * 3 + bt * 2 + st * 2) / 12
// output weights (multiplied by pointvalue as before)
ow = array.new_float(legs)
for [i, v] in ow
    op_w = weights.get(i, 0)
    hi_w = weights.get(i, 1)
    lo_w = weights.get(i, 2)
    cl_w = weights.get(i, 3)
    bt_w = weights.get(i, 4)
    st_w = weights.get(i, 5)
    ow.set(i, (op_w * 1 + hi_w * 2 + lo_w * 2 + cl_w * 3 + bt_w * 2 + st_w * 2) / 12 * data.get(i, 10))
// visuals.............................................................................................................
color_dn = color.red
color_nt = color.purple
color_up = color.blue
color_cs = cl > op ? color_up : cl < op ? color_dn : color_nt
// ... (rest of visuals same as your original script)
var table info = table.new(position.top_right, 2, legs)
if barstate.islast
    for [i, v] in symbols
        table.cell(info, 0, i, v , text_color = color.gray)
        table.cell(info, 1, i, str.tostring(ow.get(i), '0.0000'), text_color = color.gray)
// ∞`;

type Mode = 'addition' | 'subtraction';

type Candle = {
  time: string;
  open: number;
  high: number;
  low: number;
  close: number;
};

type ICTBar = {
  time: UTCTimestamp;
  open: number;
  high: number;
  low: number;
  close: number;
  mp: number;
};

type LastBarWeightsRow = {
  symbol: string;
  ticker: string;
  lastClose: number;
  mpWeight: number;
};

const LIST_INIT =
  'NASDAQ:NVDA\nNASDAQ:AAPL\nNASDAQ:MSFT\nNASDAQ:AMZN\nNASDAQ:GOOGL\nNASDAQ:META\nNASDAQ:AVGO\nNASDAQ:TSLA\nNYSE:LLY\nNASDAQ:NFLX\nNYSE:BRK.B';

function toYahooTicker(inputSymbol: string) {
  const trimmed = inputSymbol.trim();
  if (!trimmed) return '';
  const withoutExchange = trimmed.includes(':') ? trimmed.split(':').at(-1) ?? '' : trimmed;
  return withoutExchange.replaceAll('.', '-').toUpperCase();
}

function parseSymbols(text: string) {
  return text
    .split('\n')
    .map(s => s.trim())
    .filter(Boolean);
}

function normalizeWeights(values: number[]) {
  const sum = values.reduce((acc, v) => acc + v, 0);
  if (!Number.isFinite(sum) || sum === 0) return values.map(() => 1 / values.length);
  return values.map(v => v / sum);
}

function computeICTBars(params: {
  symbols: string[];
  tickers: string[];
  candlesByTicker: Record<string, Candle[]>;
  mode: Mode;
  normalizationLookbackBars: number;
  tickSize?: number;
}) {
  const { symbols, tickers, candlesByTicker, mode, normalizationLookbackBars, tickSize = 0.01 } = params;

  const maps = new Map<string, Map<string, Candle>>();
  const indexMaps = new Map<string, Map<string, number>>();
  const sortedCandlesByTicker = new Map<string, Candle[]>();
  for (const ticker of tickers) {
    const sortedCandles = [...(candlesByTicker[ticker] ?? [])].sort((a, b) => a.time.localeCompare(b.time));
    sortedCandlesByTicker.set(ticker, sortedCandles);

    const candleMap = new Map<string, Candle>();
    const indexMap = new Map<string, number>();
    for (let i = 0; i < sortedCandles.length; i++) {
      const c = sortedCandles[i];
      candleMap.set(c.time, c);
      indexMap.set(c.time, i);
    }
    maps.set(ticker, candleMap);
    indexMaps.set(ticker, indexMap);
  }

  const firstTicker = tickers[0];
  if (!firstTicker) return { bars: [] as ICTBar[], lastWeights: [] as LastBarWeightsRow[] };

  let commonTimes = Array.from(maps.get(firstTicker)?.keys() ?? []);
  for (const ticker of tickers.slice(1)) {
    const m = maps.get(ticker);
    if (!m) return { bars: [] as ICTBar[], lastWeights: [] as LastBarWeightsRow[] };
    const has = (t: string) => m.has(t);
    commonTimes = commonTimes.filter(has);
  }
  commonTimes.sort();

  const legs = tickers.length;
  const bars: ICTBar[] = [];

  let lastOpenWeights: number[] = [];
  let lastHighWeights: number[] = [];
  let lastLowWeights: number[] = [];
  let lastCloseWeights: number[] = [];
  let lastHL2Weights: number[] = [];

  for (const timeStr of commonTimes) {
    const opens: number[] = [];
    const highs: number[] = [];
    const lows: number[] = [];
    const closes: number[] = [];
    const hl2s: number[] = [];

    for (const ticker of tickers) {
      const c = maps.get(ticker)?.get(timeStr);
      if (!c) continue;

      let baseClose = 1;
      if (normalizationLookbackBars > 0) {
        const idx = indexMaps.get(ticker)?.get(timeStr);
        const baseIdx = typeof idx === 'number' ? idx - normalizationLookbackBars : -1;
        const baseCandle = baseIdx >= 0 ? (sortedCandlesByTicker.get(ticker) ?? [])[baseIdx] : undefined;
        if (baseCandle && baseCandle.close !== 0) baseClose = baseCandle.close;
      }

      opens.push(c.open / baseClose);
      highs.push(c.high / baseClose);
      lows.push(c.low / baseClose);
      closes.push(c.close / baseClose);
      hl2s.push(((c.high + c.low) / 2) / baseClose);
    }

    if (opens.length !== legs) continue;

    const openW = normalizeWeights(opens);
    const highW = normalizeWeights(highs);
    const lowW = normalizeWeights(lows);
    const closeW = normalizeWeights(closes);
    const hl2W = normalizeWeights(hl2s);

    const reduceFeature = (values: number[], weights: number[]) => {
      if (mode === 'addition') return values.reduce((acc, v, i) => acc + v * weights[i], 0);
      const head = values[0] * weights[0];
      const tail = values.slice(1).reduce((acc, v, i) => acc + v * weights[i + 1], 0);
      return head - tail;
    };

    const op = reduceFeature(opens, openW);
    const hi = reduceFeature(highs, highW);
    const lo = reduceFeature(lows, lowW);
    const cl = reduceFeature(closes, closeW);
    const bt = reduceFeature(hl2s, hl2W);
    const st = bt;

    const mp = (op * 1 + hi * 2 + lo * 2 + cl * 3 + bt * 2 + st * 2) / 12;

    const t = (new Date(timeStr).getTime() / 1000) as UTCTimestamp;
    bars.push({
      time: t,
      open: op,
      high: hi,
      low: lo,
      close: cl,
      mp,
    });

    lastOpenWeights = openW;
    lastHighWeights = highW;
    lastLowWeights = lowW;
    lastCloseWeights = closeW;
    lastHL2Weights = hl2W;
  }

  const lastWeights: LastBarWeightsRow[] = tickers.map((ticker, i) => {
    const mpWeight =
      (lastOpenWeights[i] * 1 +
        lastHighWeights[i] * 2 +
        lastLowWeights[i] * 2 +
        lastCloseWeights[i] * 3 +
        lastHL2Weights[i] * 2 +
        lastHL2Weights[i] * 2) /
      12;

    const lastCommonTime = commonTimes.at(-1);
    const last = lastCommonTime ? maps.get(ticker)?.get(lastCommonTime) : undefined;
    return {
      symbol: symbols[i] ?? ticker,
      ticker,
      lastClose: last?.close ?? NaN,
      mpWeight: Number.isFinite(mpWeight) ? mpWeight : 0,
    };
  });

  // Keep tickSize reference (matches Pine shape); it’s used in iv/ivd/itc in Pine but not charted here yet.
  void tickSize;

  return { bars, lastWeights };
}

function ICTChart({ bars }: { bars: ICTBar[] }) {
  const chartContainerRef = useRef<HTMLDivElement | null>(null);
  const chartRef = useRef<IChartApi | null>(null);
  const candleSeriesRef = useRef<ISeriesApi<'Candlestick'> | null>(null);
  const mpSeriesRef = useRef<ISeriesApi<'Line'> | null>(null);

  useEffect(() => {
    const el = chartContainerRef.current;
    if (!el) return;

    const chart = createChart(el, {
      width: el.clientWidth,
      height: 460,
      layout: {
        background: { color: '#1a1a1a' },
        textColor: '#d1d4dc',
      },
      grid: {
        vertLines: { color: '#2b2b43' },
        horzLines: { color: '#2b2b43' },
      },
      rightPriceScale: {
        borderColor: '#485c7b',
      },
      timeScale: {
        borderColor: '#485c7b',
        timeVisible: true,
        secondsVisible: false,
      },
      crosshair: { mode: 1 },
    });

    chartRef.current = chart;

    candleSeriesRef.current = chart.addCandlestickSeries({
      upColor: '#9C27B0',
      downColor: '#9C27B0',
      borderVisible: false,
      wickUpColor: '#9C27B0',
      wickDownColor: '#9C27B0',
    });

    mpSeriesRef.current = chart.addLineSeries({
      color: '#D1D4DC',
      lineWidth: 2,
      title: 'MP',
      priceLineVisible: true,
      lastValueVisible: true,
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
      candleSeriesRef.current = null;
      mpSeriesRef.current = null;
    };
  }, []);

  useEffect(() => {
    if (!candleSeriesRef.current || !mpSeriesRef.current) return;
    if (bars.length === 0) return;

    const candleData: CandlestickData<UTCTimestamp>[] = bars.map(b => ({
      time: b.time,
      open: b.open,
      high: b.high,
      low: b.low,
      close: b.close,
    }));

    const mpData: LineData<UTCTimestamp>[] = bars.map(b => ({
      time: b.time,
      value: b.mp,
    }));

    candleSeriesRef.current.setData(candleData);
    mpSeriesRef.current.setData(mpData);
    chartRef.current?.timeScale().fitContent();
  }, [bars]);

  return <div ref={chartContainerRef} style={{ width: '100%' }} />;
}

export default function IndexConstructionToolPage() {
  const [symbolsText, setSymbolsText] = useState(LIST_INIT);
  const [mode, setMode] = useState<Mode>('addition');
  const [days, setDays] = useState<number>(180);
  const [normalizationLookbackBars, setNormalizationLookbackBars] = useState<number>(1);

  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [bars, setBars] = useState<ICTBar[]>([]);
  const [lastWeights, setLastWeights] = useState<LastBarWeightsRow[]>([]);
  const [snackbarOpen, setSnackbarOpen] = useState(false);
  const [pineOpen, setPineOpen] = useState(false);

  const handleCopy = useCallback(async () => {
    try {
      await navigator.clipboard.writeText(PINE_SCRIPT);
      setSnackbarOpen(true);
    } catch {
      window.prompt('Copy Pine Script:', PINE_SCRIPT);
    }
  }, []);

  const parsedSymbols = useMemo(() => parseSymbols(symbolsText), [symbolsText]);
  const tickers = useMemo(() => parsedSymbols.map(toYahooTicker).filter(Boolean), [parsedSymbols]);

  const fetchAndCompute = useCallback(async () => {
    setIsLoading(true);
    setError(null);
    setBars([]);
    setLastWeights([]);

    try {
      if (parsedSymbols.length < 2) {
        setError('Add at least 2 symbols.');
        return;
      }

      const candlesByTicker: Record<string, Candle[]> = {};
      const results = await Promise.all(
        tickers.map(async (ticker) => {
          const res = await fetch(`/api/lower-extension/candles/${encodeURIComponent(ticker)}?days=${days}`);
          if (!res.ok) throw new Error(`Failed to fetch candles for ${ticker}`);
          const data = (await res.json()) as { candles?: Candle[] };
          return { ticker, candles: data.candles ?? [] };
        })
      );

      for (const r of results) candlesByTicker[r.ticker] = r.candles;

      const computed = computeICTBars({
        symbols: parsedSymbols,
        tickers,
        candlesByTicker,
        mode,
        normalizationLookbackBars,
      });

      if (computed.bars.length === 0) {
        setError('Not enough overlapping candle history across all symbols.');
        return;
      }

      setBars(computed.bars);
      setLastWeights(computed.lastWeights.sort((a, b) => b.mpWeight - a.mpWeight));
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Failed to compute index');
    } finally {
      setIsLoading(false);
    }
  }, [days, mode, normalizationLookbackBars, parsedSymbols, tickers]);

  useEffect(() => {
    // Auto-run once with defaults for a “TradingView indicator” feel.
    void fetchAndCompute();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  return (
    <Box>
      <Paper elevation={3} sx={{ p: 3, mb: 3 }}>
        <Box sx={{ display: 'flex', alignItems: 'baseline', justifyContent: 'space-between', gap: 2, mb: 2 }}>
          <Box>
            <Typography variant="h6">Index Construction Tool (ICT)</Typography>
            <Typography variant="body2" color="text.secondary">
              Visual replica of your Pine logic: normalized synthetic OHLC + MP line and last-bar component weights.
            </Typography>
          </Box>
          <Box sx={{ display: 'flex', gap: 1, flexWrap: 'wrap', justifyContent: 'flex-end' }}>
            <Button variant="outlined" onClick={() => setPineOpen(v => !v)}>
              {pineOpen ? 'Hide Pine' : 'Show Pine'}
            </Button>
            <Button variant="outlined" onClick={handleCopy}>
              Copy Pine
            </Button>
          </Box>
        </Box>

        <Box sx={{ display: 'grid', gap: 2, gridTemplateColumns: { xs: '1fr', md: '2fr 1fr 1fr 1fr' } }}>
          <TextField
            label="Symbols (TradingView format ok)"
            fullWidth
            multiline
            minRows={4}
            value={symbolsText}
            onChange={(e) => setSymbolsText(e.target.value)}
            helperText={`Parsed: ${tickers.join(', ')}`}
          />

          <FormControl fullWidth>
            <InputLabel>Mode</InputLabel>
            <Select value={mode} label="Mode" onChange={(e) => setMode(e.target.value as Mode)}>
              <MenuItem value="addition">addition</MenuItem>
              <MenuItem value="subtraction">subtraction</MenuItem>
            </Select>
          </FormControl>

          <FormControl fullWidth>
            <InputLabel>Days</InputLabel>
            <Select value={days} label="Days" onChange={(e) => setDays(Number(e.target.value))}>
              <MenuItem value={60}>60</MenuItem>
              <MenuItem value={120}>120</MenuItem>
              <MenuItem value={180}>180</MenuItem>
              <MenuItem value={252}>252</MenuItem>
              <MenuItem value={500}>500</MenuItem>
            </Select>
          </FormControl>

          <FormControl fullWidth>
            <InputLabel>Normalization Lookback</InputLabel>
            <Select
              value={normalizationLookbackBars}
              label="Normalization Lookback"
              onChange={(e) => setNormalizationLookbackBars(Number(e.target.value))}
            >
              <MenuItem value={0}>0 (off)</MenuItem>
              <MenuItem value={1}>1</MenuItem>
              <MenuItem value={5}>5</MenuItem>
              <MenuItem value={20}>20</MenuItem>
              <MenuItem value={63}>63</MenuItem>
            </Select>
          </FormControl>
        </Box>

        <Box sx={{ display: 'flex', gap: 2, alignItems: 'center', mt: 2 }}>
          <Button variant="contained" onClick={fetchAndCompute} disabled={isLoading}>
            {isLoading ? 'Computing…' : 'Update'}
          </Button>
          {isLoading && <CircularProgress size={22} />}
        </Box>

        {error && (
          <Box sx={{ mt: 2 }}>
            <Alert severity="error">{error}</Alert>
          </Box>
        )}
      </Paper>

      <Paper elevation={3} sx={{ p: 2, mb: 3 }}>
        {bars.length === 0 && !isLoading ? (
          <Box sx={{ py: 6, textAlign: 'center' }}>
            <Typography color="text.secondary">No synthetic series yet.</Typography>
          </Box>
        ) : (
          <ICTChart bars={bars} />
        )}
      </Paper>

      <Paper elevation={3} sx={{ p: 3, mb: 3 }}>
        <Typography variant="h6" sx={{ mb: 1 }}>
          Component Weights (last bar)
        </Typography>
        <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
          MP weight uses your formula: average of per-field weights for O/H/L/C/HL2/HL2.
        </Typography>

        <Table size="small">
          <TableHead>
            <TableRow>
              <TableCell>Symbol</TableCell>
              <TableCell>Ticker</TableCell>
              <TableCell align="right">Last Close</TableCell>
              <TableCell align="right">MP Weight</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {lastWeights.map((row) => (
              <TableRow key={row.ticker}>
                <TableCell>{row.symbol}</TableCell>
                <TableCell>{row.ticker}</TableCell>
                <TableCell align="right">{Number.isFinite(row.lastClose) ? row.lastClose.toFixed(2) : '—'}</TableCell>
                <TableCell align="right">{(row.mpWeight * 100).toFixed(2)}%</TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </Paper>

      {pineOpen && (
        <Paper elevation={3} sx={{ p: 3 }}>
          <Typography variant="h6" sx={{ mb: 2 }}>
            Pine Script
          </Typography>
          <TextField
            fullWidth
            multiline
            minRows={18}
            value={PINE_SCRIPT}
            InputProps={{ readOnly: true }}
            sx={{
              '& .MuiInputBase-input': {
                fontFamily: 'ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace',
                fontSize: '0.85rem',
                lineHeight: 1.5,
              },
            }}
          />
        </Paper>
      )}

      <Snackbar
        open={snackbarOpen}
        autoHideDuration={2500}
        onClose={() => setSnackbarOpen(false)}
        message="Pine Script copied to clipboard"
      />
    </Box>
  );
}
