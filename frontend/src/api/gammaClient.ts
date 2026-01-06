const API_BASE_URL = import.meta.env.VITE_API_URL ?? '';

export interface GammaLevel {
  price: number;
  distance_pct: number;
  direction: 'ABOVE' | 'BELOW';
}

export interface SymbolGammaData {
  symbol: string;
  current_price: number;
  timestamp: string;
  levels: {
    st_put: GammaLevel;
    lt_put: GammaLevel;
    q_put: GammaLevel;
    gamma_flip: GammaLevel;
  };
  st_put_methods: {
    max_gex: number;
    centroid: number;
    cumulative: number;
    weighted_combo: number;
  };
}

export interface AllGammaData {
  timestamp: string;
  market_regime: string;
  vix: number;
  weights: Record<string, number>;
  symbols: Record<string, any>;
}

/**
 * Fetch gamma data for all symbols
 */
export async function fetchAllGammaData(refresh = false): Promise<AllGammaData> {
  const url = `${API_BASE_URL}/api/gamma/all${refresh ? '?refresh=true' : ''}`;
  const response = await fetch(url);
  
  if (!response.ok) {
    throw new Error(`Failed to fetch gamma data: ${response.statusText}`);
  }
  
  const result = await response.json();
  if (result.status === 'error') {
    throw new Error(result.message);
  }
  
  return result.data;
}

/**
 * Fetch gamma data for a specific symbol
 */
export async function fetchSymbolGamma(symbol: string): Promise<SymbolGammaData> {
  const response = await fetch(`${API_BASE_URL}/api/gamma/${symbol}`);
  
  if (!response.ok) {
    throw new Error(`Failed to fetch gamma for ${symbol}`);
  }
  
  const result = await response.json();
  if (result.status === 'error') {
    throw new Error(result.message);
  }
  
  return result.data;
}

/**
 * Force refresh all gamma data
 */
export async function refreshGammaData(): Promise<{ message: string; timestamp: string }> {
  const response = await fetch(`${API_BASE_URL}/api/gamma/refresh`, {
    method: 'POST',
  });
  
  if (!response.ok) {
    throw new Error('Failed to refresh gamma data');
  }
  
  const result = await response.json();
  return result;
}
