"""
Real-time Stock Price Fetcher
Provides current market prices for stocks and indices

Uses multiple free APIs in fallback order:
1. Yahoo Finance V8 API (direct, no library)
2. Finnhub (free tier, no key needed for quotes)
3. yfinance (fallback)
"""

import yfinance as yf
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Dict, List, Optional
from datetime import datetime
import logging
import requests
import json

from ticker_utils import resolve_yahoo_symbol

router = APIRouter()
logger = logging.getLogger(__name__)

class PriceData(BaseModel):
    symbol: str
    price: float
    source: str
    timestamp: str

class BatchPriceRequest(BaseModel):
    symbols: List[str]

class BatchPriceResponse(BaseModel):
    prices: Dict[str, PriceData]
    timestamp: str

def clean_symbol(symbol: str) -> str:
    """Clean symbol for yfinance API"""
    # Remove display suffix like (NDX)
    if '(' in symbol:
        parts = symbol.split('(')
        if len(parts) > 1 and ')' in parts[1]:
            return parts[1].split(')')[0]
    return symbol

def fetch_yahoo_direct(symbol: str) -> Optional[float]:
    """Fetch from Yahoo Finance V8 API directly (bypasses yfinance library)"""
    try:
        url = f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol}"
        params = {'interval': '1d', 'range': '1d'}
        headers = {'User-Agent': 'Mozilla/5.0'}

        response = requests.get(url, params=params, headers=headers, timeout=5)
        if response.status_code == 200:
            data = response.json()
            price = data.get('chart', {}).get('result', [{}])[0].get('meta', {}).get('regularMarketPrice')
            if price and price > 0:
                logger.info(f"Yahoo Direct API success for {symbol}: ${price}")
                return float(price)
    except Exception as e:
        logger.warning(f"Yahoo Direct API failed for {symbol}: {e}")
    return None

def fetch_finnhub(symbol: str) -> Optional[float]:
    """Fetch from Finnhub free API"""
    try:
        # Finnhub free tier allows quotes without API key for major symbols
        url = f"https://finnhub.io/api/v1/quote"
        params = {'symbol': symbol}
        headers = {'X-Finnhub-Token': 'demo'}  # Use demo token

        response = requests.get(url, params=params, headers=headers, timeout=5)
        if response.status_code == 200:
            data = response.json()
            price = data.get('c')  # current price
            if price and price > 0:
                logger.info(f"Finnhub API success for {symbol}: ${price}")
                return float(price)
    except Exception as e:
        logger.warning(f"Finnhub API failed for {symbol}: {e}")
    return None

def get_current_price(symbol: str) -> Optional[PriceData]:
    """Fetch current price using multiple APIs with fallback"""
    try:
        # Clean the symbol
        clean_sym = clean_symbol(symbol)

        # Add ^ prefix for indices if needed
        yahoo_sym = clean_sym
        if clean_sym in ['SPX', 'NDX', 'VIX', 'DJI', 'RUT']:
            yahoo_sym = f'^{clean_sym}'
        else:
            yahoo_sym = resolve_yahoo_symbol(yahoo_sym)

        # Use QQQ as proxy for NDX if symbol is QQQ(NDX)
        if 'NDX' in symbol and 'QQQ' in symbol:
            yahoo_sym = 'QQQ'
            clean_sym = 'QQQ'

        logger.info(f"Fetching price for {symbol} -> {yahoo_sym}")

        price = None
        source = "unknown"

        # Method 1: Yahoo Finance Direct API (fastest, most reliable)
        price = fetch_yahoo_direct(yahoo_sym)
        if price:
            source = "yahoo_direct"

        # Method 2: Finnhub API (fallback for stocks)
        if not price and not yahoo_sym.startswith('^'):
            price = fetch_finnhub(clean_sym)
            if price:
                source = "finnhub"

        # Method 3: yfinance library (slowest, but most compatible)
        if not price:
            try:
                ticker = yf.Ticker(yahoo_sym)
                hist = ticker.history(period="1d")
                if not hist.empty:
                    price = hist['Close'].iloc[-1]
                    source = "yfinance_history"
                    logger.info(f"yfinance fallback success for {yahoo_sym}: ${price}")
            except Exception as e:
                logger.warning(f"yfinance failed for {yahoo_sym}: {e}")

        if price and price > 0:
            return PriceData(
                symbol=symbol,
                price=float(price),
                source=source,
                timestamp=datetime.now().isoformat()
            )

        logger.error(f"All methods failed for {symbol}")
        return None

    except Exception as e:
        logger.error(f"Error fetching price for {symbol}: {e}")
        return None

@router.get("/api/prices/{symbol}")
async def get_price(symbol: str):
    """Get current price for a single symbol"""
    price_data = get_current_price(symbol)

    if not price_data:
        raise HTTPException(
            status_code=404,
            detail=f"Could not fetch price for {symbol}"
        )

    return price_data

@router.post("/api/prices/batch")
async def get_batch_prices(request: BatchPriceRequest):
    """Get current prices for multiple symbols"""
    prices = {}

    for symbol in request.symbols:
        price_data = get_current_price(symbol)
        if price_data:
            prices[symbol] = price_data

    return BatchPriceResponse(
        prices=prices,
        timestamp=datetime.now().isoformat()
    )

@router.get("/api/prices/health")
async def health_check():
    """Health check endpoint"""
    # Test with AAPL
    test_price = get_current_price("AAPL")

    return {
        "status": "healthy" if test_price else "degraded",
        "test_symbol": "AAPL",
        "test_price": test_price.price if test_price else None,
        "timestamp": datetime.now().isoformat()
    }
