# Next Task for Coding Agent

## Task Overview

**Task**: Make Multi-Timeframe Divergence Logic Compatible with Swing Framework/Duration  
**Priority**: HIGH  
**Estimated Effort**: 20–40 minutes  
**Category**: Multiple Timeframe Support (Feature F034)

## Objective

In the Swing Trading Framework tab, the Daily and 4-hour (4H) logic used in the **Framework** and **Duration** views is the trusted “source of truth”. Elsewhere (Multi-Timeframe Divergence), we also compare Daily vs 4H, but the underlying calculation has drifted and is not fully compatible with the framework/duration approach.

Update the multi-timeframe divergence calculation so Daily and 4H percentiles are computed using comparable lookback periods and the same indicator methodology, making “convergence vs divergence” insights actionable and consistent across the app.

## Scope (Single Feature Only)

- Keep the existing endpoint and response shape used by the UI: `GET /api/multi-timeframe/{ticker}`.
- Change only the **calculation inputs** (lookbacks/alignment) so Daily vs 4H is apples-to-apples.
- Do not redesign charts or add new UI flows.
- Do not modify `project_memory/feature_list.json`.

## Incremental Implementation Plan

1. **Confirm framework/duration “truth”**
   - Review `backend/swing_duration_intraday.py` (4H RSI‑MA and percentile window alignment) and `backend/swing_duration_analysis_v2.py` (daily RSI‑MA/percentiles).
   - Write down the intended Daily vs 4H lookback equivalence (e.g., 252 trading days ≈ 410 4H bars using 6.5 market hours/day).

2. **Align 4H percentile computation**
   - Update `backend/multi_timeframe_analyzer.py` so the 4H percentile rank is computed on true 4H bars using the aligned 4H window (not a daily-window applied after resampling).
   - Preserve the existing divergence sign convention used by the frontend (`current_divergence_pct` and `divergence_pct` fields).

3. **Keep output schema stable**
   - Ensure the analyzer still returns the same keys consumed by `frontend/src/components/MultiTimeframeDivergence.tsx`, including:
     - `current_daily_percentile`, `current_4h_percentile`, `current_divergence_pct`, `current_signal`, `current_recommendation`
     - `divergence_events[]` with `daily_percentile`, `hourly_4h_percentile`, `divergence_pct`, `divergence_type`, `signal_strength`, `forward_returns`
     - `divergence_stats`, `optimal_thresholds`

4. **Sanity-check actions for convergence/divergence**
   - Verify the four-category mapping remains coherent:
     - `4h_overextended` → take profits / reduce risk
     - `bullish_convergence` → buy/add/re-enter
     - `daily_overextended` → reduce/hedge
     - `bearish_convergence` → exit/avoid longs
   - Do not rename categories unless strictly required for compatibility.

5. **Add an offline regression test**
   - Add a small test that monkeypatches `yfinance.Ticker().history` to return deterministic synthetic daily + hourly data.
   - Assert the analysis runs without network access and returns non-null current percentiles once sufficient history exists.

## Testing Instructions

1. Run the new offline test: `pytest -q tests/unit/test_multi_timeframe_alignment.py` (or your exact filename).
2. Manual smoke (optional): start backend and load Multi-Timeframe Divergence for a ticker (e.g., GOOGL) and verify the Current Signal card populates and categories/actions look sensible.

## Success Criteria

- Daily vs 4H divergence values are now compatible with the Swing Framework/Duration interpretation (lookbacks aligned).
- The Multi-Timeframe Divergence UI continues to work without requiring schema changes.
- The offline regression test passes.

