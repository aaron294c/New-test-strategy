#!/usr/bin/env python3

import argparse
import json
import sys
from pathlib import Path
from datetime import datetime, timezone


def _write_json(path: Path, payload: dict, pretty: bool) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    indent = 2 if pretty else None
    with path.open("w", encoding="utf-8") as file:
        json.dump(payload, file, indent=indent)
        file.write("\n")


def main() -> int:
    parser = argparse.ArgumentParser(description="Compute Multi-Timeframe snapshot JSON files.")
    parser.add_argument(
        "--tickers",
        nargs="+",
        default=["AAPL", "MSFT", "NVDA", "GOOGL"],
        help="Tickers to compute (default: AAPL MSFT NVDA GOOGL).",
    )
    parser.add_argument(
        "--out-dir",
        default=None,
        help="Output directory (defaults to backend/static_snapshots/multi_timeframe).",
    )
    parser.add_argument("--pretty", action="store_true", help="Pretty-print JSON output.")
    parser.add_argument(
        "--include-enhanced",
        action="store_true",
        help="Also compute enhanced MTF snapshots (/api/enhanced-mtf/*).",
    )
    args = parser.parse_args()

    repo_root = Path(__file__).resolve().parents[1]
    backend_dir = repo_root / "backend"
    sys.path.insert(0, str(backend_dir))

    from multi_timeframe_analyzer import run_multi_timeframe_analysis  # noqa: E402
    from enhanced_mtf_analyzer import run_enhanced_analysis  # noqa: E402

    default_out_dir = backend_dir / "static_snapshots" / "multi_timeframe"
    out_dir = Path(args.out_dir) if args.out_dir else default_out_dir

    now = datetime.now(timezone.utc).isoformat()

    for ticker in args.tickers:
        ticker = ticker.upper()
        slug = "".join(ch if ch.isalnum() or ch in {"-", "_", "."} else "_" for ch in ticker)

        analysis = run_multi_timeframe_analysis(ticker)
        payload = {"ticker": ticker, "analysis": analysis, "timestamp": now}
        _write_json(out_dir / f"multi-timeframe-{slug}.json", payload, pretty=args.pretty)

        if args.include_enhanced:
            enhanced = run_enhanced_analysis(ticker)
            payload = {"ticker": ticker, "enhanced_analysis": enhanced, "timestamp": now}
            _write_json(out_dir / f"enhanced-mtf-{slug}.json", payload, pretty=args.pretty)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())

