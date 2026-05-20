"""
Shared snapshot delivery logic used by both the webhook handler and the poller.

_deliver(chat_id, msg_type)  — fetches live data and sends snapshot(s).

msg_type: "all" | "macro" | "mr" | "momentum" | "divergence" | "cov"
          | "covgreen" | "sma200" | "gammawalls" | "maxpain"
          | "kelly_hist" | "kelly_dyn" | "kelly_strategy"
"""

from __future__ import annotations

import sys
from pathlib import Path

# Allow importing backend modules when called from scripts/
_here = Path(__file__).resolve().parent
if str(_here) not in sys.path:
    sys.path.insert(0, str(_here))


def _deliver(chat_id: str, msg_type: str = "all") -> None:
    """Fetch live data and send Telegram snapshot(s) to chat_id."""
    from macro_rsi_calculator import (
        fetch_all_macro_data,
        compute_live_swing_percentiles,
        compute_live_full_rows,
    )
    from telegram_formatters import (
        _load_swing_snapshot,
        _enrich_second_order,
        format_macro_dashboard,
        format_mean_reversion,
        format_momentum,
        format_divergence,
        format_cov_snapshot,
        format_cov_green_snapshot,
        format_sma200_snapshot,
        format_gamma_walls,
        format_max_pain,
    )
    from telegram_bot import split_and_send

    print(f"[delivery] type={msg_type}  chat={chat_id}")

    # Only fetch macro data when it's actually needed
    needs_macro = msg_type in ("all", "macro", "mr", "momentum")
    macro_data = fetch_all_macro_data() if needs_macro else {}

    swing_data = list(_load_swing_snapshot() or [])

    needs_live = msg_type in ("all", "mr", "momentum", "divergence", "cov", "covgreen")
    if needs_live and swing_data is not None:
        # Inject live rows for tickers in the universe but absent from the snapshot
        from macdv_calculator import SWING_FRAMEWORK_TICKERS
        snapshot_tickers = {row.get("ticker") for row in swing_data}
        new_tickers = [t for t in SWING_FRAMEWORK_TICKERS if t not in snapshot_tickers]
        if new_tickers:
            print(f"[delivery] computing live rows for new tickers: {new_tickers}")
            new_rows = compute_live_full_rows(new_tickers)
            swing_data.extend(new_rows)

        # Overlay snapshot rows with live RSI-MA / CoV from yfinance
        live = compute_live_swing_percentiles(swing_data)
        for row in swing_data:
            ld = live.get(row.get("ticker", ""), {})
            if ld.get("current_percentile") is not None:
                row["current_percentile"] = ld["current_percentile"]
            if ld.get("price") is not None:
                row["current_price"]    = ld["price"]
                row["price_change_pct"] = ld.get("price_chg_pct")
            if ld.get("rsi_ma") is not None:
                row["rsi_ma"] = ld["rsi_ma"]
            if ld.get("cov_dir_metric") is not None:
                row["cov_dir_metric"] = ld["cov_dir_metric"]
            if ld.get("cov_bar_color") is not None:
                row["cov_bar_color"] = ld["cov_bar_color"]
        # Re-enrich second-order after live percentile update
        _enrich_second_order(swing_data)

    # ── For divergence: fill in four_h_percentile live for any ticker missing it
    if msg_type in ("divergence", "all"):
        missing_4h = [
            r["ticker"] for r in swing_data
            if r.get("current_percentile") is not None
            and r.get("four_h_percentile") is None
            and r.get("ticker")
        ]
        if missing_4h:
            print(f"[delivery] computing live 4H pct for {len(missing_4h)} tickers: {missing_4h}")
            try:
                from rsima_cov_4h_live import compute_live_4h_percentiles
                h4_pcts = compute_live_4h_percentiles(missing_4h)
                ticker_map = {r["ticker"]: r for r in swing_data}
                # Default first-order divergence thresholds for tickers not in snapshot
                _DEFAULT_P85 = 20.0
                _DEFAULT_P95 = 30.0
                for ticker, h4_pct in h4_pcts.items():
                    if h4_pct is None:
                        continue
                    row = ticker_map.get(ticker)
                    if row is None:
                        continue
                    daily_pct = row.get("current_percentile")
                    row["four_h_percentile"]  = h4_pct
                    if daily_pct is not None:
                        div = float(daily_pct) - float(h4_pct)
                        row["divergence_pct"]     = div
                        row["abs_divergence_pct"] = abs(div)
                        ad = abs(div)
                        p85 = row.get("p85_threshold") or _DEFAULT_P85
                        p95 = row.get("p95_threshold") or _DEFAULT_P95
                        row.setdefault("p85_threshold", p85)
                        row.setdefault("p95_threshold", p95)
                        if ad <= p85:
                            row["dislocation_level"] = "Normal"
                            row["dislocation_color"] = "⚪"
                        elif ad <= p95:
                            row["dislocation_level"] = "Significant (P85)"
                            row["dislocation_color"] = "⚠️"
                        else:
                            row["dislocation_level"] = "Extreme (P95)"
                            row["dislocation_color"] = "⚡"
            except Exception as exc:
                print(f"[delivery] live 4H pct error: {exc}")

    if msg_type in ("all", "macro"):
        split_and_send(format_macro_dashboard(macro_data), chat_id=chat_id)

    if msg_type in ("all", "mr"):
        split_and_send(format_mean_reversion(swing_data, macro_data), chat_id=chat_id)

    if msg_type in ("all", "momentum"):
        split_and_send(format_momentum(swing_data, macro_data), chat_id=chat_id)

    if msg_type in ("all", "cov"):
        split_and_send(format_cov_snapshot(swing_data), chat_id=chat_id)

    if msg_type == "all":
        try:
            from telegram_options_handler import handle_optwatch_brief
            split_and_send(handle_optwatch_brief(), chat_id=chat_id)
        except Exception as exc:
            print(f"[delivery] optwatch brief error: {exc}")

    if msg_type == "divergence":
        split_and_send(format_divergence(swing_data, macro_data), chat_id=chat_id)

    if msg_type == "covgreen":
        split_and_send(format_cov_green_snapshot(swing_data), chat_id=chat_id)

    if msg_type == "sma200":
        from macdv_calculator import SWING_FRAMEWORK_TICKERS
        split_and_send(format_sma200_snapshot(SWING_FRAMEWORK_TICKERS), chat_id=chat_id)

    if msg_type == "gammawalls":
        split_and_send(format_gamma_walls(), chat_id=chat_id)

    if msg_type == "maxpain":
        split_and_send(format_max_pain(), chat_id=chat_id)

    if msg_type in ("kelly_hist", "kelly_dyn", "kelly_strategy"):
        from macdv_calculator import SWING_FRAMEWORK_TICKERS
        from kelly_analyzer import (
            historical_kelly, dynamic_kelly, strategy_kelly,
            format_historical_kelly, format_dynamic_kelly,
            format_percentile_kelly, format_strategy_kelly,
        )
        if msg_type == "kelly_hist":
            split_and_send(
                format_historical_kelly(historical_kelly(SWING_FRAMEWORK_TICKERS, lookback=2000),
                                        title="Historical (2000-day)"),
                chat_id=chat_id,
            )
        elif msg_type == "kelly_dyn":
            res = dynamic_kelly(SWING_FRAMEWORK_TICKERS, lookback=252)
            split_and_send(format_dynamic_kelly(res), chat_id=chat_id)
            split_and_send(format_percentile_kelly(res), chat_id=chat_id)
        elif msg_type == "kelly_strategy":
            split_and_send(
                format_strategy_kelly(strategy_kelly(SWING_FRAMEWORK_TICKERS, horizon=5),
                                      horizon=5),
                chat_id=chat_id,
            )

    if msg_type == "rsima4h":
        from telegram_formatters import format_4h_rsima
        split_and_send(format_4h_rsima(), chat_id=chat_id)

    if msg_type == "cov4h":
        from telegram_formatters import format_4h_cov
        split_and_send(format_4h_cov(), chat_id=chat_id)

    print("[delivery] done.")
