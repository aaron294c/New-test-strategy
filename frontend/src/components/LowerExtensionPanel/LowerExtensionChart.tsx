import React, { useEffect, useRef } from 'react';
import { createChart, IChartApi, ISeriesApi, CandlestickData, LineData } from 'lightweight-charts';
import { LowerExtMetrics } from '../../utils/lowerExtensionCalculations';

interface CandleData {
  time: string | number;
  open: number;
  high: number;
  low: number;
  close: number;
}

interface LowerExtensionChartProps {
  metrics: LowerExtMetrics;
  candleData: CandleData[];
  showAnnotation?: boolean;
  showShading?: boolean;
}

const LowerExtensionChart: React.FC<LowerExtensionChartProps> = ({
  metrics,
  candleData,
  showAnnotation = true,
  showShading = true
}) => {
  const chartContainerRef = useRef<HTMLDivElement>(null);
  const chartRef = useRef<IChartApi | null>(null);
  const candleSeriesRef = useRef<ISeriesApi<'Candlestick'> | null>(null);
  const lowerExtLineRef = useRef<ISeriesApi<'Line'> | null>(null);

  useEffect(() => {
    if (!chartContainerRef.current) return;

    // Create chart
    const chart = createChart(chartContainerRef.current, {
      width: chartContainerRef.current.clientWidth,
      height: 400,
      layout: {
        background: { color: '#1a1a1a' },
        textColor: '#d1d4dc',
      },
      grid: {
        vertLines: { color: '#2b2b43' },
        horzLines: { color: '#2b2b43' },
      },
      crosshair: {
        mode: 1,
      },
      rightPriceScale: {
        borderColor: '#485c7b',
      },
      timeScale: {
        borderColor: '#485c7b',
        timeVisible: true,
        secondsVisible: false,
      },
    });

    chartRef.current = chart;

    // Add candlestick series
    const candleSeries = chart.addCandlestickSeries({
      upColor: '#26a69a',
      downColor: '#ef5350',
      borderVisible: false,
      wickUpColor: '#26a69a',
      wickDownColor: '#ef5350',
    });

    candleSeriesRef.current = candleSeries;

    // Add lower extension line (bold blue)
    const lowerExtLine = chart.addLineSeries({
      color: '#2962ff',
      lineWidth: 3,
      lineStyle: 0, // solid
      title: 'Lower Extension',
      priceLineVisible: true,
      lastValueVisible: true,
    });

    lowerExtLineRef.current = lowerExtLine;

    // Handle resize
    const handleResize = () => {
      if (chartContainerRef.current && chartRef.current) {
        chartRef.current.applyOptions({
          width: chartContainerRef.current.clientWidth,
        });
      }
    };

    window.addEventListener('resize', handleResize);

    return () => {
      window.removeEventListener('resize', handleResize);
      chart.remove();
    };
  }, []);

  useEffect(() => {
    if (!candleSeriesRef.current || !lowerExtLineRef.current) return;

    // Update candle data
    const formattedCandles: CandlestickData[] = candleData.map(c => ({
      time: typeof c.time === 'string' ? new Date(c.time).getTime() / 1000 : c.time,
      open: c.open,
      high: c.high,
      low: c.low,
      close: c.close,
    }));

    candleSeriesRef.current.setData(formattedCandles);

    // Create lower extension line data (horizontal line at lower_ext value)
    const lowerExtLineData: LineData[] = candleData.map(c => ({
      time: typeof c.time === 'string' ? new Date(c.time).getTime() / 1000 : c.time,
      value: metrics.lower_ext,
    }));

    lowerExtLineRef.current.setData(lowerExtLineData);

    // Fit content
    if (chartRef.current) {
      chartRef.current.timeScale().fitContent();
    }
  }, [candleData, metrics.lower_ext]);

  // Render shading below lower_ext when breached
  useEffect(() => {
    if (!chartContainerRef.current || !showShading) return;

    // This would require custom rendering or additional series
    // For now, we'll use a simple visual indicator in the annotation
  }, [metrics.is_below_lower_ext, showShading]);

  return (
    <div style={{ position: 'relative', width: '100%' }}>
      <div ref={chartContainerRef} style={{ width: '100%' }} />

      {showAnnotation && (
        <div
          style={{
            position: 'absolute',
            top: '10px',
            left: '10px',
            background: metrics.is_below_lower_ext
              ? 'rgba(34, 197, 94, 0.9)'
              : 'rgba(107, 114, 128, 0.9)',
            color: 'white',
            padding: '8px 12px',
            borderRadius: '6px',
            fontSize: '14px',
            fontWeight: '600',
            boxShadow: '0 2px 8px rgba(0,0,0,0.3)',
            zIndex: 10,
          }}
        >
          {metrics.is_below_lower_ext ? (
            <>
              <span style={{ fontSize: '18px' }}>↓</span> {metrics.pct_dist_lower_ext}% below lower_ext
            </>
          ) : (
            <>
              <span style={{ fontSize: '18px' }}>↑</span> {metrics.pct_dist_lower_ext}% above lower_ext
            </>
          )}
        </div>
      )}

      {showShading && metrics.is_below_lower_ext && (
        <div
          style={{
            position: 'absolute',
            bottom: '0',
            left: '0',
            right: '0',
            height: '40px',
            background: 'linear-gradient(to top, rgba(34, 197, 94, 0.1), transparent)',
            pointerEvents: 'none',
            zIndex: 5,
          }}
        />
      )}
    </div>
  );
};

export default LowerExtensionChart;
