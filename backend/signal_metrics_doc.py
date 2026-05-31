"""
Reader for docs/SIGNAL_METRICS_REFERENCE.md — single source of truth for the
backtest reference tables surfaced by /mr and /sortino.

Parses the markdown into (heading-path, table) records so handlers can pick the
exact table they want (e.g. "Signal A" + "Sortino-like") and render a compact,
mobile-friendly <pre> view of a chosen subset of columns.
"""

from __future__ import annotations

import re
from pathlib import Path

_MD_FILE = Path(__file__).resolve().parent.parent / "docs" / "SIGNAL_METRICS_REFERENCE.md"

_PIPE = "§"   # placeholder for escaped pipes inside cells


def _clean(s: str) -> str:
    return s.replace("**", "").replace("`", "").replace(_PIPE, "|").strip()


def _doc_lines() -> list[str]:
    if not _MD_FILE.exists():
        return []
    return _MD_FILE.read_text(encoding="utf-8").splitlines()


def _split_row(line: str) -> list[str]:
    body = line.strip().replace("\\|", _PIPE)
    body = body.strip("|")
    return [_clean(c) for c in body.split("|")]


def iter_tables() -> list[dict]:
    """
    Returns a list of {"headings": {level:int -> text}, "cols": [...], "rows": [[...]]}.
    headings holds the active heading at each level when the table was encountered.
    """
    lines = _doc_lines()
    headings: dict[int, str] = {}
    out: list[dict] = []
    i = 0
    n = len(lines)
    while i < n:
        line = lines[i]
        m = re.match(r"^(#{1,6})\s+(.*)$", line)
        if m:
            lvl = len(m.group(1))
            headings[lvl] = _clean(m.group(2))
            for d in [d for d in headings if d > lvl]:
                del headings[d]
            i += 1
            continue

        if line.lstrip().startswith("|"):
            block = []
            while i < n and lines[i].lstrip().startswith("|"):
                block.append(lines[i])
                i += 1
            if len(block) >= 2:
                cols = _split_row(block[0])
                rows = []
                for r in block[2:]:               # skip header + divider
                    cells = _split_row(r)
                    if len(cells) == len(cols):
                        rows.append(cells)
                if rows:
                    out.append({"headings": dict(headings), "cols": cols, "rows": rows})
            continue
        i += 1
    return out


def find_table(*needles: str, deepest: str | None = None) -> dict | None:
    """
    First table whose heading-path contains every `needle` (case-insensitive).
    If `deepest` is given, the table's lowest-level heading must contain it.
    """
    needles_l = [s.lower() for s in needles]
    for t in iter_tables():
        joined = " | ".join(t["headings"].values()).lower()
        if not all(s in joined for s in needles_l):
            continue
        if deepest is not None:
            low = t["headings"][max(t["headings"])].lower()
            if deepest.lower() not in low:
                continue
        return t
    return None


def render(
    table: dict | None,
    select: list[str],
    *,
    title: str = "",
    max_rows: int | None = None,
    rename: dict | None = None,
    note: str = "",
) -> str:
    """Render selected columns of a parsed table as an aligned Telegram <pre> block."""
    if not table:
        return f"{title}<i>Table not found in reference doc.</i>"
    rename = rename or {}
    col_idx = {c: i for i, c in enumerate(table["cols"])}
    sel = [(rename.get(c, c), col_idx[c]) for c in select if c in col_idx]
    if not sel:
        return f"{title}<i>No matching columns ({', '.join(select)}).</i>"

    headers = [h for h, _ in sel]
    rows = table["rows"][:max_rows] if max_rows else table["rows"]
    data = [[r[i] for _, i in sel] for r in rows]

    widths = [
        max(len(headers[j]), *(len(d[j]) for d in data)) if data else len(headers[j])
        for j in range(len(headers))
    ]

    def fmt(cells):
        # first column left-aligned (ticker), the rest right-aligned (numbers)
        parts = [cells[0].ljust(widths[0])]
        parts += [cells[j].rjust(widths[j]) for j in range(1, len(cells))]
        return "  ".join(parts)

    head = fmt(headers)
    divider = "-" * len(head)
    body = "\n".join(fmt(d) for d in data)
    block = f"{title}<pre>{head}\n{divider}\n{body}</pre>"
    if note:
        block += f"\n{note}"
    return block
