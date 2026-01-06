import { useState, useEffect, useCallback } from 'react';

export interface GammaSymbolData {
  symbol: string;
  current_price: number;
  timestamp: string;
  st_put_wall: number;
  lt_put_wall: number;
  q_put_wall: number;
  wk_put_wall: number;
  st_put_distance: number;
  lt_put_distance: number;
  q_put_distance: number;
  st_call_wall: number;
  lt_call_wall: number;
  q_call_wall: number;
  gamma_flip: number;
  max_pain: number;
  lower_1sd: number;
  upper_1sd: number;
  lower_2sd: number;
  upper_2sd: number;
  put_wall_methods?: {
    swing?: {
      max_gex: number;
      weighted_centroid: number;
      cumulative_threshold: number;
      weighted_combo: number;
      confidence: string;
    };
  };
  category: string;
}

export interface GammaDataResponse {
  timestamp: string;
  last_update: string;
  market_regime: string;
  vix: number;
  weights: Record<string, number>;
  symbols: Record<string, GammaSymbolData>;
}

export function useGammaData() {
  const [data, setData] = useState<GammaDataResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchData = useCallback(async (forceRefresh = false) => {
    setLoading(true);
    setError(null);

    try {
      // Try API endpoint first
      const apiUrl = forceRefresh 
        ? '/api/gamma/refresh'
        : '/api/gamma/data';
      
      let response = await fetch(apiUrl, {
        method: forceRefresh ? 'POST' : 'GET',
      });

      if (response.ok) {
        const result = await response.json();
        if (result.status === 'success' && result.data) {
          setData(result.data);
          setLoading(false);
          return;
        }
      }

      // Fallback to static JSON file
      response = await fetch('/data/gamma_walls.json');
      if (response.ok) {
        const jsonData = await response.json();
        setData(jsonData);
      } else {
        throw new Error('Failed to fetch gamma data from any source');
      }
    } catch (err) {
      console.error('Error fetching gamma data:', err);
      setError(err instanceof Error ? err.message : 'Unknown error');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  const refresh = useCallback(() => {
    fetchData(true);
  }, [fetchData]);

  return { data, loading, error, refresh };
}
