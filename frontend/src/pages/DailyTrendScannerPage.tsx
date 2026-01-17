import { useEffect, useMemo, useRef, useState } from 'react';
import {
  Box,
  Button,
  CircularProgress,
  FormControl,
  Grid,
  InputLabel,
  MenuItem,
  Paper,
  Select,
  Switch,
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableRow,
  TextField,
  Typography,
} from '@mui/material';
import { useQuery } from '@tanstack/react-query';
import { createChart, CrosshairMode, IChartApi, ISeriesApi, LineStyle, UTCTimestamp } from 'lightweight-charts';

import { dailyTrendApi } from '@/api/client';
import type { DailyTrendBatchResponse, DailyTrendCandle, DailyTrendLevels, DailyTrendSymbolData } from '@/types';

type SortingMode = 'None' | 'Chg %' | 'Bullish' | 'Bearish';
type TrendStyle = 'Text' | 'Symbols white' | 'Symbols black';
type NeutralIcon = '⚠️' | '⌛' | '⏳' | '🕖' | '🚫' | '⁉️';

const DEFAULT_WATCHLIST = [
  'SPY',
  'QQQ',
  'AAPL',
  'NVDA',
  'MSFT',
  'TSLA',
  'GOOG',
  'META',
  'AMZN',
  'AVGO',
  'AMD',
  'PLTR',
  'COIN',
  'NFLX',
  'HOOD',
  'SNOW',
  'SOFI',
  'TSM',
  'ARM',
  'IWM',
];

function calcBoxes(price: number, midpoint: number, target: number, isHigh: boolean): number {
  if (!Number.isFinite(price) || !Number.isFinite(midpoint) || !Number.isFinite(target)) return 0;
  if (isHigh) {
    const rangeToTarget = target - midpoint;
    if (rangeToTarget <= 0) return 0;
    if (price <= midpoint || price >= target) return 0;
    const progress = (price - midpoint) / rangeToTarget;
    if (progress >= 0.8) return 5;
    if (progress >= 0.6) return 4;
    if (progress >= 0.4) return 3;
    if (progress >= 0.2) return 2;
    return 1;
  }
  const rangeToTarget = midpoint - target;
  if (rangeToTarget <= 0) return 0;
  if (price >= midpoint || price <= target) return 0;
  const progress = (midpoint - price) / rangeToTarget;
  if (progress >= 0.8) return 5;
  if (progress >= 0.6) return 4;
  if (progress >= 0.4) return 3;
  if (progress >= 0.2) return 2;
  return 1;
}

function buildDisplay(boxes: number): string {
  if (boxes === 5) return '▓▓▓▓▓';
  if (boxes === 4) return '▓▓▓▓▒';
  if (boxes === 3) return '▓▓▓▒▒';
  if (boxes === 2) return '▓▓▒▒▒';
  if (boxes === 1) return '▓▒▒▒▒';
  return '▒▒▒▒▒';
}

function computeTrend(levels: DailyTrendLevels, price: number | null): 'Bullish' | 'Bearish' | 'Neutral' {
  if (price == null) return 'Neutral';
  const abovePDH = levels.pdh != null && price > levels.pdh;
  const abovePMH = levels.pmh != null && price > levels.pmh;
  const belowPDL = levels.pdl != null && price < levels.pdl;
  const belowPML = levels.pml != null && price < levels.pml;
  if (abovePDH && abovePMH) return 'Bullish';
  if (belowPDL && belowPML) return 'Bearish';
  return 'Neutral';
}

function DailyTrendChart({ candles, levels }: { candles: DailyTrendCandle[]; levels: DailyTrendLevels | null }) {
  const containerRef = useRef<HTMLDivElement | null>(null);
  const chartRef = useRef<IChartApi | null>(null);
  const candleSeriesRef = useRef<ISeriesApi<'Candlestick'> | null>(null);
  const priceLinesRef = useRef<Array<ReturnType<ISeriesApi<'Candlestick'>['createPriceLine']>>>([]);

  useEffect(() => {
    const container = containerRef.current;
    if (!container) return;

    const chart = createChart(container, {
      width: container.clientWidth,
      height: 420,
      layout: { background: { color: '#131722' }, textColor: '#D1D4DC' },
      grid: { vertLines: { color: '#2A2E39' }, horzLines: { color: '#2A2E39' } },
      crosshair: { mode: CrosshairMode.Normal },
      rightPriceScale: { borderColor: '#2A2E39' },
      timeScale: { borderColor: '#2A2E39', timeVisible: true, secondsVisible: false },
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
      if (!containerRef.current || !chartRef.current) return;
      chartRef.current.applyOptions({ width: containerRef.current.clientWidth });
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
    if (!chartRef.current || !candleSeriesRef.current) return;

    const formatted = candles
      .filter((c) => c.open != null && c.high != null && c.low != null && c.close != null)
      .map((c) => ({
        time: (new Date(c.time).getTime() / 1000) as UTCTimestamp,
        open: c.open as number,
        high: c.high as number,
        low: c.low as number,
        close: c.close as number,
      }));

    candleSeriesRef.current.setData(formatted);

    for (const line of priceLinesRef.current) {
      try {
        candleSeriesRef.current.removePriceLine(line);
      } catch {
        // ignore
      }
    }
    priceLinesRef.current = [];

    if (levels) {
      const addLine = (price: number, title: string, color: string, style: LineStyle, width = 1) => {
        priceLinesRef.current.push(
          candleSeriesRef.current!.createPriceLine({
            price,
            title,
            color,
            lineStyle: style,
            lineWidth: width,
            axisLabelVisible: true,
          })
        );
      };

      if (levels.pdh != null) addLine(levels.pdh, 'PDH', '#FFFFFF', LineStyle.Solid, 1);
      if (levels.pdl != null) addLine(levels.pdl, 'PDL', '#FFFFFF', LineStyle.Solid, 1);
      if (levels.pmh != null) addLine(levels.pmh, 'PMH', '#FF9800', LineStyle.Dashed, 1);
      if (levels.pml != null) addLine(levels.pml, 'PML', '#FF9800', LineStyle.Dashed, 1);
      if (levels.orb_high != null) addLine(levels.orb_high, 'ORB H', '#4CAF50', LineStyle.Dotted, 1);
      if (levels.orb_low != null) addLine(levels.orb_low, 'ORB L', '#4CAF50', LineStyle.Dotted, 1);
    }

    chartRef.current.timeScale().fitContent();
  }, [candles, levels]);

  return <div ref={containerRef} style={{ width: '100%' }} />;
}

function formatMaybe(value: number | null | undefined, digits = 2): string {
  if (value == null || !Number.isFinite(value)) return '';
  return value.toFixed(digits);
}

function parseWatchlistInput(input: string): string[] {
  const parts = input
    .split(/[\s,]+/)
    .map((s) => s.trim().toUpperCase())
    .filter(Boolean);
  return Array.from(new Set(parts)).slice(0, 50);
}

export default function DailyTrendScannerPage({ ticker }: { ticker: string }) {
  const [interval, setInterval] = useState<string>('5m');
  const [days, setDays] = useState<number>(5);
  const [orbMinutes, setOrbMinutes] = useState<number>(5);

  const [watchlistInput, setWatchlistInput] = useState<string>(DEFAULT_WATCHLIST.join(', '));
  const watchlist = useMemo(() => parseWatchlistInput(watchlistInput), [watchlistInput]);

  const [sorting, setSorting] = useState<SortingMode>('Bullish');
  const [showProgressBars, setShowProgressBars] = useState(true);
  const [showPMValues, setShowPMValues] = useState(false);
  const [showPDValues, setShowPDValues] = useState(false);
  const [trendStyle, setTrendStyle] = useState<TrendStyle>('Symbols white');
  const [neutralIcon, setNeutralIcon] = useState<NeutralIcon>('⌛');
  const [autoRefresh, setAutoRefresh] = useState<boolean>(false);

  const singleQuery = useQuery({
    queryKey: ['dailyTrend', ticker, interval, days, orbMinutes],
    queryFn: () =>
      dailyTrendApi.getDailyTrend(ticker, { interval, days, orb_minutes: orbMinutes, include_candles: true }),
    staleTime: 20_000,
    refetchInterval: autoRefresh ? 60_000 : false,
  });

  const batchQuery = useQuery({
    queryKey: ['dailyTrendBatch', watchlist.join('|'), interval, days, orbMinutes],
    queryFn: () =>
      dailyTrendApi.getDailyTrendBatch({ symbols: watchlist, interval, days, orb_minutes: orbMinutes }),
    enabled: watchlist.length > 0,
    staleTime: 20_000,
    refetchInterval: autoRefresh ? 60_000 : false,
  });

  const single = singleQuery.data || null;
  const singleLevels = single?.levels ?? null;

  const singleTrend = useMemo(() => (singleLevels ? computeTrend(singleLevels, single?.price ?? null) : 'Neutral'), [
    singleLevels,
    single?.price,
  ]);

  const singleTrendDisplay = useMemo(() => {
    if (trendStyle === 'Text') return singleTrend;
    if (singleTrend === 'Bullish') return '▲';
    if (singleTrend === 'Bearish') return '▼';
    return neutralIcon;
  }, [singleTrend, trendStyle, neutralIcon]);

  const singleTrendBg = singleTrend === 'Bullish' ? '#4caf50' : singleTrend === 'Bearish' ? '#f44336' : '#6b728080';
  const singleTrendTextColor =
    trendStyle === 'Text' ? '#FFFFFF' : singleTrend === 'Neutral' ? '#FFFFFF' : trendStyle === 'Symbols white' ? '#FFFFFF' : '#111827';

  const batch = batchQuery.data || (null as DailyTrendBatchResponse | null);

  const sortedRows = useMemo(() => {
    const data = batch?.data || {};
    const rows: Array<{ symbol: string; payload: DailyTrendSymbolData | null }> = watchlist.map((sym) => ({
      symbol: sym,
      payload: data[sym] || data[sym.toUpperCase()] || null,
    }));

    const scoreFor = (row: { symbol: string; payload: DailyTrendSymbolData | null }): number => {
      const p = row.payload;
      const price = p?.price ?? null;
      const chg = p?.chg_pct ?? 0;
      const levels = p?.levels;
      const abovePDH = !!(price != null && levels?.pdh != null && price > levels.pdh);
      const abovePMH = !!(price != null && levels?.pmh != null && price > levels.pmh);
      const belowPDL = !!(price != null && levels?.pdl != null && price < levels.pdl);
      const belowPML = !!(price != null && levels?.pml != null && price < levels.pml);
      const isBullish = abovePDH && abovePMH;
      const isBearish = belowPDL && belowPML;

      if (sorting === 'None') return 10_000 - watchlist.indexOf(row.symbol);
      if (sorting === 'Chg %') return chg;

      if (sorting === 'Bullish') {
        if (isBullish) return 6000 + chg * 10;
        if (!isBearish && chg >= 0) return 5000 + chg * 10;
        if (!isBearish && chg < 0) return 4000 + chg * 10;
        return 3000 + chg * 10;
      }

      if (isBearish) return 6000 - chg * 10;
      if (!isBullish && chg < 0) return 5000 - chg * 10;
      if (!isBullish && chg >= 0) return 4000 - chg * 10;
      return 3000 - chg * 10;
    };

    return rows
      .slice()
      .sort((a, b) => scoreFor(b) - scoreFor(a))
      .slice(0, 20);
  }, [batch?.data, sorting, watchlist]);

  return (
    <Grid container spacing={3}>
      <Grid item xs={12}>
        <Paper elevation={3} sx={{ p: 3 }}>
          <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: 2, flexWrap: 'wrap' }}>
            <Box>
              <Typography variant="h6">Daily Trend Scanner (PDH/PMH + PDL/PML)</Typography>
              <Typography variant="body2" color="text.secondary">
                {single?.data_source ? `Source: ${single.data_source}` : ''} {single?.as_of ? `• ${single.as_of}` : ''}
              </Typography>
            </Box>

            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, flexWrap: 'wrap' }}>
              <FormControl size="small" sx={{ minWidth: 110 }}>
                <InputLabel>Interval</InputLabel>
                <Select value={interval} label="Interval" onChange={(e) => setInterval(e.target.value)}>
                  <MenuItem value="5m">5m</MenuItem>
                  <MenuItem value="15m">15m</MenuItem>
                  <MenuItem value="30m">30m</MenuItem>
                  <MenuItem value="60m">60m</MenuItem>
                </Select>
              </FormControl>

              <TextField
                size="small"
                label="Days"
                type="number"
                value={days}
                onChange={(e) => setDays(Math.max(1, Math.min(30, Number(e.target.value) || 5)))}
                sx={{ width: 90 }}
              />

              <FormControl size="small" sx={{ minWidth: 120 }}>
                <InputLabel>ORB</InputLabel>
                <Select value={orbMinutes} label="ORB" onChange={(e) => setOrbMinutes(Number(e.target.value))}>
                  <MenuItem value={5}>5 min</MenuItem>
                  <MenuItem value={10}>10 min</MenuItem>
                  <MenuItem value={30}>30 min</MenuItem>
                </Select>
              </FormControl>

              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                <Typography variant="body2" color="text.secondary">
                  Auto
                </Typography>
                <Switch size="small" checked={autoRefresh} onChange={(_, v) => setAutoRefresh(v)} />
              </Box>

              <Button
                variant="outlined"
                onClick={() => {
                  singleQuery.refetch();
                  batchQuery.refetch();
                }}
                disabled={singleQuery.isFetching || batchQuery.isFetching}
              >
                {singleQuery.isFetching || batchQuery.isFetching ? <CircularProgress size={18} /> : 'Refresh'}
              </Button>
            </Box>
          </Box>
        </Paper>
      </Grid>

      <Grid item xs={12} lg={7}>
        <Paper elevation={3} sx={{ p: 3 }}>
          <Box sx={{ display: 'flex', alignItems: 'baseline', justifyContent: 'space-between', gap: 2, mb: 1 }}>
            <Typography variant="h6">{ticker}</Typography>
            <Typography variant="body2" color="text.secondary">
              {single?.price != null ? `Price: ${formatMaybe(single.price)} ` : ''}
              {single?.chg_pct != null ? `(${single.chg_pct >= 0 ? '+' : ''}${formatMaybe(single.chg_pct)}%)` : ''}
            </Typography>
          </Box>

          {singleQuery.isLoading && (
            <Box sx={{ display: 'flex', justifyContent: 'center', py: 6 }}>
              <CircularProgress />
            </Box>
          )}

          {singleQuery.error && (
            <Typography color="error">{(singleQuery.error as Error).message || 'Failed to load daily trend data'}</Typography>
          )}

          {single && singleLevels && (
            <Box sx={{ mb: 2 }}>
              <Table size="small">
                <TableHead>
                  <TableRow>
                    <TableCell>PDH</TableCell>
                    <TableCell>PMH</TableCell>
                    <TableCell>PDL</TableCell>
                    <TableCell>PML</TableCell>
                    <TableCell>Trend</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  <TableRow>
                    <TableCell>{formatMaybe(singleLevels.pdh)}</TableCell>
                    <TableCell>{formatMaybe(singleLevels.pmh)}</TableCell>
                    <TableCell>{formatMaybe(singleLevels.pdl)}</TableCell>
                    <TableCell>{formatMaybe(singleLevels.pml)}</TableCell>
                    <TableCell sx={{ bgcolor: singleTrendBg, color: singleTrendTextColor, fontWeight: 700 }}>
                      {singleTrendDisplay}
                    </TableCell>
                  </TableRow>
                </TableBody>
              </Table>
            </Box>
          )}

          <DailyTrendChart candles={(single?.candles || []) as DailyTrendCandle[]} levels={singleLevels} />
        </Paper>
      </Grid>

      <Grid item xs={12} lg={5}>
        <Paper elevation={3} sx={{ p: 3 }}>
          <Typography variant="h6" sx={{ mb: 1 }}>
            Multi-Symbol Table
          </Typography>

          <Box sx={{ display: 'flex', gap: 1, flexWrap: 'wrap', mb: 2 }}>
            <FormControl size="small" sx={{ minWidth: 130 }}>
              <InputLabel>Sorting</InputLabel>
              <Select value={sorting} label="Sorting" onChange={(e) => setSorting(e.target.value as SortingMode)}>
                <MenuItem value="None">None</MenuItem>
                <MenuItem value="Chg %">Chg %</MenuItem>
                <MenuItem value="Bullish">Bullish</MenuItem>
                <MenuItem value="Bearish">Bearish</MenuItem>
              </Select>
            </FormControl>

            <FormControl size="small" sx={{ minWidth: 150 }}>
              <InputLabel>Trend Style</InputLabel>
              <Select value={trendStyle} label="Trend Style" onChange={(e) => setTrendStyle(e.target.value as TrendStyle)}>
                <MenuItem value="Text">Text</MenuItem>
                <MenuItem value="Symbols white">Symbols white</MenuItem>
                <MenuItem value="Symbols black">Symbols black</MenuItem>
              </Select>
            </FormControl>

            <FormControl size="small" sx={{ minWidth: 120 }}>
              <InputLabel>Neutral</InputLabel>
              <Select value={neutralIcon} label="Neutral" onChange={(e) => setNeutralIcon(e.target.value as NeutralIcon)}>
                {(['⚠️', '⌛', '⏳', '🕖', '🚫', '⁉️'] as NeutralIcon[]).map((v) => (
                  <MenuItem key={v} value={v}>
                    {v}
                  </MenuItem>
                ))}
              </Select>
            </FormControl>

            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
              <Typography variant="body2" color="text.secondary">
                Progress
              </Typography>
              <Switch size="small" checked={showProgressBars} onChange={(_, v) => setShowProgressBars(v)} />
            </Box>

            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
              <Typography variant="body2" color="text.secondary">
                PM vals
              </Typography>
              <Switch size="small" checked={showPMValues} onChange={(_, v) => setShowPMValues(v)} />
            </Box>

            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
              <Typography variant="body2" color="text.secondary">
                PD vals
              </Typography>
              <Switch size="small" checked={showPDValues} onChange={(_, v) => setShowPDValues(v)} />
            </Box>
          </Box>

          <TextField
            label="Watchlist (comma/space separated)"
            size="small"
            fullWidth
            value={watchlistInput}
            onChange={(e) => setWatchlistInput(e.target.value)}
            helperText="Up to 20 displayed; batch fetch supports up to 50."
            sx={{ mb: 2 }}
          />

          {batchQuery.isLoading && (
            <Box sx={{ display: 'flex', justifyContent: 'center', py: 4 }}>
              <CircularProgress />
            </Box>
          )}

          {batchQuery.error && (
            <Typography color="error">{(batchQuery.error as Error).message || 'Failed to load batch trend data'}</Typography>
          )}

          {batch && Object.keys(batch.errors || {}).length > 0 && (
            <Typography variant="caption" color="text.secondary" sx={{ display: 'block', mb: 1 }}>
              Missing: {Object.keys(batch.errors).slice(0, 8).join(', ')}
              {Object.keys(batch.errors).length > 8 ? '…' : ''}
            </Typography>
          )}

          <Table size="small">
            <TableHead>
              <TableRow>
                <TableCell>Ticker</TableCell>
                <TableCell align="right">Price</TableCell>
                <TableCell align="right">Chg %</TableCell>
                {showPDValues && <TableCell align="right">PDH</TableCell>}
                {showPMValues && <TableCell align="right">PMH</TableCell>}
                {showPDValues && <TableCell align="right">PDL</TableCell>}
                {showPMValues && <TableCell align="right">PML</TableCell>}
                <TableCell>PDH</TableCell>
                <TableCell>PMH</TableCell>
                <TableCell>PDL</TableCell>
                <TableCell>PML</TableCell>
                <TableCell>Trend</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {sortedRows.map(({ symbol, payload }) => {
                const levels = payload?.levels;
                const price = payload?.price ?? null;
                const chg = payload?.chg_pct ?? null;

                const pdh = levels?.pdh ?? null;
                const pdl = levels?.pdl ?? null;
                const pmh = levels?.pmh ?? null;
                const pml = levels?.pml ?? null;

                const abovePDH = price != null && pdh != null && price > pdh;
                const belowPDL = price != null && pdl != null && price < pdl;
                const abovePMH = price != null && pmh != null && price > pmh;
                const belowPML = price != null && pml != null && price < pml;

                const pdMid = pdh != null && pdl != null ? (pdh + pdl) / 2 : null;
                const pmMid = pmh != null && pml != null ? (pmh + pml) / 2 : null;

                const pdhDisplay =
                  pdh == null || pdl == null || price == null
                    ? ''
                    : abovePDH
                      ? '🟢'
                      : showProgressBars && pdMid != null && price > pdMid
                        ? buildDisplay(calcBoxes(price, pdMid, pdh, true))
                        : '';
                const pdlDisplay =
                  pdh == null || pdl == null || price == null
                    ? ''
                    : belowPDL
                      ? '🔴'
                      : showProgressBars && pdMid != null && price < pdMid
                        ? buildDisplay(calcBoxes(price, pdMid, pdl, false))
                        : '';
                const pmhDisplay =
                  pmh == null || pml == null || price == null
                    ? ''
                    : abovePMH
                      ? '🟢'
                      : showProgressBars && pmMid != null && price > pmMid
                        ? buildDisplay(calcBoxes(price, pmMid, pmh, true))
                        : '';
                const pmlDisplay =
                  pmh == null || pml == null || price == null
                    ? ''
                    : belowPML
                      ? '🔴'
                      : showProgressBars && pmMid != null && price < pmMid
                        ? buildDisplay(calcBoxes(price, pmMid, pml, false))
                        : '';

                const t = levels ? computeTrend(levels, price) : 'Neutral';
                const trendDisplay =
                  trendStyle === 'Text' ? t : t === 'Bullish' ? '▲' : t === 'Bearish' ? '▼' : neutralIcon;
                const trendBg = t === 'Bullish' ? '#4caf50' : t === 'Bearish' ? '#f44336' : '#6b728080';
                const trendTextColor =
                  trendStyle === 'Text' ? '#FFFFFF' : t === 'Neutral' ? '#FFFFFF' : trendStyle === 'Symbols white' ? '#FFFFFF' : '#111827';

                const chgColor = chg == null ? '#9CA3AF' : chg > 0 ? '#4caf50' : chg < 0 ? '#f44336' : '#9CA3AF';
                const barGreen = abovePDH || abovePMH ? '#4caf50' : '#69f0ae80';
                const barRed = belowPDL || belowPML ? '#f44336' : '#ff525280';

                return (
                  <TableRow key={symbol}>
                    <TableCell>{symbol}</TableCell>
                    <TableCell align="right">{price == null ? '' : formatMaybe(price)}</TableCell>
                    <TableCell align="right" sx={{ color: chgColor }}>
                      {chg == null ? '' : `${chg >= 0 ? '+' : ''}${formatMaybe(chg)}%`}
                    </TableCell>
                    {showPDValues && <TableCell align="right">{formatMaybe(pdh)}</TableCell>}
                    {showPMValues && <TableCell align="right">{formatMaybe(pmh)}</TableCell>}
                    {showPDValues && <TableCell align="right">{formatMaybe(pdl)}</TableCell>}
                    {showPMValues && <TableCell align="right">{formatMaybe(pml)}</TableCell>}
                    <TableCell sx={{ color: abovePDH ? '#4caf50' : barGreen, fontFamily: 'monospace' }}>{pdhDisplay}</TableCell>
                    <TableCell sx={{ color: abovePMH ? '#4caf50' : barGreen, fontFamily: 'monospace' }}>{pmhDisplay}</TableCell>
                    <TableCell sx={{ color: belowPDL ? '#f44336' : barRed, fontFamily: 'monospace' }}>{pdlDisplay}</TableCell>
                    <TableCell sx={{ color: belowPML ? '#f44336' : barRed, fontFamily: 'monospace' }}>{pmlDisplay}</TableCell>
                    <TableCell sx={{ bgcolor: trendBg, color: trendTextColor, fontWeight: 700 }}>{trendDisplay}</TableCell>
                  </TableRow>
                );
              })}
            </TableBody>
          </Table>
        </Paper>
      </Grid>
    </Grid>
  );
}

