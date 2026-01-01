/**
 * Gamma Symbol Table Component
 * Per-symbol metrics table with sortable columns
 */

import React, { useState, useMemo } from 'react';
import { ParsedSymbolData } from './types';

interface GammaSymbolTableProps {
  symbols: ParsedSymbolData[];
}

type SortColumn = 'symbol' | 'price' | 'gammaFlip' | 'distanceToFlip' | 'swingIV' | 'cpRatio';
type SortDirection = 'asc' | 'desc';

export const GammaSymbolTable: React.FC<GammaSymbolTableProps> = ({ symbols }) => {
  const [sortColumn, setSortColumn] = useState<SortColumn>('symbol');
  const [sortDirection, setSortDirection] = useState<SortDirection>('asc');

  const sortedSymbols = useMemo(() => {
    return [...symbols].sort((a, b) => {
      let aVal: number | string;
      let bVal: number | string;

      switch (sortColumn) {
        case 'symbol':
          aVal = a.displayName;
          bVal = b.displayName;
          break;
        case 'price':
          aVal = a.currentPrice;
          bVal = b.currentPrice;
          break;
        case 'gammaFlip':
          aVal = a.gammaFlip;
          bVal = b.gammaFlip;
          break;
        case 'distanceToFlip':
          aVal = ((a.gammaFlip - a.currentPrice) / a.currentPrice) * 100;
          bVal = ((b.gammaFlip - b.currentPrice) / b.currentPrice) * 100;
          break;
        case 'swingIV':
          aVal = a.swingIV;
          bVal = b.swingIV;
          break;
        case 'cpRatio':
          aVal = a.cpRatio;
          bVal = b.cpRatio;
          break;
        default:
          aVal = a.displayName;
          bVal = b.displayName;
      }

      if (typeof aVal === 'string' && typeof bVal === 'string') {
        return sortDirection === 'asc'
          ? aVal.localeCompare(bVal)
          : bVal.localeCompare(aVal);
      }

      return sortDirection === 'asc'
        ? (aVal as number) - (bVal as number)
        : (bVal as number) - (aVal as number);
    });
  }, [symbols, sortColumn, sortDirection]);

  const handleSort = (column: SortColumn) => {
    if (sortColumn === column) {
      setSortDirection(sortDirection === 'asc' ? 'desc' : 'asc');
    } else {
      setSortColumn(column);
      setSortDirection('asc');
    }
  };

  const SortableHeader: React.FC<{ column: SortColumn; children: React.ReactNode }> = ({
    column,
    children,
  }) => (
    <th onClick={() => handleSort(column)} style={styles.th}>
      {children}
      {sortColumn === column && (
        <span style={{ marginLeft: '5px' }}>
          {sortDirection === 'asc' ? '↑' : '↓'}
        </span>
      )}
    </th>
  );

  return (
    <div className="gamma-symbol-table" style={styles.container}>
      <h3 style={styles.heading}>Symbol Metrics</h3>
      <div style={styles.tableWrapper}>
        <table style={styles.table}>
          <thead>
            <tr>
              <SortableHeader column="symbol">Symbol</SortableHeader>
              <SortableHeader column="price">Price</SortableHeader>
              <SortableHeader column="gammaFlip">Gamma Flip</SortableHeader>
              <SortableHeader column="distanceToFlip">Dist to Flip %</SortableHeader>
              <SortableHeader column="swingIV">Swing IV %</SortableHeader>
              <SortableHeader column="cpRatio">C/P Ratio</SortableHeader>
              <th style={styles.th}>Walls</th>
              <th style={styles.th}>Strongest Wall</th>
            </tr>
          </thead>
          <tbody>
            {sortedSymbols.map((symbol) => {
              const distanceToFlip = ((symbol.gammaFlip - symbol.currentPrice) / symbol.currentPrice) * 100;
              const strongestWall = symbol.walls.reduce(
                (max, wall) => (wall.strength > max.strength ? wall : max),
                symbol.walls[0] || { strength: 0, strike: 0, timeframe: '', type: '' }
              );

              return (
                <tr key={symbol.symbol} style={styles.tr}>
                  <td style={styles.td}>{symbol.displayName}</td>
                  <td style={styles.tdNumber}>${symbol.currentPrice.toFixed(2)}</td>
                  <td style={styles.tdNumber}>${symbol.gammaFlip.toFixed(2)}</td>
                  <td
                    style={{
                      ...styles.tdNumber,
                      color: distanceToFlip > 0 ? '#44FF44' : '#FF4444',
                    }}
                  >
                    {distanceToFlip > 0 ? '+' : ''}
                    {distanceToFlip.toFixed(2)}%
                  </td>
                  <td style={styles.tdNumber}>{symbol.swingIV.toFixed(1)}%</td>
                  <td style={styles.tdNumber}>{symbol.cpRatio.toFixed(2)}</td>
                  <td style={styles.tdNumber}>{symbol.walls.length}</td>
                  <td style={styles.td}>
                    {strongestWall.strength > 0 ? (
                      <span>
                        ${strongestWall.strike.toFixed(0)} {strongestWall.type} (
                        {strongestWall.strength.toFixed(0)})
                      </span>
                    ) : (
                      '-'
                    )}
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
};

const styles: Record<string, React.CSSProperties> = {
  container: {
    backgroundColor: '#1a1a1a',
    padding: '20px',
    borderRadius: '8px',
    marginTop: '20px',
  },
  heading: {
    fontSize: '18px',
    marginBottom: '15px',
    color: '#FFFFFF',
  },
  tableWrapper: {
    overflowX: 'auto',
  },
  table: {
    width: '100%',
    borderCollapse: 'collapse',
    fontSize: '14px',
  },
  th: {
    backgroundColor: '#2a2a2a',
    color: '#FFFFFF',
    padding: '12px 8px',
    textAlign: 'left',
    borderBottom: '2px solid #444444',
    cursor: 'pointer',
    userSelect: 'none',
    whiteSpace: 'nowrap',
  },
  tr: {
    borderBottom: '1px solid #333333',
  },
  td: {
    padding: '10px 8px',
    color: '#CCCCCC',
  },
  tdNumber: {
    padding: '10px 8px',
    color: '#CCCCCC',
    textAlign: 'right',
    fontFamily: 'monospace',
  },
};
