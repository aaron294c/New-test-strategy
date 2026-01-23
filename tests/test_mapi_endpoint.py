#!/usr/bin/env python3
"""
MAPI Endpoint Test Suite
Tests all three sub-tab data sources and signal generation
"""

import sys
sys.path.insert(0, '../backend')

from fastapi.testclient import TestClient
from api import app
import json

client = TestClient(app)

def test_mapi_endpoint():
    """Test MAPI endpoint returns correct data structure"""
    print("=" * 60)
    print("MAPI ENDPOINT TEST SUITE")
    print("=" * 60)

    # Test with AAPL
    ticker = "AAPL"
    days = 252

    print(f"\n1. Testing endpoint: /api/mapi-chart/{ticker}?days={days}")
    response = client.get(f'/api/mapi-chart/{ticker}?days={days}')

    assert response.status_code == 200, f"Expected 200, got {response.status_code}"
    print("   ✓ Status code: 200")

    data = response.json()

    # Verify response structure
    assert data['success'] == True, "Response not successful"
    assert data['ticker'] == ticker, f"Expected ticker {ticker}, got {data['ticker']}"
    print(f"   ✓ Ticker: {data['ticker']}")

    chart_data = data['chart_data']

    # Verify data length
    assert len(chart_data['dates']) == days, f"Expected {days} dates, got {len(chart_data['dates'])}"
    print(f"   ✓ Data points: {len(chart_data['dates'])}")

    return chart_data, data['metadata']


def test_composite_tab_data(chart_data):
    """Test data for Composite Score tab"""
    print("\n2. Testing Composite Score Tab Data")

    # Verify composite score exists
    assert 'composite_score' in chart_data, "Missing composite_score"
    composite_scores = chart_data['composite_score']
    assert all(0 <= score <= 100 for score in composite_scores), "Composite scores out of range"
    print(f"   ✓ Composite scores: {len(composite_scores)} points (range: 0-100%)")

    # Verify signals exist
    assert 'strong_momentum_signals' in chart_data, "Missing strong_momentum_signals"
    assert 'pullback_signals' in chart_data, "Missing pullback_signals"
    assert 'exit_signals' in chart_data, "Missing exit_signals"

    strong_count = sum(chart_data['strong_momentum_signals'])
    pullback_count = sum(chart_data['pullback_signals'])
    exit_count = sum(chart_data['exit_signals'])

    print(f"   ✓ Strong momentum signals: {strong_count}")
    print(f"   ✓ Pullback signals: {pullback_count}")
    print(f"   ✓ Exit signals: {exit_count}")

    # Verify thresholds
    thresholds = chart_data['thresholds']
    assert thresholds['strong_momentum'] == 65, "Strong momentum threshold incorrect"
    assert thresholds['exit_threshold'] == 40, "Exit threshold incorrect"
    print(f"   ✓ Thresholds: Strong={thresholds['strong_momentum']}%, Exit={thresholds['exit_threshold']}%")


def test_components_tab_data(chart_data):
    """Test data for EDR & ESV tab"""
    print("\n3. Testing EDR & ESV Components Tab Data")

    # Verify EDR percentile
    assert 'edr_percentile' in chart_data, "Missing edr_percentile"
    edr_percentiles = chart_data['edr_percentile']
    assert all(0 <= p <= 100 for p in edr_percentiles), "EDR percentiles out of range"
    print(f"   ✓ EDR percentiles: {len(edr_percentiles)} points (range: 0-100%)")

    # Verify ESV percentile
    assert 'esv_percentile' in chart_data, "Missing esv_percentile"
    esv_percentiles = chart_data['esv_percentile']
    assert all(0 <= p <= 100 for p in esv_percentiles), "ESV percentiles out of range"
    print(f"   ✓ ESV percentiles: {len(esv_percentiles)} points (range: 0-100%)")

    # Verify current values
    current = chart_data['current']
    print(f"   ✓ Current EDR: {current['edr_percentile']:.2f}%")
    print(f"   ✓ Current ESV: {current['esv_percentile']:.2f}%")


def test_price_ema_tab_data(chart_data):
    """Test data for Price & EMAs tab"""
    print("\n4. Testing Price & EMAs Tab Data")

    # Verify price data
    assert 'close' in chart_data, "Missing close prices"
    prices = chart_data['close']
    assert all(p > 0 for p in prices), "Invalid prices"
    print(f"   ✓ Close prices: {len(prices)} points")

    # Verify EMA(20)
    assert 'ema20' in chart_data, "Missing ema20"
    ema20 = chart_data['ema20']
    assert all(e > 0 for e in ema20), "Invalid EMA(20)"
    print(f"   ✓ EMA(20): {len(ema20)} points")

    # Verify EMA(50)
    assert 'ema50' in chart_data, "Missing ema50"
    ema50 = chart_data['ema50']
    assert all(e > 0 for e in ema50), "Invalid EMA(50)"
    print(f"   ✓ EMA(50): {len(ema50)} points")

    # Verify current values
    current = chart_data['current']
    print(f"   ✓ Current Price: ${current['close']:.2f}")
    print(f"   ✓ Current EMA(20): ${current['ema20']:.2f}")
    print(f"   ✓ Current EMA(50): ${current['ema50']:.2f}")
    print(f"   ✓ Distance to EMA(20): {current['distance_to_ema20_pct']:.2f}%")


def test_current_metrics(chart_data):
    """Test current metrics displayed in dashboard"""
    print("\n5. Testing Current Metrics Dashboard")

    current = chart_data['current']

    # Verify all required fields
    required_fields = [
        'composite_score', 'edr_percentile', 'esv_percentile',
        'ema20', 'ema50', 'close', 'adx', 'regime',
        'strong_momentum_entry', 'pullback_entry', 'exit_signal',
        'distance_to_ema20_pct'
    ]

    for field in required_fields:
        assert field in current, f"Missing required field: {field}"
    print(f"   ✓ All {len(required_fields)} required fields present")

    # Display current signal
    print(f"\n   CURRENT SIGNAL:")
    print(f"   - Composite Score: {current['composite_score']:.2f}%")
    print(f"   - Regime: {current['regime']} (ADX: {current['adx']:.1f})")

    if current['strong_momentum_entry']:
        print(f"   - Signal: STRONG MOMENTUM ENTRY ⬆️")
    elif current['pullback_entry']:
        print(f"   - Signal: PULLBACK ENTRY 🔵")
    elif current['exit_signal']:
        print(f"   - Signal: EXIT SIGNAL ⬇️")
    else:
        print(f"   - Signal: NEUTRAL")


def test_regime_detection(chart_data):
    """Test regime detection logic"""
    print("\n6. Testing Regime Detection")

    assert 'regime' in chart_data, "Missing regime data"
    assert 'adx' in chart_data, "Missing ADX data"

    regimes = chart_data['regime']
    adx_values = chart_data['adx']

    momentum_count = sum(1 for r in regimes if r == "Momentum")
    mean_rev_count = sum(1 for r in regimes if r == "Mean Reversion")

    print(f"   ✓ Total periods: {len(regimes)}")
    print(f"   ✓ Momentum periods: {momentum_count} ({momentum_count/len(regimes)*100:.1f}%)")
    print(f"   ✓ Mean Reversion periods: {mean_rev_count} ({mean_rev_count/len(regimes)*100:.1f}%)")
    print(f"   ✓ Average ADX: {sum(adx_values)/len(adx_values):.2f}")


def test_metadata(metadata):
    """Test metadata structure"""
    print("\n7. Testing Metadata")

    assert 'ema_period' in metadata, "Missing ema_period"
    assert 'ema_slope_period' in metadata, "Missing ema_slope_period"
    assert 'atr_period' in metadata, "Missing atr_period"
    assert 'edr_lookback' in metadata, "Missing edr_lookback"
    assert 'esv_lookback' in metadata, "Missing esv_lookback"

    print(f"   ✓ EMA Period: {metadata['ema_period']}")
    print(f"   ✓ EMA Slope Period: {metadata['ema_slope_period']}")
    print(f"   ✓ ATR Period: {metadata['atr_period']}")
    print(f"   ✓ EDR Lookback: {metadata['edr_lookback']} days")
    print(f"   ✓ ESV Lookback: {metadata['esv_lookback']} days")


def run_all_tests():
    """Run all tests"""
    try:
        # Test 1: Endpoint
        chart_data, metadata = test_mapi_endpoint()

        # Test 2: Composite tab
        test_composite_tab_data(chart_data)

        # Test 3: Components tab
        test_components_tab_data(chart_data)

        # Test 4: Price & EMAs tab
        test_price_ema_tab_data(chart_data)

        # Test 5: Current metrics
        test_current_metrics(chart_data)

        # Test 6: Regime detection
        test_regime_detection(chart_data)

        # Test 7: Metadata
        test_metadata(metadata)

        print("\n" + "=" * 60)
        print("✅ ALL TESTS PASSED - MAPI SUB-TABS FULLY FUNCTIONAL")
        print("=" * 60)
        return True

    except AssertionError as e:
        print(f"\n❌ TEST FAILED: {e}")
        return False
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
