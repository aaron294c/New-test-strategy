#!/usr/bin/env python3

import argparse
import asyncio
import json
import os
import sys
from pathlib import Path


async def _compute() -> dict:
    repo_root = Path(__file__).resolve().parents[1]
    backend_dir = repo_root / "backend"
    sys.path.insert(0, str(backend_dir))

    os.environ["SWING_STATIC_SNAPSHOTS"] = "0"

    import swing_framework_api  # noqa: E402

    current_state = await swing_framework_api.get_current_market_state(force_refresh=True)
    current_state_4h = await swing_framework_api.get_current_market_state_4h(force_refresh=True)
    current_state_enriched = await swing_framework_api.get_current_market_state_enriched(force_refresh=False)

    return {
        "current_state": current_state,
        "current_state_4h": current_state_4h,
        "current_state_enriched": current_state_enriched,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Compute Swing Framework snapshot JSON files.")
    parser.add_argument(
        "--out-dir",
        default=None,
        help="Output directory (defaults to backend/static_snapshots/swing_framework).",
    )
    parser.add_argument("--pretty", action="store_true", help="Pretty-print JSON output.")
    args = parser.parse_args()

    repo_root = Path(__file__).resolve().parents[1]
    default_out_dir = repo_root / "backend" / "static_snapshots" / "swing_framework"
    out_dir = Path(args.out_dir) if args.out_dir else default_out_dir
    out_dir.mkdir(parents=True, exist_ok=True)

    payloads = asyncio.run(_compute())

    indent = 2 if args.pretty else None
    for filename, key in [
        ("current-state.json", "current_state"),
        ("current-state-4h.json", "current_state_4h"),
        ("current-state-enriched.json", "current_state_enriched"),
    ]:
        path = out_dir / filename
        with path.open("w", encoding="utf-8") as file:
            json.dump(payloads[key], file, indent=indent)
            file.write("\n")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())

