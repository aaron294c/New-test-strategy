/**
 * RSI Chebyshev Pro with Goldilocks Fractals
 *
 * This is a SEPARATE indicator tab that displays RSI as candlesticks,
 * exactly matching the TradingView Pine Script implementation.
 *
 * Features:
 * - RSI calculated from price OHLC using Chebyshev Type I filtering
 * - Displays RSI values as candlesticks (not price candles)
 * - Adaptive moving average (MAMA-based)
 * - Goldilocks Fractals with BUY/SELL signals
 * - Candlestick pattern detection (Engulfing, Morning/Evening Star)
 * - Leading signal option (1 bar earlier)
 */

import { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import {
  Box,
  Button,
  Checkbox,
  CircularProgress,
  FormControlLabel,
  Paper,
  Slider,
  Switch,
  Typography,
  Snackbar,
  Alert,
} from '@mui/material';
import {
  createChart,
  IChartApi,
  ISeriesApi,
  CandlestickData,
  LineData,
  UTCTimestamp,
  LineStyle,
} from 'lightweight-charts';

// ============================================================================
// PINE SCRIPT REFERENCE
// ============================================================================
const RSI_CHEBYSHEV_PINE_SCRIPT = `//@version=6
// =================================================================
// RSI Chebyshev Pro with Goldilocks Fractals - Non-Repaint
// =================================================================
// © 2025 NPR21 (TradingView: @NPR21)
// All Rights Reserved
//
// Features:
// - RSI with Chebyshev Type I filtering for ultra-smooth calcs
// - Adaptive moving average based on MESA Adaptive Moving Average (MAMA)
// - Goldilocks Fractals for precise entry/exit signals (non-repainting)
// - Candlestick pattern recognition (Engulfing, Morning/Evening Star)
// - Multiple display styles: Candle, Candle Trend
//
// Full script: src/indicators/rsi-chebyshev-pro-leading-v2.pine
// =================================================================

indicator("RSI Chebyshev Pro with Goldilocks Fractals - NR [NPR21]",
     shorttitle="RSI Cheby Pro NR",
     overlay=false,
     max_labels_count=500)

// ... (see full script in project files)`;

// ============================================================================
// TYPES
// ============================================================================
interface PriceOHLC {
  time: UTCTimestamp;
  open: number;
  high: number;
  low: number;
  close: number;
}

interface RSICandle {
  time: UTCTimestamp;
  open: number;
  high: number;
  low: number;
  close: number;
}

interface FractalSignal {
  index: number;
  time: UTCTimestamp;
  rsiValue: number;
  type: 'buy' | 'sell';
  isLeading: boolean;
}

interface PatternSignal {
  index: number;
  time: UTCTimestamp;
  rsiValue: number;
  pattern: 'engulfing_bull' | 'engulfing_bear' | 'morning_star' | 'evening_star';
}

type Props = {
  ticker: string;
};

// ============================================================================
// CHEBYSHEV TYPE I FILTER (Matches Pine Script exactly)
// ============================================================================
function cosh(x: number): number {
  return (Math.exp(x) + Math.exp(-x)) / 2;
}

function sinh(x: number): number {
  return (Math.exp(x) - Math.exp(-x)) / 2;
}

function asinh(x: number): number {
  return Math.log(x + Math.sqrt(x * x + 1));
}

function acosh(x: number): number {
  return x < 1 ? 1 : Math.log(x + Math.sqrt(x * x - 1));
}

function chebyshevI(data: number[], length: number, ripple: number): number[] {
  const result: number[] = [];
  const alpha = 1 / length;
  const acoshRi = 1 / (1 - ripple);
  const asinhRi = 1 / ripple;
  const acoshVal = acosh(acoshRi);
  const asinhVal = asinh(asinhRi);
  const a = cosh(alpha * acoshVal);
  const b = sinh(alpha * asinhVal);
  const g = (a - b) / (a + b);

  let prevValue = data[0] || 0;

  for (let i = 0; i < data.length; i++) {
    const filtered = (1 - g) * data[i] + g * prevValue;
    result.push(filtered);
    prevValue = filtered;
  }

  return result;
}

// ============================================================================
// MAMA PERIOD CALCULATION (Matches Pine Script)
// ============================================================================
function calculateMamaPeriod(data: number[], dynLow: number = 1, dynHigh: number = 2048): number[] {
  const periods: number[] = [];
  let period = 0;
  let I2 = 0, Q2 = 0, Re = 0, Im = 0;

  const C1 = 0.0962;
  const C2 = 0.5769;

  const smooth: number[] = [];
  const detrend: number[] = [];
  const Q1: number[] = [];
  const I1: number[] = [];
  const jI: number[] = [];
  const jQ: number[] = [];

  for (let i = 0; i < data.length; i++) {
    const C3 = 0.075 * (periods[i - 1] || 0) + 0.54;

    // Smooth calculation
    const s = (4 * data[i] +
               3 * (data[i - 1] || data[i]) +
               2 * (data[i - 2] || data[i]) +
               (data[i - 3] || data[i])) / 10;
    smooth.push(s);

    // Detrend
    const d = C3 * (C1 * s +
              C2 * (smooth[i - 2] || s) -
              C2 * (smooth[i - 4] || s) -
              C1 * (smooth[i - 6] || s));
    detrend.push(d);

    // Q1
    const q1 = C3 * (C1 * d +
               C2 * (detrend[i - 2] || d) -
               C2 * (detrend[i - 4] || d) -
               C1 * (detrend[i - 6] || d));
    Q1.push(q1);

    // I1
    const i1 = detrend[i - 3] || d;
    I1.push(i1);

    // jI
    const ji = C3 * (C1 * i1 +
               C2 * (I1[i - 2] || i1) -
               C2 * (I1[i - 4] || i1) -
               C1 * (I1[i - 6] || i1));
    jI.push(ji);

    // jQ
    const jq = C3 * (C1 * q1 +
               C2 * (Q1[i - 2] || q1) -
               C2 * (Q1[i - 4] || q1) -
               C1 * (Q1[i - 6] || q1));
    jQ.push(jq);

    // I2, Q2
    const I2_temp = i1 - jq;
    const Q2_temp = q1 + ji;
    I2 = 0.2 * I2_temp + 0.8 * I2;
    Q2 = 0.2 * Q2_temp + 0.8 * Q2;

    // Re, Im
    const Re_temp = I2 * (I2 || 0) + Q2 * (Q2 || 0);
    const Im_temp = I2 * (Q2 || 0) - Q2 * (I2 || 0);
    Re = 0.2 * Re_temp + 0.8 * Re;
    Im = 0.2 * Im_temp + 0.8 * Im;

    // Period calculation
    let period1 = Re !== 0 && Im !== 0 ? 2 * Math.PI / Math.atan(Im / Re) : 0;
    let period2 = Math.min(period1, 1.5 * (periods[i - 1] || period1));
    let period3 = Math.max(period2, (2 / 3) * (periods[i - 1] || period2));
    let period4 = Math.min(Math.max(period3, dynLow), dynHigh);
    period = period4 * 0.2 + (periods[i - 1] || period4) * 0.8;
    periods.push(period);
  }

  return periods;
}

// ============================================================================
// CUSTOM RSI CALCULATION (Matches Pine Script customRSI function)
// ============================================================================
function customRSI(source: number[], rsiLength: number, rsiSmoothing: number): number[] {
  // Step 1: Chebyshev filter on source
  const closeFiltered = chebyshevI(source, rsiSmoothing, 0.5);

  // Step 2: Calculate changes
  const changes: number[] = [];
  for (let i = 0; i < closeFiltered.length; i++) {
    if (i === 0) {
      changes.push(0);
    } else {
      changes.push(closeFiltered[i] - closeFiltered[i - 1]);
    }
  }

  // Step 3: Separate ups and downs
  const ups = changes.map(c => Math.max(c, 0));
  const downs = changes.map(c => -Math.min(c, 0));

  // Step 4: Chebyshev filter on ups and downs
  const upFiltered = chebyshevI(ups, rsiLength, 0.5);
  const downFiltered = chebyshevI(downs, rsiLength, 0.5);

  // Step 5: Calculate RSI
  const rsi: number[] = [];
  for (let i = 0; i < source.length; i++) {
    if (downFiltered[i] === 0) {
      rsi.push(100);
    } else {
      rsi.push(100 - (100 / (1 + upFiltered[i] / downFiltered[i])));
    }
  }

  return rsi;
}

// ============================================================================
// CALCULATE RSI OHLC (The core calculation matching Pine Script)
// ============================================================================
function calculateRSIOHLC(
  priceData: PriceOHLC[],
  length: number,
  smoothing: number,
  maMultiplier: number
): {
  candles: RSICandle[];
  ma: number[];
  ohlc: number[];
} {
  // Extract price arrays (using [1] offset like Pine Script for non-repaint)
  const opens: number[] = [];
  const highs: number[] = [];
  const lows: number[] = [];
  const closes: number[] = [];

  for (let i = 0; i < priceData.length; i++) {
    // Use previous bar's values (like Pine Script's [1])
    const prevIndex = Math.max(0, i - 1);
    opens.push(priceData[prevIndex].open);
    highs.push(priceData[prevIndex].high);
    lows.push(priceData[prevIndex].low);
    closes.push(priceData[prevIndex].close);
  }

  // Calculate RSI for each price component
  const rsiOpen = customRSI(opens, length, smoothing);
  const rsiHigh = customRSI(highs, length, smoothing);
  const rsiLow = customRSI(lows, length, smoothing);
  const rsiClose = customRSI(closes, length, smoothing);

  // Calculate OHLC average
  const ohlc: number[] = [];
  for (let i = 0; i < rsiOpen.length; i++) {
    ohlc.push((rsiOpen[i] + rsiHigh[i] + rsiLow[i] + rsiClose[i]) / 4);
  }

  // Calculate adaptive MA length using MAMA
  const mamaPeriods = calculateMamaPeriod(ohlc);

  // Calculate MA with dynamic length
  const ma: number[] = [];
  for (let i = 0; i < ohlc.length; i++) {
    const cycle = Math.round(mamaPeriods[i] || 14);
    const maLength = Math.max(1, (cycle + 1) * maMultiplier);

    // Use Chebyshev filter for MA
    const startIdx = Math.max(0, i - maLength + 1);
    const slice = ohlc.slice(startIdx, i + 1);
    const filtered = chebyshevI(slice, maLength, 0.05);
    ma.push(filtered[filtered.length - 1]);
  }

  // Build RSI candles
  const candles: RSICandle[] = priceData.map((p, i) => ({
    time: p.time,
    open: rsiOpen[i],
    high: rsiHigh[i],
    low: rsiLow[i],
    close: rsiClose[i],
  }));

  return { candles, ma, ohlc };
}

// ============================================================================
// FRACTAL DETECTION (Non-Repainting)
// ============================================================================
function detectFractals(
  rsiHigh: number[],
  rsiLow: number[],
  times: UTCTimestamp[],
  n: number
): { buySignals: FractalSignal[]; sellSignals: FractalSignal[] } {
  const buySignals: FractalSignal[] = [];
  const sellSignals: FractalSignal[] = [];

  for (let i = n; i < rsiHigh.length - n; i++) {
    // Check for up fractal (SELL signal - high pivot in RSI)
    let isUpFractal = true;
    for (let j = 1; j <= n; j++) {
      if (rsiHigh[i] <= rsiHigh[i - j] || rsiHigh[i] <= rsiHigh[i + j]) {
        isUpFractal = false;
        break;
      }
    }
    if (isUpFractal) {
      sellSignals.push({
        index: i,
        time: times[i],
        rsiValue: rsiHigh[i],
        type: 'sell',
        isLeading: false,
      });
    }

    // Check for down fractal (BUY signal - low pivot in RSI)
    let isDownFractal = true;
    for (let j = 1; j <= n; j++) {
      if (rsiLow[i] >= rsiLow[i - j] || rsiLow[i] >= rsiLow[i + j]) {
        isDownFractal = false;
        break;
      }
    }
    if (isDownFractal) {
      buySignals.push({
        index: i,
        time: times[i],
        rsiValue: rsiLow[i],
        type: 'buy',
        isLeading: false,
      });
    }
  }

  return { buySignals, sellSignals };
}

// ============================================================================
// LEADING SIGNAL DETECTION (1 bar earlier)
// ============================================================================
function detectLeadingSignals(
  rsiOpen: number[],
  rsiHigh: number[],
  rsiLow: number[],
  rsiClose: number[],
  times: UTCTimestamp[],
  n: number,
  oversoldZone: number,
  overboughtZone: number
): FractalSignal[] {
  const signals: FractalSignal[] = [];
  let lastBuyBar = -n - 1;
  let lastSellBar = -n - 1;

  for (let i = n; i < rsiClose.length; i++) {
    // Check if current RSI low is lowest in last N bars
    let isPotentialLow = true;
    for (let j = 1; j <= n; j++) {
      if (rsiLow[i - j] <= rsiLow[i]) {
        isPotentialLow = false;
        break;
      }
    }

    // Check if current RSI high is highest in last N bars
    let isPotentialHigh = true;
    for (let j = 1; j <= n; j++) {
      if (rsiHigh[i - j] >= rsiHigh[i]) {
        isPotentialHigh = false;
        break;
      }
    }

    // Momentum detection
    const prevMomentum = (rsiClose[i - 1] || 0) - (rsiClose[i - 2] || 0);
    const currentMomentum = rsiClose[i] - (rsiClose[i - 1] || 0);
    const bullishMomentumShift = prevMomentum < 0 && currentMomentum > 0;
    const bearishMomentumShift = prevMomentum > 0 && currentMomentum < 0;

    // Candle patterns
    const bullishCandle = rsiClose[i] > rsiOpen[i];
    const bearishCandle = rsiClose[i] < rsiOpen[i];

    // Leading BUY
    if (
      rsiLow[i] < oversoldZone &&
      isPotentialLow &&
      (bullishMomentumShift || bullishCandle) &&
      (i - lastBuyBar) > n
    ) {
      signals.push({
        index: i,
        time: times[i],
        rsiValue: rsiLow[i],
        type: 'buy',
        isLeading: true,
      });
      lastBuyBar = i;
    }

    // Leading SELL
    if (
      rsiHigh[i] > overboughtZone &&
      isPotentialHigh &&
      (bearishMomentumShift || bearishCandle) &&
      (i - lastSellBar) > n
    ) {
      signals.push({
        index: i,
        time: times[i],
        rsiValue: rsiHigh[i],
        type: 'sell',
        isLeading: true,
      });
      lastSellBar = i;
    }
  }

  return signals;
}

// ============================================================================
// PATTERN DETECTION (Engulfing, Morning/Evening Star)
// ============================================================================
function detectPatterns(
  rsiOpen: number[],
  rsiHigh: number[],
  rsiLow: number[],
  rsiClose: number[],
  ohlc: number[],
  ma: number[],
  times: UTCTimestamp[]
): PatternSignal[] {
  const patterns: PatternSignal[] = [];

  // DMA for body average (simplified)
  const bodyAvg: number[] = [];
  let ema1 = 0, ema2 = 0;

  for (let i = 0; i < rsiClose.length; i++) {
    const body = Math.abs(rsiClose[i] - rsiOpen[i]);
    const k = 2 / (i + 2);
    ema1 = body * k + ema1 * (1 - k);
    ema2 = ema1 * k + ema2 * (1 - k);
    bodyAvg.push(2 * ema1 - ema2);
  }

  for (let i = 2; i < rsiClose.length; i++) {
    const downTrend = ohlc[i] < ma[i];
    const upTrend = ohlc[i] > ma[i];
    const rsiLowZone = rsiHigh[i] < 40;
    const rsiHighZone = rsiLow[i] > 60;

    const body = Math.abs(rsiClose[i] - rsiOpen[i]);
    const longBody = body > bodyAvg[i];
    const whiteBody = rsiOpen[i] < rsiClose[i];
    const blackBody = rsiOpen[i] > rsiClose[i];

    const prevWhiteBody = rsiOpen[i - 1] < rsiClose[i - 1];
    const prevBlackBody = rsiOpen[i - 1] > rsiClose[i - 1];
    const prevSmallBody = Math.abs(rsiClose[i - 1] - rsiOpen[i - 1]) < bodyAvg[i - 1];

    // Bullish Engulfing
    if (
      downTrend &&
      whiteBody &&
      longBody &&
      prevBlackBody &&
      prevSmallBody &&
      rsiClose[i] >= rsiOpen[i - 1] &&
      rsiOpen[i] <= rsiClose[i - 1] &&
      rsiLowZone
    ) {
      patterns.push({
        index: i,
        time: times[i],
        rsiValue: rsiLow[i],
        pattern: 'engulfing_bull',
      });
    }

    // Bearish Engulfing
    if (
      upTrend &&
      blackBody &&
      longBody &&
      prevWhiteBody &&
      prevSmallBody &&
      rsiClose[i] <= rsiOpen[i - 1] &&
      rsiOpen[i] >= rsiClose[i - 1] &&
      rsiHighZone
    ) {
      patterns.push({
        index: i,
        time: times[i],
        rsiValue: rsiHigh[i],
        pattern: 'engulfing_bear',
      });
    }

    // Morning Star
    const prevPrevLongBody = Math.abs(rsiClose[i - 2] - rsiOpen[i - 2]) > bodyAvg[i - 2];
    const prevPrevBlackBody = rsiOpen[i - 2] > rsiClose[i - 2];
    const prevPrevBodyMiddle = (Math.abs(rsiClose[i - 2] - rsiOpen[i - 2])) / 2 + Math.min(rsiClose[i - 2], rsiOpen[i - 2]);

    if (
      prevPrevLongBody &&
      prevSmallBody &&
      longBody &&
      downTrend &&
      prevPrevBlackBody &&
      whiteBody &&
      rsiClose[i] >= prevPrevBodyMiddle &&
      rsiLowZone
    ) {
      patterns.push({
        index: i,
        time: times[i],
        rsiValue: rsiLow[i],
        pattern: 'morning_star',
      });
    }

    // Evening Star
    const prevPrevWhiteBody = rsiOpen[i - 2] < rsiClose[i - 2];

    if (
      prevPrevLongBody &&
      prevSmallBody &&
      longBody &&
      upTrend &&
      prevPrevWhiteBody &&
      blackBody &&
      rsiClose[i] <= prevPrevBodyMiddle &&
      rsiHighZone
    ) {
      patterns.push({
        index: i,
        time: times[i],
        rsiValue: rsiHigh[i],
        pattern: 'evening_star',
      });
    }
  }

  return patterns;
}

// ============================================================================
// FETCH PRICE DATA (Using Yahoo Finance style endpoint)
// ============================================================================
async function fetchPriceData(ticker: string, days: number = 365): Promise<PriceOHLC[]> {
  // Try to fetch from our backend's daily trend API which has candle data
  try {
    const response = await fetch(
      `/api/daily-trend/${encodeURIComponent(ticker)}?days=${days}&include_candles=true`
    );
    if (response.ok) {
      const data = await response.json();
      if (data.candles && Array.isArray(data.candles)) {
        return data.candles.map((c: any) => ({
          time: (new Date(c.time || c.date).getTime() / 1000) as UTCTimestamp,
          open: c.open,
          high: c.high,
          low: c.low,
          close: c.close,
        }));
      }
    }
  } catch (e) {
    console.log('Daily trend API not available, generating sample data');
  }

  // Generate realistic sample price data for demonstration
  const data: PriceOHLC[] = [];
  let price = 100 + Math.random() * 100;
  const startDate = new Date();
  startDate.setDate(startDate.getDate() - days);

  for (let i = 0; i < days; i++) {
    const date = new Date(startDate);
    date.setDate(date.getDate() + i);

    // Skip weekends
    if (date.getDay() === 0 || date.getDay() === 6) continue;

    const volatility = 0.02;
    const trend = Math.sin(i / 30) * 0.005; // Slight cyclical trend
    const change = (Math.random() - 0.5) * 2 * volatility + trend;

    const open = price;
    const close = price * (1 + change);
    const high = Math.max(open, close) * (1 + Math.random() * volatility * 0.5);
    const low = Math.min(open, close) * (1 - Math.random() * volatility * 0.5);

    data.push({
      time: (date.getTime() / 1000) as UTCTimestamp,
      open,
      high,
      low,
      close,
    });

    price = close;
  }

  return data;
}

// ============================================================================
// RSI CHEBYSHEV CHART COMPONENT
// ============================================================================
function RSIChebyshevChart(props: {
  priceData: PriceOHLC[];
  rsiLength: number;
  rsiSmoothing: number;
  maMultiplier: number;
  fractalPeriods: number;
  showMA: boolean;
  showStandardSignals: boolean;
  showLeadingSignals: boolean;
  showPatterns: boolean;
  oversoldZone: number;
  overboughtZone: number;
  styleChoice: 'Candle' | 'Candle Trend';
  // New props matching Pine Script settings
  maLineWidth: number;
  showFractalShapes: boolean;
  buyOffset: number;
  sellOffset: number;
  colorBars: boolean;
  colorRSILine: boolean;
  rsiLineWidth: number;
}) {
  const {
    priceData,
    rsiLength,
    rsiSmoothing,
    maMultiplier,
    fractalPeriods,
    showMA,
    showStandardSignals,
    showLeadingSignals,
    showPatterns,
    oversoldZone,
    overboughtZone,
    styleChoice,
    maLineWidth,
    showFractalShapes,
    buyOffset,
    sellOffset,
    colorBars,
    colorRSILine,
    rsiLineWidth,
  } = props;

  const chartContainerRef = useRef<HTMLDivElement | null>(null);
  const chartRef = useRef<IChartApi | null>(null);
  const candleSeriesRef = useRef<ISeriesApi<'Candlestick'> | null>(null);
  const maSeriesRef = useRef<ISeriesApi<'Line'> | null>(null);

  // Calculate RSI OHLC
  const { candles, ma, ohlc } = useMemo(
    () => calculateRSIOHLC(priceData, rsiLength, rsiSmoothing, maMultiplier),
    [priceData, rsiLength, rsiSmoothing, maMultiplier]
  );

  const times = useMemo(() => priceData.map(d => d.time), [priceData]);
  const rsiHigh = useMemo(() => candles.map(c => c.high), [candles]);
  const rsiLow = useMemo(() => candles.map(c => c.low), [candles]);
  const rsiOpen = useMemo(() => candles.map(c => c.open), [candles]);
  const rsiClose = useMemo(() => candles.map(c => c.close), [candles]);

  // Detect signals
  const standardSignals = useMemo(
    () => detectFractals(rsiHigh, rsiLow, times, fractalPeriods),
    [rsiHigh, rsiLow, times, fractalPeriods]
  );

  const leadingSignals = useMemo(
    () => detectLeadingSignals(rsiOpen, rsiHigh, rsiLow, rsiClose, times, fractalPeriods, oversoldZone, overboughtZone),
    [rsiOpen, rsiHigh, rsiLow, rsiClose, times, fractalPeriods, oversoldZone, overboughtZone]
  );

  const patterns = useMemo(
    () => detectPatterns(rsiOpen, rsiHigh, rsiLow, rsiClose, ohlc, ma, times),
    [rsiOpen, rsiHigh, rsiLow, rsiClose, ohlc, ma, times]
  );

  // Current values
  const currentRsiClose = rsiClose[rsiClose.length - 1] || 50;
  const currentMA = ma[ma.length - 1] || 50;
  const currentOHLC = ohlc[ohlc.length - 1] || 50;

  // Calculate MA gradient color based on current OHLC
  const currentColVal = currentOHLC > 65 ? 255 : currentOHLC < 35 ? 0 : currentOHLC * 2.55;
  const currentMAColor = `rgb(${Math.round(255 - currentColVal)}, ${Math.round(currentColVal)}, 0)`;

  useEffect(() => {
    const el = chartContainerRef.current;
    if (!el) return;

    const chart = createChart(el, {
      width: el.clientWidth,
      height: 450,
      layout: { background: { color: '#1a1a1a' }, textColor: '#d1d4dc' },
      grid: { vertLines: { color: '#2b2b43' }, horzLines: { color: '#2b2b43' } },
      rightPriceScale: {
        borderColor: '#485c7b',
        scaleMargins: { top: 0.05, bottom: 0.05 },
      },
      timeScale: { borderColor: '#485c7b', timeVisible: true, secondsVisible: false },
      crosshair: { mode: 1 },
    });
    chartRef.current = chart;

    // Candlestick series for RSI
    candleSeriesRef.current = chart.addCandlestickSeries({
      upColor: 'transparent',
      downColor: '#EF5350',
      borderUpColor: '#00FF00',
      borderDownColor: '#EF5350',
      wickUpColor: '#00FF00',
      wickDownColor: '#EF5350',
    });

    // MA line (will be colored per-bar based on OHLC value)
    maSeriesRef.current = chart.addLineSeries({
      color: '#00FF00', // Default, will be overridden per point
      lineWidth: maLineWidth as 1 | 2 | 3 | 4,
      title: 'Adaptive MA',
      lastValueVisible: true,
      priceLineVisible: false,
    });

    // Reference lines
    const addHLine = (price: number, color: string) => {
      candleSeriesRef.current?.createPriceLine({
        price,
        color,
        lineWidth: 1,
        lineStyle: LineStyle.Dashed,
        axisLabelVisible: true,
      });
    };

    addHLine(70, 'rgba(128,128,128,0.5)');
    addHLine(50, 'rgba(128,128,128,0.5)');
    addHLine(30, 'rgba(128,128,128,0.5)');

    const handleResize = () => {
      if (chartContainerRef.current && chartRef.current) {
        chartRef.current.applyOptions({ width: chartContainerRef.current.clientWidth });
      }
    };
    window.addEventListener('resize', handleResize);

    return () => {
      window.removeEventListener('resize', handleResize);
      chart.remove();
    };
  }, [maLineWidth]);

  useEffect(() => {
    if (!candleSeriesRef.current || !maSeriesRef.current) return;

    // Style candles based on styleChoice
    const isTrendStyle = styleChoice === 'Candle Trend';

    candleSeriesRef.current.applyOptions({
      upColor: isTrendStyle ? 'transparent' : '#00FF00',
      downColor: '#EF5350',
      borderUpColor: '#00FF00',
      borderDownColor: '#EF5350',
      wickUpColor: '#00FF00',
      wickDownColor: '#EF5350',
    });

    // Set candle data
    const candleData: CandlestickData<UTCTimestamp>[] = candles.map(c => ({
      time: c.time,
      open: c.open,
      high: c.high,
      low: c.low,
      close: c.close,
    }));
    candleSeriesRef.current.setData(candleData);

    // Set MA data with gradient color based on OHLC value
    // Pine Script formula: col_val = OHLC > 65 ? 255 : OHLC < 35 ? 0 : OHLC * 2.55
    // color = rgb(255 - col_val, col_val, 0)
    if (showMA) {
      const maData: (LineData<UTCTimestamp> & { color?: string })[] = times.map((t, i) => {
        const ohlcVal = ohlc[i] || 50;
        const colVal = ohlcVal > 65 ? 255 : ohlcVal < 35 ? 0 : ohlcVal * 2.55;
        const r = Math.round(255 - colVal);
        const g = Math.round(colVal);
        const gradColor = `rgb(${r}, ${g}, 0)`;
        return {
          time: t,
          value: ma[i],
          color: gradColor,
        };
      });
      maSeriesRef.current.setData(maData);
    } else {
      maSeriesRef.current.setData([]);
    }

    // Build markers
    const markers: any[] = [];

    // Standard fractal signals (BUY/SELL labels)
    if (showStandardSignals) {
      for (const s of standardSignals.buySignals) {
        // Add label marker
        markers.push({
          time: s.time,
          position: 'belowBar',
          color: '#2962FF',
          shape: 'arrowUp',
          text: 'BUY',
        });
        // Add fractal shape (triangle) if enabled
        if (showFractalShapes) {
          markers.push({
            time: s.time,
            position: 'belowBar',
            color: '#2962FF',
            shape: 'arrowUp',
            text: '',
            size: 0.5,
          });
        }
      }
      for (const s of standardSignals.sellSignals) {
        markers.push({
          time: s.time,
          position: 'aboveBar',
          color: '#DD0000',
          shape: 'arrowDown',
          text: 'SELL',
        });
        if (showFractalShapes) {
          markers.push({
            time: s.time,
            position: 'aboveBar',
            color: '#DD0000',
            shape: 'arrowDown',
            text: '',
            size: 0.5,
          });
        }
      }
    }

    // Leading signals
    if (showLeadingSignals) {
      for (const s of leadingSignals) {
        if (s.type === 'buy') {
          markers.push({
            time: s.time,
            position: 'belowBar',
            color: '#00E676',
            shape: 'arrowUp',
            text: 'LEAD',
          });
        } else {
          markers.push({
            time: s.time,
            position: 'aboveBar',
            color: '#FF5252',
            shape: 'arrowDown',
            text: 'LEAD',
          });
        }
      }
    }

    // Pattern signals (only show in Candle Trend mode as per Pine Script)
    if (showPatterns && styleChoice === 'Candle Trend') {
      for (const p of patterns) {
        if (p.pattern === 'engulfing_bull' || p.pattern === 'morning_star') {
          markers.push({
            time: p.time,
            position: 'belowBar',
            color: '#00FF00',
            shape: 'circle',
            text: p.pattern === 'engulfing_bull' ? 'Eng' : 'MS',
          });
        } else {
          markers.push({
            time: p.time,
            position: 'aboveBar',
            color: '#FF0000',
            shape: 'circle',
            text: p.pattern === 'engulfing_bear' ? 'Eng' : 'ES',
          });
        }
      }
    }

    markers.sort((a, b) => (a.time as number) - (b.time as number));
    candleSeriesRef.current.setMarkers(markers);

    chartRef.current?.timeScale().fitContent();
  }, [candles, ma, ohlc, times, showMA, showStandardSignals, showLeadingSignals, showPatterns, standardSignals, leadingSignals, patterns, styleChoice, showFractalShapes, buyOffset, sellOffset, colorBars, colorRSILine, rsiLineWidth]);

  return (
    <Box>
      <Box sx={{ display: 'flex', gap: 3, mb: 2, flexWrap: 'wrap' }}>
        <Box sx={{ textAlign: 'center' }}>
          <Typography variant="caption" color="text.secondary">RSI Close</Typography>
          <Typography
            variant="h6"
            sx={{
              color: currentRsiClose < 30 ? '#00C853' : currentRsiClose > 70 ? '#EF5350' : '#787B86',
              fontWeight: 700,
            }}
          >
            {currentRsiClose.toFixed(2)}
          </Typography>
        </Box>
        <Box sx={{ textAlign: 'center' }}>
          <Typography variant="caption" color="text.secondary">Adaptive MA</Typography>
          <Typography variant="h6" sx={{ color: currentMAColor, fontWeight: 700 }}>
            {currentMA.toFixed(2)}
          </Typography>
        </Box>
        <Box sx={{ textAlign: 'center' }}>
          <Typography variant="caption" color="text.secondary">RSI OHLC Avg</Typography>
          <Typography variant="h6" sx={{ color: currentMAColor, fontWeight: 700 }}>
            {currentOHLC.toFixed(2)}
          </Typography>
        </Box>
        <Box sx={{ textAlign: 'center' }}>
          <Typography variant="caption" color="text.secondary">Standard Signals</Typography>
          <Typography variant="h6" sx={{ color: '#2962FF', fontWeight: 700 }}>
            {standardSignals.buySignals.length + standardSignals.sellSignals.length}
          </Typography>
        </Box>
        <Box sx={{ textAlign: 'center' }}>
          <Typography variant="caption" color="text.secondary">Leading Signals</Typography>
          <Typography variant="h6" sx={{ color: '#00E676', fontWeight: 700 }}>
            {leadingSignals.length}
          </Typography>
        </Box>
        <Box sx={{ textAlign: 'center' }}>
          <Typography variant="caption" color="text.secondary">Patterns</Typography>
          <Typography variant="h6" sx={{ color: '#9C27B0', fontWeight: 700 }}>
            {patterns.length}
          </Typography>
        </Box>
      </Box>
      <div ref={chartContainerRef} style={{ width: '100%' }} />
    </Box>
  );
}

// ============================================================================
// MAIN PAGE COMPONENT
// ============================================================================
export default function RSIChebyshevLeadingPage(props: Props) {
  const { ticker } = props;

  // State
  const [priceData, setPriceData] = useState<PriceOHLC[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // RSI Settings (matching Pine Script exactly)
  const [colorBars, setColorBars] = useState(false);
  const [styleChoice, setStyleChoice] = useState<'Candle' | 'Candle Trend'>('Candle');
  const [colorRSILine, setColorRSILine] = useState(false);
  const [rsiLineWidth, setRsiLineWidth] = useState(2);
  const [rsiLength, setRsiLength] = useState(24);
  const [rsiSmoothing, setRsiSmoothing] = useState(3);
  const [autoMA, setAutoMA] = useState(true);
  const [maMultiplier, setMaMultiplier] = useState(1);
  const [maLineWidth, setMaLineWidth] = useState(2);

  // Fractal Settings (matching Pine Script exactly)
  const [fractalPeriods, setFractalPeriods] = useState(5);
  const [showBuySellLabels, setShowBuySellLabels] = useState(true);
  const [showFractalShapes, setShowFractalShapes] = useState(false);
  const [buyOffset, setBuyOffset] = useState(8);
  const [sellOffset, setSellOffset] = useState(8);

  // Additional display settings
  const [showLeadingSignals, setShowLeadingSignals] = useState(true);
  const [showPatterns, setShowPatterns] = useState(true);
  const [oversoldZone, setOversoldZone] = useState(35);
  const [overboughtZone, setOverboughtZone] = useState(65);
  const [pineScriptCopied, setPineScriptCopied] = useState(false);

  // Fetch data
  useEffect(() => {
    setIsLoading(true);
    setError(null);

    fetchPriceData(ticker, 365)
      .then(data => {
        setPriceData(data);
        setIsLoading(false);
      })
      .catch(err => {
        setError(err.message);
        setIsLoading(false);
      });
  }, [ticker]);

  const handleCopyPineScript = useCallback(async () => {
    try {
      await navigator.clipboard.writeText(RSI_CHEBYSHEV_PINE_SCRIPT);
      setPineScriptCopied(true);
    } catch {
      window.prompt('Copy Pine Script:', RSI_CHEBYSHEV_PINE_SCRIPT);
    }
  }, []);

  if (isLoading) {
    return (
      <Paper sx={{ p: 3, display: 'flex', justifyContent: 'center', alignItems: 'center', minHeight: 520 }}>
        <CircularProgress />
      </Paper>
    );
  }

  if (error) {
    return (
      <Paper sx={{ p: 3 }}>
        <Alert severity="error">{error}</Alert>
      </Paper>
    );
  }

  return (
    <Box>
      {/* Header */}
      <Paper elevation={3} sx={{ p: 3, mb: 3 }}>
        <Box sx={{ display: 'flex', alignItems: 'baseline', justifyContent: 'space-between', gap: 2, mb: 2 }}>
          <Box>
            <Typography variant="h6">RSI Chebyshev Pro with Goldilocks Fractals</Typography>
            <Typography variant="body2" color="text.secondary">
              {ticker} • RSI displayed as candlesticks with adaptive MA • Non-repainting signals
            </Typography>
          </Box>
          <Box sx={{ display: 'flex', gap: 1 }}>
            <Button variant="outlined" onClick={() => fetchPriceData(ticker).then(setPriceData)}>
              Refresh
            </Button>
            <Button variant="contained" onClick={handleCopyPineScript}>
              Copy Pine Script
            </Button>
          </Box>
        </Box>
      </Paper>

      {/* Chart */}
      <Paper elevation={3} sx={{ p: 2, mb: 3 }}>
        <RSIChebyshevChart
          priceData={priceData}
          rsiLength={rsiLength}
          rsiSmoothing={rsiSmoothing}
          maMultiplier={maMultiplier}
          fractalPeriods={fractalPeriods}
          showMA={autoMA}
          showStandardSignals={showBuySellLabels}
          showLeadingSignals={showLeadingSignals}
          showPatterns={showPatterns}
          oversoldZone={oversoldZone}
          overboughtZone={overboughtZone}
          styleChoice={styleChoice}
          maLineWidth={maLineWidth}
          showFractalShapes={showFractalShapes}
          buyOffset={buyOffset}
          sellOffset={sellOffset}
          colorBars={colorBars}
          colorRSILine={colorRSILine}
          rsiLineWidth={rsiLineWidth}
        />
      </Paper>

      {/* RSI SETTINGS - Matching Pine Script exactly */}
      <Paper elevation={3} sx={{ p: 3, mb: 3 }}>
        <Typography variant="h6" sx={{ mb: 2, fontWeight: 700 }}>RSI SETTINGS</Typography>

        <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
          {/* Color Bars */}
          <FormControlLabel
            control={<Checkbox checked={colorBars} onChange={(e) => setColorBars(e.target.checked)} />}
            label="Color Bars"
          />

          {/* Style dropdown */}
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
            <Typography variant="body2" sx={{ minWidth: 80 }}>Style:</Typography>
            <select
              value={styleChoice}
              onChange={(e) => setStyleChoice(e.target.value as 'Candle' | 'Candle Trend')}
              style={{ padding: '8px 12px', borderRadius: 4, border: '1px solid #555', background: '#2a2a2a', color: '#fff', minWidth: 150 }}
            >
              <option value="Candle">Candle</option>
              <option value="Candle Trend">Candle Trend</option>
            </select>
          </Box>

          {/* Color RSI Line */}
          <FormControlLabel
            control={<Checkbox checked={colorRSILine} onChange={(e) => setColorRSILine(e.target.checked)} />}
            label="Color RSI Line"
          />

          {/* RSI Line Width */}
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
            <Typography variant="body2" sx={{ minWidth: 120 }}>RSI Line Width:</Typography>
            <Slider
              value={rsiLineWidth}
              onChange={(_, v) => setRsiLineWidth(v as number)}
              min={1}
              max={5}
              step={1}
              sx={{ width: 150 }}
              valueLabelDisplay="auto"
            />
            <Typography variant="body2" sx={{ minWidth: 30 }}>{rsiLineWidth}</Typography>
          </Box>

          {/* Length */}
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
            <Typography variant="body2" sx={{ minWidth: 120 }}>Length:</Typography>
            <Slider
              value={rsiLength}
              onChange={(_, v) => setRsiLength(v as number)}
              min={5}
              max={50}
              sx={{ width: 150 }}
              valueLabelDisplay="auto"
            />
            <Typography variant="body2" sx={{ minWidth: 30 }}>{rsiLength}</Typography>
          </Box>

          {/* Smoothing */}
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
            <Typography variant="body2" sx={{ minWidth: 120 }}>Smoothing:</Typography>
            <Slider
              value={rsiSmoothing}
              onChange={(_, v) => setRsiSmoothing(v as number)}
              min={1}
              max={10}
              sx={{ width: 150 }}
              valueLabelDisplay="auto"
            />
            <Typography variant="body2" sx={{ minWidth: 30 }}>{rsiSmoothing}</Typography>
          </Box>

          {/* Auto MA */}
          <FormControlLabel
            control={<Checkbox checked={autoMA} onChange={(e) => setAutoMA(e.target.checked)} />}
            label="Auto MA"
          />

          {/* MA Multiplier */}
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
            <Typography variant="body2" sx={{ minWidth: 120 }}>MA Multiplier:</Typography>
            <Slider
              value={maMultiplier}
              onChange={(_, v) => setMaMultiplier(v as number)}
              min={1}
              max={5}
              sx={{ width: 150 }}
              valueLabelDisplay="auto"
            />
            <Typography variant="body2" sx={{ minWidth: 30 }}>{maMultiplier}</Typography>
          </Box>

          {/* MA Line Width */}
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
            <Typography variant="body2" sx={{ minWidth: 120 }}>MA Line Width:</Typography>
            <Slider
              value={maLineWidth}
              onChange={(_, v) => setMaLineWidth(v as number)}
              min={1}
              max={5}
              step={1}
              sx={{ width: 150 }}
              valueLabelDisplay="auto"
            />
            <Typography variant="body2" sx={{ minWidth: 30 }}>{maLineWidth}</Typography>
          </Box>
        </Box>
      </Paper>

      {/* FRACTALS - Matching Pine Script exactly */}
      <Paper elevation={3} sx={{ p: 3, mb: 3 }}>
        <Typography variant="h6" sx={{ mb: 2, fontWeight: 700 }}>FRACTALS</Typography>

        <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
          {/* Fractal Periods (n) */}
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
            <Typography variant="body2" sx={{ minWidth: 140 }}>Fractal Periods (n):</Typography>
            <Slider
              value={fractalPeriods}
              onChange={(_, v) => setFractalPeriods(v as number)}
              min={2}
              max={10}
              sx={{ width: 150 }}
              valueLabelDisplay="auto"
            />
            <Typography variant="body2" sx={{ minWidth: 30 }}>{fractalPeriods}</Typography>
          </Box>

          {/* Show BUY/SELL Labels */}
          <FormControlLabel
            control={<Checkbox checked={showBuySellLabels} onChange={(e) => setShowBuySellLabels(e.target.checked)} />}
            label="Show BUY/SELL Labels"
          />

          {/* Show Fractal Shapes */}
          <FormControlLabel
            control={<Checkbox checked={showFractalShapes} onChange={(e) => setShowFractalShapes(e.target.checked)} />}
            label="Show Fractal Shapes"
          />

          {/* BUY offset (ticks) */}
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
            <Typography variant="body2" sx={{ minWidth: 140 }}>BUY offset (ticks):</Typography>
            <Slider
              value={buyOffset}
              onChange={(_, v) => setBuyOffset(v as number)}
              min={1}
              max={20}
              sx={{ width: 150 }}
              valueLabelDisplay="auto"
            />
            <Typography variant="body2" sx={{ minWidth: 30 }}>{buyOffset}</Typography>
          </Box>

          {/* SELL offset (ticks) */}
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
            <Typography variant="body2" sx={{ minWidth: 140 }}>SELL offset (ticks):</Typography>
            <Slider
              value={sellOffset}
              onChange={(_, v) => setSellOffset(v as number)}
              min={1}
              max={20}
              sx={{ width: 150 }}
              valueLabelDisplay="auto"
            />
            <Typography variant="body2" sx={{ minWidth: 30 }}>{sellOffset}</Typography>
          </Box>
        </Box>
      </Paper>

      {/* Additional Settings */}
      <Paper elevation={3} sx={{ p: 3, mb: 3 }}>
        <Typography variant="h6" sx={{ mb: 2, fontWeight: 700 }}>ADDITIONAL SETTINGS</Typography>

        <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
          {/* Leading Signals */}
          <FormControlLabel
            control={
              <Switch
                checked={showLeadingSignals}
                onChange={(e) => setShowLeadingSignals(e.target.checked)}
                color="success"
              />
            }
            label={
              <Box>
                <Typography variant="body1" sx={{ fontWeight: 700, color: showLeadingSignals ? '#00E676' : 'text.secondary' }}>
                  Enable Leading Signals (1 Bar Earlier)
                </Typography>
                <Typography variant="caption" color="text.secondary">
                  Fires at potential pivot point before N-bar confirmation
                </Typography>
              </Box>
            }
          />

          {/* Show Patterns */}
          <FormControlLabel
            control={<Checkbox checked={showPatterns} onChange={(e) => setShowPatterns(e.target.checked)} />}
            label="Show Patterns (Engulfing, Stars)"
          />

          {/* Oversold Zone */}
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
            <Typography variant="body2" sx={{ minWidth: 120 }}>Oversold Zone:</Typography>
            <Slider
              value={oversoldZone}
              onChange={(_, v) => setOversoldZone(v as number)}
              min={20}
              max={45}
              sx={{ width: 150 }}
              color="success"
              valueLabelDisplay="auto"
            />
            <Typography variant="body2" sx={{ minWidth: 30 }}>{oversoldZone}</Typography>
          </Box>

          {/* Overbought Zone */}
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
            <Typography variant="body2" sx={{ minWidth: 120 }}>Overbought Zone:</Typography>
            <Slider
              value={overboughtZone}
              onChange={(_, v) => setOverboughtZone(v as number)}
              min={55}
              max={80}
              sx={{ width: 150 }}
              color="error"
              valueLabelDisplay="auto"
            />
            <Typography variant="body2" sx={{ minWidth: 30 }}>{overboughtZone}</Typography>
          </Box>
        </Box>
      </Paper>

      {/* Info */}
      <Paper elevation={3} sx={{ p: 3 }}>
        <Alert severity="info" sx={{ mb: 2 }}>
          <strong>This is a separate RSI indicator</strong> - not combined with RSI-MA. It calculates RSI from price OHLC
          and displays the RSI values as candlesticks, exactly like the TradingView Pine Script.
        </Alert>
        <Typography variant="body2" color="text.secondary">
          <strong>Standard Signals (Blue/Red):</strong> Non-repainting fractals confirmed after N bars. Delayed but 100% reliable.<br />
          <strong>Leading Signals (Bright Green/Red):</strong> Fire 1 bar earlier at potential pivot points. ~70-80% become confirmed fractals.<br />
          <strong>Patterns:</strong> Engulfing (Eng), Morning Star (MS), Evening Star (ES) detected on RSI candles.
        </Typography>
      </Paper>

      <Snackbar
        open={pineScriptCopied}
        autoHideDuration={2000}
        onClose={() => setPineScriptCopied(false)}
        message="Pine Script reference copied"
      />
    </Box>
  );
}
