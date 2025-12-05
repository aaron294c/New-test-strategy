/**
 * Gamma Wall Scanner Data Parser
 * Parses the dynamic VAR strings from Python script into structured data
 */

import {
  ParsedSymbolData,
  ParseError,
  GammaWall,
  FIELD_MAPPING,
  StandardDeviationBands,
  GammaDataResponse
} from './types';

export class GammaDataParser {
  private errors: ParseError[] = [];

  /**
   * Parse a single level_data string into structured symbol data
   * Format: "SYMBOL:field0,field1,...,field35;"
   */
  parseLevelData(levelDataString: string, lineNumber: number): ParsedSymbolData | null {
    try {
      // Extract symbol and data
      const colonIndex = levelDataString.indexOf(':');
      const semicolonIndex = levelDataString.indexOf(';');

      if (colonIndex === -1 || semicolonIndex === -1) {
        this.addError(lineNumber, 'UNKNOWN', 'Missing colon or semicolon delimiter');
        return null;
      }

      const symbol = levelDataString.substring(0, colonIndex).trim();
      const dataString = levelDataString.substring(colonIndex + 1, semicolonIndex);
      const fields = dataString.split(',').map(f => f.trim());

      // Validate field count (must be exactly 36)
      if (fields.length < 36) {
        this.addError(lineNumber, symbol, `Invalid field count: ${fields.length}, expected 36`);
        return null;
      }

      // Parse numeric fields with validation
      const parseField = (index: number, min?: number, max?: number): number => {
        const value = parseFloat(fields[index]);
        if (isNaN(value)) {
          this.addError(lineNumber, symbol, `Invalid numeric value at field ${index}`, index);
          return 0;
        }
        if (min !== undefined && value < min) return min;
        if (max !== undefined && value > max) return max;
        return value;
      };

      // Extract display name from symbol (e.g., "QQQ(NDX)" -> "QQQ (NDX)")
      const displayName = symbol.replace(/\(([^)]+)\)/, ' ($1)');

      // Parse gamma walls
      const walls: GammaWall[] = [];

      // Swing walls
      const stPutWall = parseField(FIELD_MAPPING.ST_PUT_WALL, 0);
      const stCallWall = parseField(FIELD_MAPPING.ST_CALL_WALL, 0);
      if (stPutWall > 0) {
        walls.push({
          strike: stPutWall,
          strength: parseField(FIELD_MAPPING.ST_PUT_STRENGTH, 0, 100),
          gex: parseField(FIELD_MAPPING.ST_PUT_GEX),
          dte: parseField(FIELD_MAPPING.ST_DTE, 1, 365),
          type: 'put',
          timeframe: 'swing',
        });
      }
      if (stCallWall > 0) {
        walls.push({
          strike: stCallWall,
          strength: parseField(FIELD_MAPPING.ST_CALL_STRENGTH, 0, 100),
          gex: parseField(FIELD_MAPPING.ST_CALL_GEX),
          dte: parseField(FIELD_MAPPING.ST_DTE, 1, 365),
          type: 'call',
          timeframe: 'swing',
        });
      }

      // Long-term walls
      const ltPutWall = parseField(FIELD_MAPPING.LT_PUT_WALL, 0);
      const ltCallWall = parseField(FIELD_MAPPING.LT_CALL_WALL, 0);
      if (ltPutWall > 0) {
        walls.push({
          strike: ltPutWall,
          strength: parseField(FIELD_MAPPING.LT_PUT_STRENGTH, 0, 100),
          gex: parseField(FIELD_MAPPING.LT_PUT_GEX),
          dte: parseField(FIELD_MAPPING.LT_DTE, 1, 365),
          type: 'put',
          timeframe: 'long',
        });
      }
      if (ltCallWall > 0) {
        walls.push({
          strike: ltCallWall,
          strength: parseField(FIELD_MAPPING.LT_CALL_STRENGTH, 0, 100),
          gex: parseField(FIELD_MAPPING.LT_CALL_GEX),
          dte: parseField(FIELD_MAPPING.LT_DTE, 1, 365),
          type: 'call',
          timeframe: 'long',
        });
      }

      // Quarterly walls
      const qPutWall = parseField(FIELD_MAPPING.Q_PUT_WALL, 0);
      const qCallWall = parseField(FIELD_MAPPING.Q_CALL_WALL, 0);
      if (qPutWall > 0) {
        walls.push({
          strike: qPutWall,
          strength: parseField(FIELD_MAPPING.Q_PUT_STRENGTH, 0, 100),
          gex: parseField(FIELD_MAPPING.Q_PUT_GEX),
          dte: parseField(FIELD_MAPPING.Q_DTE, 1, 365),
          type: 'put',
          timeframe: 'quarterly',
        });
      }
      if (qCallWall > 0) {
        walls.push({
          strike: qCallWall,
          strength: parseField(FIELD_MAPPING.Q_CALL_STRENGTH, 0, 100),
          gex: parseField(FIELD_MAPPING.Q_CALL_GEX),
          dte: parseField(FIELD_MAPPING.Q_DTE, 1, 365),
          type: 'call',
          timeframe: 'quarterly',
        });
      }

      // Standard deviation bands
      const sdBands: StandardDeviationBands = {
        lower_1sd: parseField(FIELD_MAPPING.LOWER_1SD),
        upper_1sd: parseField(FIELD_MAPPING.UPPER_1SD),
        lower_1_5sd: parseField(FIELD_MAPPING.LOWER_1_5SD),
        upper_1_5sd: parseField(FIELD_MAPPING.UPPER_1_5SD),
        lower_2sd: parseField(FIELD_MAPPING.LOWER_2SD),
        upper_2sd: parseField(FIELD_MAPPING.UPPER_2SD),
      };

      // Calculate current price from gamma flip or use middle of SD bands
      const gammaFlip = parseField(FIELD_MAPPING.GAMMA_FLIP);
      const currentPrice = gammaFlip > 0 ? gammaFlip : (sdBands.lower_1sd + sdBands.upper_1sd) / 2;

      // Parse market metrics
      const swingIV = parseField(FIELD_MAPPING.SWING_IV, 5, 300);
      const stDte = parseField(FIELD_MAPPING.ST_DTE, 1, 365);
      const ltDte = parseField(FIELD_MAPPING.LT_DTE, 1, 365);
      const qDte = parseField(FIELD_MAPPING.Q_DTE, 1, 365);

      // Calculate timeframe-specific IVs based on DTE
      const longIV = swingIV * (1.0 + (ltDte - stDte) * 0.01);
      const quarterlyIV = swingIV * (1.0 + (qDte - stDte) * 0.005);

      return {
        symbol,
        displayName,
        currentPrice,
        walls,
        sdBands,
        gammaFlip,
        swingIV,
        longIV,
        quarterlyIV,
        cpRatio: parseField(FIELD_MAPPING.CP_RATIO, 0.1, 10),
        trend: parseField(FIELD_MAPPING.TREND, -5, 5),
        activityScore: parseField(FIELD_MAPPING.ACTIVITY_SCORE, 0, 5),
        stDte,
        ltDte,
        qDte,
      };
    } catch (error) {
      this.addError(lineNumber, 'UNKNOWN', `Parse exception: ${error instanceof Error ? error.message : 'Unknown error'}`);
      return null;
    }
  }

  /**
   * Parse full GammaDataResponse from API or manual input
   */
  parseGammaData(data: GammaDataResponse): {
    symbols: ParsedSymbolData[];
    errors: ParseError[];
    metadata: {
      lastUpdate: string;
      marketRegime: string;
      currentVix: number;
      regimeAdjustmentEnabled: boolean;
    };
  } {
    this.errors = [];
    const symbols: ParsedSymbolData[] = [];

    data.level_data.forEach((levelData, index) => {
      const parsed = this.parseLevelData(levelData, index + 1);
      if (parsed) {
        symbols.push(parsed);
      }
    });

    return {
      symbols,
      errors: this.errors,
      metadata: {
        lastUpdate: data.last_update,
        marketRegime: data.market_regime,
        currentVix: data.current_vix,
        regimeAdjustmentEnabled: data.regime_adjustment_enabled,
      },
    };
  }

  /**
   * Parse manual text input (user paste)
   */
  parseManualInput(text: string): {
    symbols: ParsedSymbolData[];
    errors: ParseError[];
  } {
    this.errors = [];
    const symbols: ParsedSymbolData[] = [];

    const lines = text.split('\n').map(line => line.trim()).filter(line => line.length > 0);

    lines.forEach((line, index) => {
      // Skip comment lines
      if (line.startsWith('//') || line.startsWith('#')) {
        return;
      }

      // Extract level_data string if it's in var format
      let dataString = line;
      if (line.includes('var string level_data')) {
        const match = line.match(/"([^"]+)"/);
        if (match) {
          dataString = match[1];
        }
      }

      const parsed = this.parseLevelData(dataString, index + 1);
      if (parsed) {
        symbols.push(parsed);
      }
    });

    return {
      symbols,
      errors: this.errors,
    };
  }

  /**
   * Get errors from last parse operation
   */
  getErrors(): ParseError[] {
    return [...this.errors];
  }

  /**
   * Clear errors
   */
  clearErrors(): void {
    this.errors = [];
  }

  private addError(line: number, symbol: string, message: string, fieldIndex?: number): void {
    this.errors.push({
      line,
      symbol,
      message,
      fieldIndex,
    });
  }
}

/**
 * Apply regime adjustment to wall strengths
 * Matches the TradingView indicator logic
 */
export function applyRegimeAdjustment(
  strength: number,
  regime: string,
  boostFactor: number = 1.2
): number {
  if (regime.includes('High Volatility')) {
    return Math.min(100, strength * boostFactor);
  } else if (regime.includes('Low Volatility')) {
    return Math.max(0, strength * (2 - boostFactor));
  }
  return strength;
}

/**
 * Calculate dynamic pin zone percentage based on IV and DTE
 * Matches the TradingView max pain logic
 */
export function calculateDynamicPinZone(iv: number, dte: number): number {
  // Base calculation: IV% * sqrt(DTE/365) * 100
  const baseMove = (iv / 100) * Math.sqrt(dte / 365);
  return Math.min(10, Math.max(0.5, baseMove * 100));
}

/**
 * Format example level_data strings for testing
 */
export const EXAMPLE_LEVEL_DATA = [
  'SPX:7000.0,7000.0,6450.0,7400.0,6369.50,6999.00,7000.00,7000.00,5724.09,25.0,1.1,0.0,3.0,7000.00,7000.00,6212.12,7156.38,6054.74,7313.76,6470.00,7210.00,66.7,70.6,86.6,80.0,63.7,65.9,13,30,83,-150.4,157.2,-0.2,0.0,-11.1,8.4;',
  'QQQ(NDX):600.0,600.0,600.0,655.0,570.30,635.27,600.00,600.00,260.80,28.6,1.0,0.0,3.0,600.00,600.00,554.06,651.51,537.82,667.75,620.00,630.00,68.6,67.2,55.6,50.6,48.6,54.6,13,27,83,-410.0,244.5,-14.4,9.2,-0.9,1.5;',
  'AAPL:270.0,280.0,270.0,285.0,253.27,289.64,270.00,280.00,216.77,35.5,1.1,0.0,3.0,270.00,280.00,244.18,298.73,235.08,307.83,220.00,255.00,63.1,63.5,57.0,63.7,62.4,67.6,13,27,104,-38.4,116.9,-2.6,7.3,-7.6,32.6;',
  'INVALID:270.0,280.0;', // Malformed example with too few fields
];
