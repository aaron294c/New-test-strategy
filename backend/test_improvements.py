#!/usr/bin/env python3
"""
Quick test of the three improvements:
1. Extended horizons (3, 7, 14, 21)
2. Confidence assessment
3. Percentile-first prediction
"""

import numpy as np
import pandas as pd
from percentile_forward_mapping import (
    PercentileForwardMapper,
    PercentileBinStats,
    PercentileFirstForecast,
    ConfidenceAssessment
)

print("="*80)
print("TESTING IMPROVEMENTS")
print("="*80)

# Test 1: Horizons
print("\n1. Testing Extended Horizons...")
mapper = PercentileForwardMapper()
print(f"   Default horizons: {mapper.horizons}")
assert mapper.horizons == [3, 7, 14, 21], "Horizons should be [3, 7, 14, 21]"
print("   ✅ PASS: Horizons extended")

# Test 2: Confidence Assessment
print("\n2. Testing Confidence Assessment...")

# Create mock bin stats with NEW horizons (3, 7, 14, 21)
mock_bin_stats = PercentileBinStats(
    bin_label="25-50",
    bin_min=25,
    bin_max=50,
    count=100,
    mean_return_3d=0.5,
    mean_return_7d=1.5,
    mean_return_14d=3.0,
    mean_return_21d=4.5,
    median_return_3d=0.4,
    median_return_7d=1.2,
    median_return_14d=2.5,
    median_return_21d=3.8,
    std_return_3d=1.5,
    std_return_7d=3.0,
    std_return_14d=5.0,
    std_return_21d=7.0,
    downside_risk_3d=1.2,
    upside_potential_3d=1.8,
    pct_5_return_3d=-2.5,
    pct_95_return_3d=3.5
)

# Test HIGH confidence (oversold + bullish)
confidence_high = mapper.assess_confidence(
    current_percentile=20.0,  # Oversold
    ensemble_forecast=0.8,     # Bullish
    horizon=7,
    bin_stats=mock_bin_stats,
    current_atr_percentile=50.0  # Normal volatility
)

print(f"   Scenario: Oversold (20%ile) + Bullish forecast (+0.8%)")
print(f"   Confidence: {confidence_high.overall_confidence}")
print(f"   Score: {confidence_high.confidence_score:.1f}/100")
print(f"   Action: {confidence_high.recommended_action}")
print(f"   Position Size: {confidence_high.position_size_pct:.0f}%")
print(f"   Reasoning: {confidence_high.reasoning[:80]}...")

assert confidence_high.overall_confidence == "HIGH", "Should be HIGH confidence"
assert confidence_high.directional_agreement == True, "Should have directional agreement"
print("   ✅ PASS: HIGH confidence scenario works")

# Test MEDIUM confidence (neutral position + moderate volatility)
confidence_medium = mapper.assess_confidence(
    current_percentile=50.0,
    ensemble_forecast=0.1,      # Weak forecast
    horizon=7,
    bin_stats=mock_bin_stats,
    current_atr_percentile=85.0  # Extreme volatility
)

print(f"\n   Scenario: Neutral (50%ile) + Weak forecast (+0.1%) + Extreme Vol")
print(f"   Confidence: {confidence_medium.overall_confidence}")
print(f"   Score: {confidence_medium.confidence_score:.1f}/100")
print(f"   Action: {confidence_medium.recommended_action}")

assert confidence_medium.overall_confidence == "MEDIUM", "Should be MEDIUM confidence"
assert confidence_medium.recommended_action == "CAUTIOUS", "Should recommend CAUTIOUS"
print("   ✅ PASS: MEDIUM confidence scenario works")

# Test LOW confidence (no directional agreement + weak forecast)
confidence_low = mapper.assess_confidence(
    current_percentile=20.0,     # Oversold
    ensemble_forecast=-0.2,      # Bearish forecast (conflicts!)
    horizon=7,
    bin_stats=mock_bin_stats,
    current_atr_percentile=85.0  # Extreme volatility
)

print(f"\n   Scenario: Oversold (20%ile) + Bearish forecast (-0.2%) + Extreme Vol")
print(f"   Confidence: {confidence_low.overall_confidence}")
print(f"   Score: {confidence_low.confidence_score:.1f}/100")
print(f"   Action: {confidence_low.recommended_action}")
print(f"   Reasoning: {confidence_low.reasoning[:80]}...")

assert confidence_low.overall_confidence == "LOW", "Should be LOW confidence"
assert confidence_low.recommended_action == "AVOID", "Should recommend AVOID"
assert confidence_low.directional_agreement == False, "Should have no directional agreement"
print("   ✅ PASS: LOW confidence scenario works")

# Test 3: Percentile-First Prediction
print("\n3. Testing Percentile-First Prediction...")

# Build minimal dataset for testing
dates = pd.date_range('2023-01-01', periods=300, freq='D')
np.random.seed(42)

df = pd.DataFrame({
    'date': dates[:250],
    'percentile': np.random.uniform(0, 100, 250),
    'rsi_ma': np.random.uniform(30, 70, 250),
    'bin': [mapper.assign_bin(p) for p in np.random.uniform(0, 100, 250)],
    'price': 100 + np.cumsum(np.random.randn(250) * 2),
})

# Add forward returns for ALL horizons (including old ones for compatibility)
for h in [1, 3, 5, 7, 10, 14, 21]:
    df[f'ret_{h}d'] = np.random.randn(250) * 2 + 0.5  # Mean +0.5%
    df[f'pct_next_{h}d'] = np.random.uniform(0, 100, 250)

# Calculate bin stats and transition matrix
mapper.calculate_empirical_bin_stats(df)
mapper.build_transition_matrix(df, horizon=7)

# Test percentile-first forecast
current_bin = 3  # 25-50 bin
current_percentile = 40.0

pf_forecast = mapper.percentile_first_forecast(
    current_bin=current_bin,
    current_percentile=current_percentile,
    horizon=7
)

print(f"   Current percentile: {current_percentile:.1f}%ile")
print(f"   Predicted future percentile (7d): {pf_forecast.predicted_percentile:.1f}%ile")
print(f"   Percentile confidence: {pf_forecast.percentile_confidence:.1f}%")
print(f"   Expected return from future pct: {pf_forecast.expected_return_from_future_pct:+.2f}%")
print(f"   Direct prediction: {pf_forecast.direct_prediction:+.2f}%")
print(f"   Percentile-first advantage: {pf_forecast.percentile_first_advantage:+.2f}%")
print(f"   Risk bounds: [{pf_forecast.downside_5th:+.2f}%, {pf_forecast.upside_95th:+.2f}%]")

assert isinstance(pf_forecast.predicted_percentile, float), "Should return float"
assert 0 <= pf_forecast.predicted_percentile <= 100, "Percentile should be 0-100"
assert 0 <= pf_forecast.percentile_confidence <= 100, "Confidence should be 0-100"
print("   ✅ PASS: Percentile-first prediction works")

print("\n" + "="*80)
print("ALL TESTS PASSED ✅")
print("="*80)
print("\nSUMMARY:")
print("✅ Horizons extended to 3, 7, 14, 21 days")
print("✅ Confidence assessment with 4 factors working")
print("✅ Percentile-first prediction functional")
print("\nReady for production use!")
