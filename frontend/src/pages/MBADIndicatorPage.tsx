import { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import {
  Box,
  Button,
  CircularProgress,
  FormControl,
  InputLabel,
  MenuItem,
  Paper,
  Select,
  Typography,
} from '@mui/material';
import {
  ColorType,
  CrosshairMode,
  IChartApi,
  ISeriesApi,
  LineStyle,
  UTCTimestamp,
  createChart,
} from 'lightweight-charts';
import { MBAD_PINE_SCRIPT } from './RSIIndicatorPage';

type Props = {
  ticker: string;
};

type Candle = {
  time: string;
  open: number;
  high: number;
  low: number;
  close: number;
};

type MBADLevels = {
  lim_lower: number;
  ext_lower: number;
  dev_lower: number;
  dev_lower2: number;
  basis: number;
  dev_upper: number;
  ext_upper: number;
  lim_upper: number;
};

declare global {
  interface Window {
    TradingView?: any;
  }
}

function TradingViewChart({ ticker }: { ticker: string }) {
  const containerRef = useRef<HTMLDivElement | null>(null);
  const widgetId = useMemo(() => `tv-mbad-${ticker}-${Math.random().toString(36).slice(2, 7)}`, [ticker]);

  useEffect(() => {
    const ensureScript = () =>
      new Promise<void>((resolve) => {
        if (window.TradingView) return resolve();
        const script = document.createElement('script');
        script.id = 'tradingview-widget-script';
        script.src = 'https://s3.tradingview.com/tv.js';
        script.async = true;
        script.onload = () => resolve();
        document.head.appendChild(script);
      });

    let cancelled = false;
    ensureScript().then(() => {
      if (cancelled || !window.TradingView || !containerRef.current) return;
      containerRef.current.innerHTML = '';
      new window.TradingView.widget({
        width: '100%',
        height: 520,
        symbol: ticker,
        interval: '60',
        timezone: 'Etc/UTC',
        theme: 'dark',
        style: '1',
        locale: 'en',
        toolbar_bg: '#1E222D',
        hide_top_toolbar: false,
        hide_legend: false,
        allow_symbol_change: true,
        save_image: false,
        container_id: widgetId,
      });
    });

    return () => {
      cancelled = true;
    };
  }, [ticker, widgetId]);

  return <div id={widgetId} ref={containerRef} style={{ width: '100%', minHeight: 520 }} />;
}

function MBADLevelsChart(props: { candles: Candle[]; levels: MBADLevels | null }) {
  const { candles, levels } = props;
  const containerRef = useRef<HTMLDivElement | null>(null);
  const chartRef = useRef<IChartApi | null>(null);
  const candleSeriesRef = useRef<ISeriesApi<'Candlestick'> | null>(null);
  const priceLinesRef = useRef<Array<ReturnType<ISeriesApi<'Candlestick'>['createPriceLine']>>>([]);

  useEffect(() => {
    const el = containerRef.current;
    if (!el) return;

    const chart = createChart(el, {
      height: 520,
      width: el.clientWidth,
      layout: {
        background: { type: ColorType.Solid, color: '#1a1a1a' },
        textColor: '#d1d4dc',
      },
      grid: {
        vertLines: { color: '#2b2b43' },
        horzLines: { color: '#2b2b43' },
      },
      rightPriceScale: { borderColor: '#485c7b' },
      timeScale: { borderColor: '#485c7b', timeVisible: true, secondsVisible: false },
      crosshair: { mode: CrosshairMode.Normal },
    });

    chartRef.current = chart;
    candleSeriesRef.current = chart.addCandlestickSeries({
      upColor: '#26A69A',
      downColor: '#EF5350',
      borderUpColor: '#26A69A',
      borderDownColor: '#EF5350',
      wickUpColor: '#26A69A',
      wickDownColor: '#EF5350',
    });

    const handleResize = () => {
      const container = containerRef.current;
      if (!container || !chartRef.current) return;
      chartRef.current.applyOptions({ width: container.clientWidth });
    };
    window.addEventListener('resize', handleResize);

    return () => {
      window.removeEventListener('resize', handleResize);
      chartRef.current?.remove();
      chartRef.current = null;
      candleSeriesRef.current = null;
      priceLinesRef.current = [];
    };
  }, []);

  useEffect(() => {
    if (!candleSeriesRef.current || !chartRef.current) return;

    const formatted = candles.map((c) => ({
      time: (new Date(c.time).getTime() / 1000) as UTCTimestamp,
      open: c.open,
      high: c.high,
      low: c.low,
      close: c.close,
    }));
    candleSeriesRef.current.setData(formatted);

    // Clear existing price lines
    for (const line of priceLinesRef.current) {
      try {
        candleSeriesRef.current.removePriceLine(line);
      } catch {
        // ignore
      }
    }
    priceLinesRef.current = [];

    if (levels) {
      const addLine = (
        price: number,
        title: string,
        color: string,
        style: LineStyle = LineStyle.Solid,
        width = 1
      ) => {
        const opts = { price, title, color, lineStyle: style, lineWidth: width, axisLabelVisible: true };
        priceLinesRef.current.push(candleSeriesRef.current!.createPriceLine(opts));
      };

      addLine(levels.lim_lower, 'Lower Limit', '#ff5252', LineStyle.Dashed);
      addLine(levels.ext_lower, 'Lower Extension (Blue)', '#2962FF', LineStyle.Solid, 2);
      addLine(levels.dev_lower, 'Lower Deviation', '#9CA3AF', LineStyle.Solid);
      addLine(levels.dev_lower2, 'Lower Deviation 2', '#9CA3AF', LineStyle.Dotted);
      addLine(levels.basis, 'Mean', '#AB47BC', LineStyle.Solid, 2);
      addLine(levels.dev_upper, 'Upper Deviation', '#9CA3AF', LineStyle.Solid);
      addLine(levels.ext_upper, 'Upper Extension', '#ff9800', LineStyle.Solid, 2);
      addLine(levels.lim_upper, 'Upper Limit', '#ff5252', LineStyle.Dashed);
    }

    chartRef.current.timeScale().fitContent();
  }, [candles, levels]);

  return <div ref={containerRef} style={{ width: '100%' }} />;
}

export default function MBADIndicatorPage({ ticker }: Props) {
  const [copied, setCopied] = useState(false);
  const [days, setDays] = useState<number>(180);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [candles, setCandles] = useState<Candle[]>([]);
  const [levels, setLevels] = useState<MBADLevels | null>(null);

  const fetchData = useCallback(async () => {
    setIsLoading(true);
    setError(null);
    try {
      const [metricsRes, candlesRes] = await Promise.all([
        fetch(`/api/lower-extension/metrics/${encodeURIComponent(ticker)}?length=256&lookback_days=60`),
        fetch(`/api/lower-extension/candles/${encodeURIComponent(ticker)}?days=${days}`),
      ]);

      if (!metricsRes.ok) throw new Error(`Failed to fetch MBAD levels for ${ticker}`);
      if (!candlesRes.ok) throw new Error(`Failed to fetch candles for ${ticker}`);

      const metricsJson = await metricsRes.json();
      const candlesJson = await candlesRes.json();
      setCandles((candlesJson.candles || []) as Candle[]);
      setLevels((metricsJson.all_levels || null) as MBADLevels | null);
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Failed to load MBAD data');
    } finally {
      setIsLoading(false);
    }
  }, [days, ticker]);

  const handleCopy = useCallback(async () => {
    try {
      await navigator.clipboard.writeText(MBAD_PINE_SCRIPT);
      setCopied(true);
      setTimeout(() => setCopied(false), 1500);
    } catch {
      window.prompt('Copy MBAD Pine Script:', MBAD_PINE_SCRIPT);
    }
  }, []);

  useEffect(() => {
    void fetchData();
  }, [fetchData]);

  return (
    <Box>
      <Paper elevation={3} sx={{ p: 3, mb: 3 }}>
        <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: 2 }}>
          <Box>
            <Typography variant="h6">MBAD Indicator (Pine v6)</Typography>
            <Typography variant="body2" color="text.secondary">
              Live TradingView candle chart plus MBAD levels overlay (lower/upper extensions, deviations, mean).
            </Typography>
            <Typography variant="body2" color="text.secondary">
              Ticker: <strong>{ticker}</strong>
            </Typography>
          </Box>
          <Box sx={{ display: 'flex', gap: 1, alignItems: 'center' }}>
            <FormControl size="small" sx={{ minWidth: 140 }}>
              <InputLabel>Days</InputLabel>
              <Select value={days} label="Days" onChange={(e) => setDays(Number(e.target.value))} disabled={isLoading}>
                <MenuItem value={90}>90</MenuItem>
                <MenuItem value={180}>180</MenuItem>
                <MenuItem value={365}>365</MenuItem>
              </Select>
            </FormControl>
            <Button variant="outlined" onClick={fetchData} disabled={isLoading}>
              {isLoading ? <CircularProgress size={18} /> : 'Refresh'}
            </Button>
            <Button variant="contained" onClick={handleCopy}>
              {copied ? 'Copied' : 'Copy Pine'}
            </Button>
          </Box>
        </Box>
      </Paper>

      <Paper elevation={3} sx={{ p: 2, mb: 3 }}>
        {error ? (
          <Box sx={{ py: 4, textAlign: 'center' }}>
            <Typography color="error">{error}</Typography>
          </Box>
        ) : (
          <>
            <MBADLevelsChart candles={candles} levels={levels} />
            <Box sx={{ display: 'flex', gap: 3, flexWrap: 'wrap', mt: 2 }}>
              {levels && (
                <>
                  <Box>
                    <Typography variant="subtitle2" color="text.secondary">
                      Lower Bands
                    </Typography>
                    <Typography variant="body2">Limit: {levels.lim_lower?.toFixed(2)}</Typography>
                    <Typography variant="body2">Extension (blue): {levels.ext_lower?.toFixed(2)}</Typography>
                    <Typography variant="body2">Deviation: {levels.dev_lower?.toFixed(2)}</Typography>
                    <Typography variant="body2">Deviation 2: {levels.dev_lower2?.toFixed(2)}</Typography>
                  </Box>
                  <Box>
                    <Typography variant="subtitle2" color="text.secondary">
                      Center
                    </Typography>
                    <Typography variant="body2">Mean: {levels.basis?.toFixed(2)}</Typography>
                  </Box>
                  <Box>
                    <Typography variant="subtitle2" color="text.secondary">
                      Upper Bands
                    </Typography>
                    <Typography variant="body2">Deviation: {levels.dev_upper?.toFixed(2)}</Typography>
                    <Typography variant="body2">Extension: {levels.ext_upper?.toFixed(2)}</Typography>
                    <Typography variant="body2">Limit: {levels.lim_upper?.toFixed(2)}</Typography>
                  </Box>
                </>
              )}
            </Box>
          </>
        )}
      </Paper>

      <Paper elevation={3} sx={{ p: 3 }}>
        <Typography variant="h6" sx={{ mb: 1 }}>
          Pine Script (copy and paste into TradingView)
        </Typography>
        <Box
          component="pre"
          sx={{
            p: 2,
            borderRadius: 1,
            bgcolor: 'background.default',
            color: 'text.primary',
            fontFamily: 'ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace',
            fontSize: '0.85rem',
            whiteSpace: 'pre-wrap',
            wordBreak: 'break-word',
          }}
        >
          {MBAD_PINE_SCRIPT}
        </Box>
        {copied && (
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mt: 1, color: 'success.main' }}>
            <CircularProgress size={14} thickness={10} sx={{ color: 'success.main' }} />
            <Typography variant="caption">Copied to clipboard</Typography>
          </Box>
        )}
      </Paper>
    </Box>
  );
}
