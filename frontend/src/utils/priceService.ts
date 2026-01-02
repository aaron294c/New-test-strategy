/**
 * Price Service - Fetch real-time stock prices
 *
 * Uses a fallback approach:
 * 1. Try Yahoo Finance API (free, no key needed)
 * 2. Fall back to estimated price from gamma data if fetch fails
 */

interface PriceData {
  symbol: string;
  price: number;
  source: 'live' | 'estimated';
  timestamp: number;
}

// Cache prices for 60 seconds
const priceCache = new Map<string, PriceData>();
const CACHE_DURATION = 60 * 1000; // 60 seconds

/**
 * Clean symbol for API requests
 * SPX -> ^SPX, NDX -> ^NDX
 */
function cleanSymbol(symbol: string): string {
  // Extract base symbol from display name
  if (symbol.includes('(')) {
    const match = symbol.match(/\(([^)]+)\)/);
    if (match) {
      symbol = match[1];
    }
  }

  // Add ^ prefix for index symbols
  if (['SPX', 'NDX', 'VIX', 'RUT', 'DJI'].includes(symbol)) {
    return `^${symbol}`;
  }

  return symbol;
}

const API_BASE_URL = import.meta.env.VITE_API_URL || '';

/**
 * Fetch real price from our backend API
 */
async function fetchBackendPrice(symbol: string): Promise<number | null> {
  try {
    const response = await fetch(`${API_BASE_URL}/api/prices/${encodeURIComponent(symbol)}`);
    if (!response.ok) {
      return null;
    }

    const data = await response.json();
    if (typeof data.price === 'number' && data.price > 0) {
      console.log(`Fetched ${symbol}: $${data.price} from ${data.source}`);
      return data.price;
    }

    return null;
  } catch (error) {
    console.warn(`Failed to fetch backend price for ${symbol}:`, error);
    return null;
  }
}

/**
 * Get current price with caching
 */
export async function getCurrentPrice(
  symbol: string,
  estimatedPrice: number
): Promise<PriceData> {
  const cacheKey = symbol;
  const now = Date.now();

  // Check cache
  const cached = priceCache.get(cacheKey);
  if (cached && (now - cached.timestamp) < CACHE_DURATION) {
    return cached;
  }

  // Try to fetch live price from backend
  const livePrice = await fetchBackendPrice(symbol);

  if (livePrice !== null) {
    const priceData: PriceData = {
      symbol,
      price: livePrice,
      source: 'live',
      timestamp: now,
    };
    priceCache.set(cacheKey, priceData);
    return priceData;
  }

  // Fall back to estimated price
  const priceData: PriceData = {
    symbol,
    price: estimatedPrice,
    source: 'estimated',
    timestamp: now,
  };
  priceCache.set(cacheKey, priceData);
  return priceData;
}

/**
 * Batch fetch prices for multiple symbols
 */
export async function batchGetPrices(
  symbols: Array<{ symbol: string; estimatedPrice: number }>
): Promise<Map<string, PriceData>> {
  const results = new Map<string, PriceData>();

  // Fetch all prices in parallel
  const promises = symbols.map(({ symbol, estimatedPrice }) =>
    getCurrentPrice(symbol, estimatedPrice).then(priceData => {
      results.set(symbol, priceData);
    })
  );

  await Promise.all(promises);

  return results;
}

/**
 * Clear price cache
 */
export function clearPriceCache(): void {
  priceCache.clear();
}
