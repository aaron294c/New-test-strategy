/**
 * Gamma Debug Console Component
 * Shows parse errors and raw data blob for debugging
 */

import React, { useState } from 'react';
import { ParseError, GammaDataResponse } from './types';

interface GammaDebugConsoleProps {
  errors: ParseError[];
  rawData: GammaDataResponse | null;
  onManualPaste?: (text: string) => void;
}

export const GammaDebugConsole: React.FC<GammaDebugConsoleProps> = ({
  errors,
  rawData,
  onManualPaste,
}) => {
  const [expanded, setExpanded] = useState(false);
  const [manualInput, setManualInput] = useState('');

  const handleManualSubmit = () => {
    if (onManualPaste && manualInput.trim()) {
      onManualPaste(manualInput);
      setManualInput('');
    }
  };

  return (
    <div className="gamma-debug-console" style={styles.container}>
      <div style={styles.header} onClick={() => setExpanded(!expanded)}>
        <h3 style={styles.heading}>
          Debug Console {expanded ? '▼' : '▶'}
        </h3>
        {errors.length > 0 && (
          <span style={styles.errorBadge}>{errors.length} error(s)</span>
        )}
      </div>

      {expanded && (
        <div style={styles.content}>
          {/* Parse Errors Section */}
          <div style={styles.section}>
            <h4 style={styles.subheading}>Parse Errors</h4>
            {errors.length === 0 ? (
              <p style={styles.success}>✓ No parse errors</p>
            ) : (
              <div style={styles.errorList}>
                {errors.map((error, idx) => (
                  <div key={idx} style={styles.errorItem}>
                    <div style={styles.errorHeader}>
                      <span style={styles.errorLine}>Line {error.line}</span>
                      <span style={styles.errorSymbol}>{error.symbol}</span>
                    </div>
                    <div style={styles.errorMessage}>{error.message}</div>
                    {error.fieldIndex !== undefined && (
                      <div style={styles.errorField}>Field index: {error.fieldIndex}</div>
                    )}
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* Raw Data Section */}
          {rawData && (
            <div style={styles.section}>
              <h4 style={styles.subheading}>Raw Data Blob</h4>
              <div style={styles.metadata}>
                <div>Last Update: {rawData.last_update}</div>
                <div>Market Regime: {rawData.market_regime}</div>
                <div>Current VIX: {rawData.current_vix.toFixed(1)}</div>
                <div>
                  Regime Adjustment: {rawData.regime_adjustment_enabled ? 'Enabled' : 'Disabled'}
                </div>
              </div>
              <div style={styles.dataBlob}>
                <pre style={styles.pre}>
                  {rawData.level_data.map((line, idx) => (
                    <div key={idx} style={styles.dataLine}>
                      <span style={styles.lineNumber}>{idx + 1}:</span>
                      <span style={styles.lineContent}>{line}</span>
                    </div>
                  ))}
                </pre>
              </div>
            </div>
          )}

          {/* Manual Input Section */}
          {onManualPaste && (
            <div style={styles.section}>
              <h4 style={styles.subheading}>Manual Data Input</h4>
              <textarea
                value={manualInput}
                onChange={(e) => setManualInput(e.target.value)}
                placeholder="Paste level_data strings here (one per line)..."
                style={styles.textarea}
              />
              <button onClick={handleManualSubmit} style={styles.button}>
                Parse Manual Input
              </button>
              <small style={styles.hint}>
                Paste raw level_data strings or var declarations from Python output
              </small>
            </div>
          )}
        </div>
      )}
    </div>
  );
};

const styles: Record<string, React.CSSProperties> = {
  container: {
    backgroundColor: '#1a1a1a',
    borderRadius: '8px',
    marginTop: '20px',
    border: '1px solid #333333',
  },
  header: {
    padding: '15px 20px',
    cursor: 'pointer',
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    userSelect: 'none',
  },
  heading: {
    fontSize: '16px',
    margin: 0,
    color: '#FFFFFF',
  },
  errorBadge: {
    backgroundColor: '#FF4444',
    color: '#FFFFFF',
    padding: '4px 10px',
    borderRadius: '12px',
    fontSize: '12px',
    fontWeight: 'bold',
  },
  content: {
    padding: '0 20px 20px',
  },
  section: {
    marginBottom: '20px',
    paddingBottom: '15px',
    borderBottom: '1px solid #333333',
  },
  subheading: {
    fontSize: '14px',
    marginBottom: '10px',
    color: '#FFFFFF',
  },
  success: {
    color: '#44FF44',
    margin: 0,
  },
  errorList: {
    maxHeight: '200px',
    overflowY: 'auto',
  },
  errorItem: {
    backgroundColor: '#2a1a1a',
    padding: '10px',
    marginBottom: '8px',
    borderLeft: '3px solid #FF4444',
    borderRadius: '4px',
  },
  errorHeader: {
    display: 'flex',
    justifyContent: 'space-between',
    marginBottom: '5px',
    fontSize: '12px',
  },
  errorLine: {
    color: '#FF8844',
    fontWeight: 'bold',
  },
  errorSymbol: {
    color: '#4488FF',
    fontFamily: 'monospace',
  },
  errorMessage: {
    color: '#CCCCCC',
    fontSize: '13px',
  },
  errorField: {
    color: '#888888',
    fontSize: '11px',
    marginTop: '5px',
  },
  metadata: {
    backgroundColor: '#2a2a2a',
    padding: '10px',
    borderRadius: '4px',
    marginBottom: '10px',
    fontSize: '13px',
    color: '#CCCCCC',
  },
  dataBlob: {
    backgroundColor: '#0d0d0d',
    padding: '10px',
    borderRadius: '4px',
    maxHeight: '300px',
    overflowY: 'auto',
    fontSize: '12px',
  },
  pre: {
    margin: 0,
    fontFamily: 'monospace',
    whiteSpace: 'pre-wrap',
    wordBreak: 'break-all',
  },
  dataLine: {
    marginBottom: '4px',
  },
  lineNumber: {
    color: '#888888',
    marginRight: '10px',
    userSelect: 'none',
  },
  lineContent: {
    color: '#CCCCCC',
  },
  textarea: {
    width: '100%',
    minHeight: '150px',
    backgroundColor: '#2a2a2a',
    color: '#CCCCCC',
    border: '1px solid #444444',
    borderRadius: '4px',
    padding: '10px',
    fontFamily: 'monospace',
    fontSize: '12px',
    resize: 'vertical',
  },
  button: {
    backgroundColor: '#4488FF',
    color: '#FFFFFF',
    border: 'none',
    padding: '10px 20px',
    borderRadius: '4px',
    cursor: 'pointer',
    marginTop: '10px',
    fontSize: '14px',
    fontWeight: 'bold',
  },
  hint: {
    display: 'block',
    marginTop: '8px',
    fontSize: '11px',
    color: '#888888',
    fontStyle: 'italic',
  },
};
