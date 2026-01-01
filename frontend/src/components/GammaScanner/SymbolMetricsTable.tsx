/**
 * Symbol Metrics Table - Compact TradingView-style metrics display
 */

import React from 'react';
import { ParsedSymbolData } from './types';

interface SymbolMetricsTableProps {
  symbols: ParsedSymbolData[];
}

const TV_COLORS = {
  background: '#131722',
  surface: '#1E222D',
  border: '#2A2E39',
  text: '#787B86',
  textBright: '#D1D4DC',
  green: '#26A69A',
  red: '#EF5350',
  orange: '#FFA726',
};

export const SymbolMetricsTable: React.FC<SymbolMetricsTableProps> = ({ symbols }) => {
  if (symbols.length === 0) {
    return (
      <div style={styles.emptyState}>
        <span style={styles.emptyText}>No symbol data available</span>
      </div>
    );
  }

  return (
    <div style={styles.container}>
      <table style={styles.table}>
        <thead>
          <tr style={styles.headerRow}>
            <th style={styles.headerCell}>Symbol</th>
            <th style={styles.headerCell}>Price</th>
            <th style={styles.headerCell}>Γ Flip</th>
            <th style={styles.headerCell}>IV%</th>
            <th style={styles.headerCell}>ST Put</th>
            <th style={styles.headerCell}>ST Call</th>
            <th style={styles.headerCell}>LT Put</th>
            <th style={styles.headerCell}>LT Call</th>
            <th style={styles.headerCell}>-1σ</th>
            <th style={styles.headerCell}>+1σ</th>
            <th style={styles.headerCell}>Total GEX</th>
          </tr>
        </thead>
        <tbody>
          {symbols.map((symbol, idx) => {
            const stPut = symbol.walls.find((w) => w.type === 'put' && w.timeframe === 'swing');
            const stCall = symbol.walls.find((w) => w.type === 'call' && w.timeframe === 'swing');
            const ltPut = symbol.walls.find((w) => w.type === 'put' && w.timeframe === 'long');
            const ltCall = symbol.walls.find((w) => w.type === 'call' && w.timeframe === 'long');

            const totalGEX = symbol.walls.reduce((sum, w) => sum + Math.abs(w.gex), 0);

            return (
              <tr key={idx} style={idx % 2 === 0 ? styles.rowEven : styles.rowOdd}>
                <td style={styles.cellSymbol}>{symbol.displayName}</td>
                <td style={styles.cell}>${symbol.currentPrice.toFixed(2)}</td>
                <td style={{ ...styles.cell, color: TV_COLORS.orange }}>
                  ${symbol.gammaFlip > 0 ? symbol.gammaFlip.toFixed(2) : '-'}
                </td>
                <td style={styles.cell}>{symbol.swingIV.toFixed(1)}%</td>
                <td style={{ ...styles.cell, color: TV_COLORS.green }}>
                  {stPut ? `$${stPut.strike.toFixed(0)} (${stPut.strength.toFixed(0)})` : '-'}
                </td>
                <td style={{ ...styles.cell, color: TV_COLORS.red }}>
                  {stCall ? `$${stCall.strike.toFixed(0)} (${stCall.strength.toFixed(0)})` : '-'}
                </td>
                <td style={{ ...styles.cell, color: TV_COLORS.green }}>
                  {ltPut ? `$${ltPut.strike.toFixed(0)} (${ltPut.strength.toFixed(0)})` : '-'}
                </td>
                <td style={{ ...styles.cell, color: TV_COLORS.red }}>
                  {ltCall ? `$${ltCall.strike.toFixed(0)} (${ltCall.strength.toFixed(0)})` : '-'}
                </td>
                <td style={styles.cell}>${symbol.sdBands.lower_1sd.toFixed(2)}</td>
                <td style={styles.cell}>${symbol.sdBands.upper_1sd.toFixed(2)}</td>
                <td style={styles.cell}>${totalGEX.toFixed(1)}M</td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
};

const styles: Record<string, React.CSSProperties> = {
  container: {
    width: '100%',
    overflowX: 'auto',
    backgroundColor: TV_COLORS.surface,
    borderRadius: '4px',
  },
  table: {
    width: '100%',
    borderCollapse: 'collapse',
    fontSize: '11px',
    fontFamily: '"Roboto", "Open Sans", "Arial", sans-serif',
  },
  headerRow: {
    backgroundColor: TV_COLORS.background,
    borderBottom: `1px solid ${TV_COLORS.border}`,
  },
  headerCell: {
    padding: '10px 12px',
    textAlign: 'left',
    fontWeight: 600,
    color: TV_COLORS.textBright,
    textTransform: 'uppercase',
    fontSize: '10px',
    letterSpacing: '0.5px',
    whiteSpace: 'nowrap',
  },
  rowEven: {
    backgroundColor: TV_COLORS.surface,
    borderBottom: `1px solid ${TV_COLORS.border}`,
  },
  rowOdd: {
    backgroundColor: 'rgba(19, 23, 34, 0.3)',
    borderBottom: `1px solid ${TV_COLORS.border}`,
  },
  cell: {
    padding: '8px 12px',
    color: TV_COLORS.text,
    whiteSpace: 'nowrap',
  },
  cellSymbol: {
    padding: '8px 12px',
    color: TV_COLORS.textBright,
    fontWeight: 600,
    whiteSpace: 'nowrap',
  },
  emptyState: {
    display: 'flex',
    justifyContent: 'center',
    alignItems: 'center',
    padding: '40px',
    backgroundColor: TV_COLORS.surface,
    borderRadius: '4px',
  },
  emptyText: {
    fontSize: '12px',
    color: TV_COLORS.text,
  },
};
