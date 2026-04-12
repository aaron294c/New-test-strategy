# Telegram Message Formatting Reference

## Supported HTML Tags

Telegram HTML mode (`parse_mode="HTML"`) supports only:

| Tag | Purpose | Example |
|-----|---------|---------|
| `<b>` | Bold | `<b>Title</b>` |
| `<i>` | Italic | `<i>note</i>` |
| `<u>` | Underline | `<u>text</u>` |
| `<s>` | Strikethrough | `<s>old</s>` |
| `<code>` | Inline mono | `<code>value</code>` |
| `<pre>` | Monospace block | `<pre>table</pre>` |
| `<a href="...">` | Link | `<a href="...">click</a>` |

**Everything else is stripped or causes a parse error.** No `<span>`, `<div>`, `<br>`, `<h1>`, etc.

## Tables (the Right Way)

Always wrap fixed-width tables in `<pre>`:

```python
def format_table(rows: list[dict]) -> str:
    HDR = f"{'Ticker':<7} {'Pct':>6}  {'Signal':<12}  {'Δ':>6}"
    SEP = "─" * len(HDR)
    lines = ["<pre>", HDR, SEP]
    for r in rows:
        ticker = r.get("ticker", "")[:7]
        pct    = r.get("current_percentile")
        signal = r.get("signal", "")[:12]
        delta  = r.get("delta")
        pct_s  = f"{pct:.1f}%" if pct is not None else "  —  "
        dlt_s  = f"{delta:+.1f}pp" if delta is not None else "    —"
        lines.append(f"{ticker:<7} {pct_s:>6}  {signal:<12}  {dlt_s:>6}")
    lines.append("</pre>")
    return "\n".join(lines)
```

### Column width gotcha

Emoji characters are double-width in monospace fonts. Avoid emoji **inside** `<pre>` blocks — they destroy column alignment. Use ASCII indicators instead:

```python
# ✅ Good — ASCII zone chars inside <pre>
zone = "!" if pct <= 5 else "^" if pct >= 85 else " "
f"{ticker:<7} {pct:>5.1f}% {zone}"

# ❌ Bad — emoji breaks column alignment inside <pre>
f"{ticker:<7} {pct:>5.1f}% {'⚡' if pct <= 5 else ''}"
```

Use emoji **outside** `<pre>` (in headers, footers, plain text) where fixed-width alignment doesn't matter.

## Message Length Limit: 4096 Characters

Telegram rejects messages over 4096 chars with HTTP 400. Always use `split_and_send`.

```python
# ✅ Always
from telegram_bot import split_and_send
split_and_send(format_table(rows), chat_id=chat_id)

# ❌ Never for potentially-long output
from telegram_bot import send_message
send_message(format_table(rows), chat_id=chat_id)
```

`split_and_send` splits at newlines and handles `<pre>` blocks:
- Closes `</pre>` at end of each chunk that splits mid-block
- Opens `<pre>` at start of next chunk
- Result: each chunk has balanced HTML tags

## Formatter Module Structure

Keep formatters pure — they take data, return strings. No side effects:

```python
# telegram_formatters.py

def format_section_a(data: list[dict], extra: dict) -> str:
    """Returns an HTML string. Never calls send_message directly."""
    lines = [f"<b>Section A</b>  {_now_uk()}\n"]
    lines.append(format_table(data))
    return "\n".join(lines)

def get_help_message() -> str:
    return (
        "<b>Available Commands</b>\n\n"
        "  /update — Full snapshot\n"
        "  /macro  — Macro dashboard\n"
        "  /help   — This message\n"
    )
```

Then in `telegram_delivery.py`:

```python
from telegram_formatters import format_section_a
from telegram_bot import split_and_send

split_and_send(format_section_a(data, extra), chat_id=chat_id)
```

## Escaping Special Characters

In HTML mode, these characters in data values must be escaped:

| Char | Escape |
|------|--------|
| `&` | `&amp;` |
| `<` | `&lt;` |
| `>` | `&gt;` |

```python
def _escape(s: str) -> str:
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
```

This matters when ticker names, signals, or user-provided text could contain these chars.
Inside `<pre>` blocks, `<` and `>` in data are rare but still need escaping.

## Timestamp Helper

```python
from datetime import datetime, timezone

def _now_uk() -> str:
    return datetime.now(timezone.utc).strftime("%a %d %b %Y  %H:%M UTC")
```

## Typical Message Structure

```python
def format_full_snapshot(data, extra):
    parts = []

    # Header (plain text + bold, no pre)
    parts.append(f"<b>Market Snapshot</b>  {_now_uk()}\n")

    # Summary line
    parts.append(f"Watching <b>{len(data)}</b> instruments\n")

    # Table (pre block)
    parts.append("<pre>")
    parts.append(f"{'Ticker':<7} {'Pct':>6}  Signal")
    parts.append("─" * 28)
    for r in sorted(data, key=lambda x: x.get("current_percentile", 50)):
        parts.append(_row(r))
    parts.append("</pre>")

    # Footer
    parts.append(f"\n<i>Next update: scheduled or on /update</i>")

    return "\n".join(parts)
```
