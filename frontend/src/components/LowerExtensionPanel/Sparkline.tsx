import React, { useRef, useEffect } from 'react';

interface SparklineProps {
  data: Array<{ timestamp: string | number; price: number }>;
  lowerExt: number;
  width?: number;
  height?: number;
}

const Sparkline: React.FC<SparklineProps> = ({ data, lowerExt, width = 400, height = 100 }) => {
  const canvasRef = useRef<HTMLCanvasElement>(null);

  useEffect(() => {
    if (!canvasRef.current || data.length === 0) return;

    const canvas = canvasRef.current;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    // Set canvas size with device pixel ratio for crisp rendering
    const dpr = window.devicePixelRatio || 1;
    canvas.width = width * dpr;
    canvas.height = height * dpr;
    canvas.style.width = `${width}px`;
    canvas.style.height = `${height}px`;
    ctx.scale(dpr, dpr);

    // Clear canvas
    ctx.clearRect(0, 0, width, height);

    // Sort data by timestamp
    const sortedData = [...data].sort((a, b) => {
      const tsA = typeof a.timestamp === 'string' ? new Date(a.timestamp).getTime() : a.timestamp;
      const tsB = typeof b.timestamp === 'string' ? new Date(b.timestamp).getTime() : b.timestamp;
      return tsA - tsB;
    });

    // Find min and max prices for scaling
    const prices = sortedData.map(d => d.price);
    const minPrice = Math.min(...prices, lowerExt);
    const maxPrice = Math.max(...prices, lowerExt);
    const priceRange = maxPrice - minPrice;

    // Add padding
    const padding = 10;
    const chartWidth = width - 2 * padding;
    const chartHeight = height - 2 * padding;

    // Scale functions
    const scaleX = (index: number) => padding + (index / (sortedData.length - 1)) * chartWidth;
    const scaleY = (price: number) => padding + chartHeight - ((price - minPrice) / priceRange) * chartHeight;

    // Draw lower_ext horizontal line
    const lowerExtY = scaleY(lowerExt);
    ctx.strokeStyle = '#2962ff';
    ctx.lineWidth = 2;
    ctx.setLineDash([5, 5]);
    ctx.beginPath();
    ctx.moveTo(padding, lowerExtY);
    ctx.lineTo(width - padding, lowerExtY);
    ctx.stroke();
    ctx.setLineDash([]);

    // Draw price line
    ctx.strokeStyle = '#10b981';
    ctx.lineWidth = 2;
    ctx.beginPath();

    sortedData.forEach((point, index) => {
      const x = scaleX(index);
      const y = scaleY(point.price);

      if (index === 0) {
        ctx.moveTo(x, y);
      } else {
        ctx.lineTo(x, y);
      }
    });

    ctx.stroke();

    // Highlight breach points (where price < lowerExt)
    ctx.fillStyle = '#22c55e';
    sortedData.forEach((point, index) => {
      if (point.price < lowerExt) {
        const x = scaleX(index);
        const y = scaleY(point.price);
        ctx.beginPath();
        ctx.arc(x, y, 3, 0, Math.PI * 2);
        ctx.fill();
      }
    });

    // Draw current price point
    const lastPoint = sortedData[sortedData.length - 1];
    const lastX = scaleX(sortedData.length - 1);
    const lastY = scaleY(lastPoint.price);
    ctx.fillStyle = lastPoint.price < lowerExt ? '#22c55e' : '#6b7280';
    ctx.beginPath();
    ctx.arc(lastX, lastY, 4, 0, Math.PI * 2);
    ctx.fill();

    // Draw labels
    ctx.fillStyle = '#9ca3af';
    ctx.font = '10px sans-serif';
    ctx.textAlign = 'right';
    ctx.fillText(`$${maxPrice.toFixed(2)}`, width - padding - 5, padding + 10);
    ctx.fillText(`$${minPrice.toFixed(2)}`, width - padding - 5, height - padding);
    ctx.fillText(`$${lowerExt.toFixed(2)}`, padding + 50, lowerExtY - 5);
  }, [data, lowerExt, width, height]);

  return (
    <div style={{ position: 'relative' }}>
      <canvas
        ref={canvasRef}
        style={{
          width: `${width}px`,
          height: `${height}px`,
          background: '#1f2937',
          borderRadius: '6px',
        }}
      />
      <div
        style={{
          marginTop: '8px',
          fontSize: '11px',
          color: '#9ca3af',
          display: 'flex',
          gap: '16px',
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
          <div style={{ width: '12px', height: '2px', background: '#10b981' }} />
          <span>Price</span>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
          <div style={{ width: '12px', height: '2px', background: '#2962ff', borderTop: '2px dashed #2962ff' }} />
          <span>Lower Ext</span>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
          <div style={{ width: '8px', height: '8px', borderRadius: '50%', background: '#22c55e' }} />
          <span>Breach</span>
        </div>
      </div>
    </div>
  );
};

export default Sparkline;
