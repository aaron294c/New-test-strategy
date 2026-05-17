"""
Telegram variance / downside-deviation reference.

/variants           → method intro + all batches (5 messages)
/variants 1         → Batches 1 & 2  (EV ≥ 2.0%)
/variants 2         → Batch 3        (EV 1.5–1.99%)
/variants 3         → Batch 4        (EV 1.0–1.49%)
/variants 4         → Batch 5 + binding summary

/sizing var         → Signal A + B EV/downside ranked tables
/sizing vara        → Signal A variance table only
/sizing varb        → Signal B variance table only
"""

from __future__ import annotations

# ─── Static data ──────────────────────────────────────────────────────────────
#
# Tail code: L = low (Avg Loss ≤ 2.5%)
#            M = moderate (2.5–3.9%)
#            H = fat (≥ 4.0%)
#
# Batch tuples:
#   (ticker, sig, ev, avg_loss, tail, sigma_down, pct95, max2pct, half_kelly, action)
# All values are strings; percentages without % symbol (implied by column header).
# max2pct = max position size derived from 2% portfolio loss budget.

_BATCH1: list[tuple] = [
    ('TSLA',     'A', '+4.31', '-3.50', 'M', '2.28', ' 7.26', '  20', '20', 'Full ½K'),
]

_BATCH2: list[tuple] = [
    ('SK Hynix', 'B', '+2.47', '-4.17', 'H', '3.54', '10.01', '  20', '20', 'At limit'),
    ('MU',       'B', '+2.39', '-4.47', 'H', '3.80', '10.74', '18.6', '17', '½K=17'),
    ('AMD',      'B', '+2.20', '-4.57', 'H', '3.88', '10.98', '18.2', '18', 'OK'),
    ('LLY',      'B', '+2.07', '-3.80', 'M', '2.47', ' 7.88', '  20', '20', 'Full ½K'),
]

_BATCH3: list[tuple] = [
    ('^TNX',     'A', '+1.93', '-4.80', 'H', '4.08', '11.53', '17.3', '18', '! USE 17%'),
    ('AVGO',     'B', '+1.74', '-2.90', 'M', '1.89', ' 6.02', '  20', '19', 'Full ½K'),
    ('TSLA',     'B', '+1.72', '-3.80', 'M', '2.47', ' 7.88', '  20', '13', 'Full ½K'),
    ('META',     'A', '+1.72', '-5.10', 'H', '4.34', '12.26', '16.3', '17', '! USE 16%'),
    ('BTC',      'A', '+1.69', '-5.50', 'H', '4.68', '13.22', '15.1', '16', '! USE 15%'),
    ('MSFT',     'A', '+1.68', '-3.10', 'M', '2.02', ' 6.43', '  20', '20', 'Full ½K'),
]

_BATCH4: list[tuple] = [
    ('Samsung',  'A', '+1.45', '-2.76', 'M', '1.79', ' 5.72', '  20', '18', 'Full ½K'),
    ('V',        'A', '+1.35', '-2.50', 'L', '1.25', ' 4.56', '  20', '20', 'Full ½K'),
    ('NVDA',     'A', '+1.33', '-3.50', 'M', '2.28', ' 7.26', '  20', '14', 'Full ½K'),
    ('NQ=F',     'A', '+1.32', '-2.30', 'L', '1.15', ' 4.20', '  20', '20', 'Full ½K'),
    ('TSM',      'A', '+1.13', '-3.50', 'M', '2.28', ' 7.26', '  20', '14', 'Full ½K'),
    ('PG',       'A', '+1.10', '-1.38', 'L', '0.69', ' 2.52', '  20', '20', 'Full ½K'),
    ('GOOGL',    'A', '+1.08', '-2.70', 'M', '1.76', ' 5.60', '  20', '15', 'Full ½K'),
    ('SMH',      'A', '+1.06', '-3.20', 'M', '2.08', ' 6.63', '  20', '11', 'Full ½K'),
    ('CSCO',     'B', '+1.06', '-2.20', 'L', '1.10', ' 4.02', '  20', '17', 'Full ½K'),
    ('NFLX',     'B', '+1.01', '-4.00', 'H', '3.40', ' 9.61', '  20', '12', 'Full ½K'),
]

# Batch 5: EV 0.5–0.99% — sorted by EV desc; ½K is operative limit throughout.
# Tuple: (ticker, sig, ev, avg_loss, tail, sigma_down, pct95, max2pct, half_kelly)
_BATCH5: list[tuple] = [
    ('WMT',    'A', '+0.95', '-1.80', 'L', '0.90', '3.29', '20', '15'),
    ('CNX1.L', 'A', '+0.95', '-1.81', 'L', '0.91', '3.31', '20', '19'),
    ('COST',   'B', '+0.93', '-2.49', 'L', '1.25', '4.55', '20', '17'),
    ('MSFT',   'B', '+0.93', '-2.20', 'L', '1.10', '4.02', '20', '14'),
    ('AVGO',   'A', '+0.89', '-3.20', 'M', '2.08', '6.63', '20', ' 9'),
    ('ES=F',   'A', '+0.85', '-1.90', 'L', '0.95', '3.47', '20', '20'),
    ('^N225',  'A', '+0.79', '-3.00', 'M', '1.95', '6.22', '20', '12'),
    ('AAPL',   'A', '+0.75', '-2.20', 'L', '1.10', '4.02', '20', '11'),
    ('UNH',    'A', '+0.70', '-2.80', 'M', '1.82', '5.79', '20', '11'),
    ('CAT',    'B', '+0.69', '-3.07', 'M', '2.00', '6.37', '20', '10'),
    ('MCD',    'B', '+0.68', '-2.40', 'L', '1.20', '4.38', '20', '14'),
    ('QQQ',    'A', '+0.66', '-2.40', 'L', '1.20', '4.38', '20', '16'),
    ('SMCI',   'A', '+0.65', '-6.50', 'H', '5.53', '15.62', '12.8', ' 5'),
    ('JNJ',    'A', '+0.65', '-2.08', 'L', '1.04', '3.80', '20', '14'),
    ('ASML',   'A', '+0.62', '-3.60', 'M', '2.34', '7.46', '20', ' 7'),
    ('V',      'B', '+0.59', '-2.30', 'L', '1.15', '4.20', '20', '14'),
    ('XLI',    'A', '+0.58', '-3.20', 'M', '2.08', '6.63', '20', '12'),
    ('TSM',    'B', '+0.58', '-3.60', 'M', '2.34', '7.46', '20', ' 9'),
    ('AAPL',   'B', '+0.56', '-3.70', 'M', '2.41', '7.67', '20', ' 7'),
    ('ORCL',   'A', '+0.56', '-2.60', 'M', '1.69', '5.39', '20', ' 8'),
    ('PG',     'B', '+0.52', '-1.72', 'L', '0.86', '3.14', '20', '12'),
]

# Variance-ranked tables: (rank, ticker, ev, avg_loss, dwn_wt, wl_ratio, ev_downside, tail)
# EV/Downside = EV ÷ Downside Weight (higher = better risk-adjusted quality)
# DwnWt = (1 − Win%) × |Avg Loss|  ← expected loss per trade

_VAR_A: list[tuple] = [
    ( 1, 'TSLA',    '+4.31%', '-3.5%',  '1.00', '2.11', '4.30', 'M'),
    ( 2, 'PG',      '+1.10%', '-1.38%', '0.47', '1.73', '2.35', 'L'),
    ( 3, 'NQ=F',    '+1.32%', '-2.3%',  '0.60', '1.13', '2.21', 'L'),
    ( 4, 'MSFT',    '+1.68%', '-3.1%',  '0.84', '1.13', '2.00', 'M'),
    ( 5, 'V',       '+1.35%', '-2.5%',  '0.72', '1.16', '1.88', 'L'),
    ( 6, 'ES=F',    '+0.85%', '-1.9%',  '0.57', '1.05', '1.49', 'L'),
    ( 7, 'CNX1.L',  '+0.95%', '-1.81%', '0.65', '1.38', '1.46', 'L'),
    ( 8, 'Samsung', '+1.45%', '-2.76%', '1.05', '1.47', '1.38', 'M'),
    ( 9, '^TNX',    '+1.93%', '-4.8%',  '1.60', '1.10', '1.20', 'H'),
    (10, 'META',    '+1.72%', '-5.1%',  '1.65', '0.98', '1.04', 'H'),
    (11, 'BTC',     '+1.69%', '-5.5%',  '1.83', '0.96', '0.92', 'H'),
    (12, 'NVDA',    '+1.33%', '-3.5%',  '1.48', '1.40', '0.89', 'M'),
    (13, 'AVGO',    '+0.89%', '-3.2%',  '1.55', '1.50', '0.57', 'M'),
]

_VAR_B: list[tuple] = [
    (1, 'SK Hynix', '+2.47%', '-4.17%', '1.33', '1.34', '1.87', 'H'),
    (2, 'LLY',      '+2.07%', '-3.8%',  '1.21', '1.26', '1.71', 'M'),
    (3, 'META',     '+1.60%', '-2.1%',  '0.99', '2.33', '1.63', 'L'),
    (4, 'AVGO',     '+1.74%', '-2.9%',  '1.10', '1.55', '1.58', 'M'),
    (5, 'AMD',      '+2.20%', '-4.57%', '1.68', '1.34', '1.31', 'H'),
    (6, 'MU',       '+2.39%', '-4.47%', '1.84', '1.61', '1.30', 'H'),
    (7, 'CSCO',     '+1.06%', '-2.2%',  '0.83', '1.38', '1.27', 'L'),
    (8, 'COST',     '+0.93%', '-2.49%', '0.87', '1.12', '1.07', 'L'),
    (9, 'TSLA',     '+1.72%', '-3.8%',  '1.79', '1.76', '0.96', 'M'),
]


# ─── Table formatters ─────────────────────────────────────────────────────────

def _fmt_batch(rows: list[tuple], with_action: bool = True) -> str:
    """Monospace pre-block table for batch rows."""
    if with_action:
        hdr = (
            f"{'Ticker':<10}  S {'EV':>5} {'Loss':>6}  T"
            f"  {'σdn':>4} {'95th':>6} {'M2%':>5} {'½K':>3}  Action"
        )
        div = '─' * 59
        lines = [hdr, div]
        for t, s, ev, lo, tail, sd, p95, m2, hk, act in rows:
            lines.append(
                f"{t:<10}  {s} {ev:>5} {lo:>6}  {tail}"
                f"  {sd:>4} {p95:>6} {m2:>5} {hk:>3}  {act}"
            )
    else:
        hdr = (
            f"{'Ticker':<10}  S {'EV':>5} {'Loss':>6}  T"
            f"  {'σdn':>4} {'95th':>6} {'M2%':>5} {'½K':>3}"
        )
        div = '─' * 49
        lines = [hdr, div]
        for t, s, ev, lo, tail, sd, p95, m2, hk in rows:
            lines.append(
                f"{t:<10}  {s} {ev:>5} {lo:>6}  {tail}"
                f"  {sd:>4} {p95:>6} {m2:>5} {hk:>3}"
            )
    return '\n'.join(lines)


def _fmt_var(rows: list[tuple]) -> str:
    """Monospace pre-block table for variance-ranked rows."""
    hdr = (
        f"{'Rk':>2} {'Ticker':<9} {'9yEV':>6} {'Loss':>6}"
        f" {'DwnWt':>5} {'W/L':>4} {'EV/Dn':>5} T"
    )
    div = '─' * len(hdr)
    lines = [hdr, div]
    for rank, ticker, ev, loss, dwn_wt, wl, ev_dn, tail in rows:
        lines.append(
            f"{rank:>2} {ticker:<9} {ev:>6} {loss:>6}"
            f" {dwn_wt:>5} {wl:>4} {ev_dn:>5} {tail}"
        )
    return '\n'.join(lines)


# ─── Message builders — /variants ────────────────────────────────────────────

def msg_intro() -> str:
    return (
        "<b>📉 DOWNSIDE DEVIATION — EV-RANKED BATCHES</b>\n"
        "<i>9yr window · D5 hold · CoV red bar confluence · all signals</i>\n"
        "\n"
        "<b>Method — deriving σ_down and 95th-pct adverse move:</b>\n"
        "<pre>"
        "σ_down  = |Avg Loss| × k\n"
        "  L tail (Avg Loss ≤ 2.5%)   k = 0.50\n"
        "  M tail (Avg Loss 2.5–3.9%) k = 0.65\n"
        "  H tail (Avg Loss ≥ 4.0%)   k = 0.85\n"
        "\n"
        "95th-pct = |Avg Loss| + 1.65 × σ_down\n"
        "           one-in-20 losing trade estimate\n"
        "\n"
        "Max (2%) = 2% portfolio budget ÷ 95th-pct loss\n"
        "Cap = 20% in all cases"
        "</pre>\n"
        "\n"
        "<b>Column key:</b>\n"
        "<pre>"
        "σdn   est. downside semi-deviation\n"
        "95th  one-in-20 adverse move\n"
        "M2%   max size at 2% loss budget\n"
        "½K    half-Kelly (cap 20%)\n"
        "! USE X%  variance overrides ½K — use X%\n"
        "½K=N      ½K already more conservative\n"
        "At limit  exactly at 2% budget boundary"
        "</pre>"
    )


def msg_batches_1_2() -> str:
    b1 = _fmt_batch(_BATCH1)
    b2 = _fmt_batch(_BATCH2)
    return (
        "<b>▸ BATCH 1 — EV ≥ 3.0%</b>\n"
        f"<pre>{b1}</pre>\n"
        "<i>EV/Downside = 4.30 — highest in universe.\n"
        "At 20%, a 95th-pct adverse trade costs only −1.45% of portfolio.</i>\n"
        "\n"
        "<b>▸ BATCH 2 — EV 2.0–2.99%</b>\n"
        f"<pre>{b2}</pre>\n"
        "<i>SK Hynix exactly at 2% budget limit — do not exceed 20%.\n"
        "MU: ½K=17% already tighter than 2% budget (18.6%) — 17% holds.\n"
        "AMD: both methods agree at 18%. LLY moderate tail → full ½K.</i>"
    )


def msg_batch_3() -> str:
    tbl = _fmt_batch(_BATCH3)
    return (
        "<b>▸ BATCH 3 — EV 1.5–1.99%</b>\n"
        f"<pre>{tbl}</pre>\n"
        "<i>Three variance-binding signals (! prefix — shave ½K by 1%):\n"
        "  ^TNX A  18% → <b>17%</b>  (95th = 11.53%)\n"
        "  META A  17% → <b>16%</b>  (95th = 12.26%)\n"
        "  BTC  A  16% → <b>15%</b>  (95th = 13.22%)\n"
        "\n"
        "AVGO B (+1.74%), TSLA B (+1.72%), MSFT A (+1.68%): variance\n"
        "non-binding — full ½K in all three.</i>"
    )


def msg_batch_4() -> str:
    tbl = _fmt_batch(_BATCH4)
    return (
        "<b>▸ BATCH 4 — EV 1.0–1.49%</b>\n"
        f"<pre>{tbl}</pre>\n"
        "<i>Variance NOT binding for any signal in this batch.\n"
        "PG: tightest profile — 95th=2.52%, 20% pos risks −0.50% of portfolio.\n"
        "V, NQ=F: L tail, 95th &lt; 4.6% — cleanest after PG.\n"
        "NVDA: same avg loss as TSM (−3.50%) and same 95th (7.26%); M tail.\n"
        "NFLX B: H tail but ½K=12% already well inside 2% budget.</i>"
    )


def msg_batch5_summary() -> str:
    # Split Batch 5 into two halves for readability
    mid = len(_BATCH5) // 2
    tbl_a = _fmt_batch(_BATCH5[:mid], with_action=False)
    tbl_b = _fmt_batch(_BATCH5[mid:], with_action=False)
    return (
        "<b>▸ BATCH 5 — EV 0.5–0.99% (reference, 21 signals)</b>\n"
        "<i>½K is the operative limit throughout — variance non-binding for all.</i>\n"
        f"<pre>{tbl_a}</pre>\n"
        f"<pre>{tbl_b}</pre>\n"
        "<i>SMCI: H tail (Avg Loss −6.50%), 95th=15.62% — ½K=5% already most conservative.\n"
        "ES=F 5yr: Avg Loss compresses to −0.8%; 95th ≈ 1.46% — near-zero constraint.\n"
        "V B, PG B: L tail — losses among the tightest in Signal B universe.</i>\n"
        "\n"
        "<b>⚠ VARIANCE-BINDING — FULL UNIVERSE (only 3 signals)</b>\n"
        "<pre>"
        "Signal        ½K   2%-Cap  → USE\n"
        "──────────────────────────────────\n"
        "^TNX  Sig A   18%   17.3%    17%\n"
        "META  Sig A   17%   16.3%    16%\n"
        "BTC   Sig A   16%   15.1%    15%\n"
        "──────────────────────────────────\n"
        "All others: ½K is the binding limit"
        "</pre>\n"
        "<i>3% budget → all three also clear the cap.\n"
        "Use /variants 1–4 to jump to a specific batch.</i>"
    )


# ─── Message builders — /sizing var ──────────────────────────────────────────

def msg_var_a() -> str:
    tbl = _fmt_var(_VAR_A)
    return (
        "<b>📊 SIGNAL A — VARIANCE RANKED (9yr)</b>\n"
        "<i>RSI-MA &lt;5th pct + CoV red · ranked by EV/Downside ratio</i>\n"
        f"<pre>{tbl}</pre>\n"
        "<i>"
        "DwnWt = (1−Win%) × |Avg Loss| — expected loss per trade\n"
        "EV/Dn = EV ÷ DwnWt — EV earned per unit of downside exposure\n"
        "T: L=low(≤2.5%)  M=mod(2.5–3.9%)  H=fat(≥4.0%)\n"
        "\n"
        "Tier 1 (EV/Dn ≥ 1.5, L/M tail): TSLA, PG, NQ=F, MSFT, V, CNX1.L\n"
        "Tier 2 (EV/Dn 0.5–1.5): Samsung, ES=F, NVDA\n"
        "Tier 3 (H tail): ^TNX, META, BTC → cap 10% or ¼-Kelly\n"
        "Tier 3 note: AVGO (M tail) sits at EV/Dn=0.57 — apply ¼-Kelly"
        "</i>"
    )


def msg_var_b() -> str:
    tbl = _fmt_var(_VAR_B)
    return (
        "<b>📊 SIGNAL B — VARIANCE RANKED (9yr)</b>\n"
        "<i>RSI-MA 5–15th pct + CoV red · ranked by EV/Downside ratio</i>\n"
        f"<pre>{tbl}</pre>\n"
        "<i>"
        "DwnWt = (1−Win%) × |Avg Loss| — expected loss per trade\n"
        "EV/Dn = EV ÷ DwnWt — EV earned per unit of downside exposure\n"
        "T: L=low(≤2.5%)  M=mod(2.5–3.9%)  H=fat(≥4.0%)\n"
        "\n"
        "SK Hynix: H tail (Avg Loss −4.17%) but EV/Dn=1.87 — highest in B.\n"
        "  Treat as Tier 1† — EV compensates; do not exceed 20%.\n"
        "META B: only L-tail name with W/L &gt; 2.0 (2.33) — genuine asymmetry.\n"
        "AMD/MU: high EV, H tails — apply Tier 3 cap (10% or ¼-Kelly)."
        "</i>"
    )


# ─── Public dispatch ──────────────────────────────────────────────────────────

def handle_variants_command(arg: str) -> list[str]:
    """
    Route /variants [sub-arg].
    Returns ordered list of HTML messages to send.
    No arg → full 5-message sequence.
    """
    a = arg.strip().lower()
    if a in ('1', 'b1', 'b2', 'batch1', 'batch2'):
        return [msg_batches_1_2()]
    if a in ('2', 'b3', 'batch3'):
        return [msg_batch_3()]
    if a in ('3', 'b4', 'batch4'):
        return [msg_batch_4()]
    if a in ('4', 'b5', 'batch5', 'summary', 'sum', 'binding'):
        return [msg_batch5_summary()]
    return [
        msg_intro(),
        msg_batches_1_2(),
        msg_batch_3(),
        msg_batch_4(),
        msg_batch5_summary(),
    ]


def handle_sizing_var(suffix: str) -> list[str]:
    """
    Route /sizing var[a/b] sub-commands.
    suffix is whatever follows 'var' in the user's argument.
    Returns ordered list of HTML messages.
    """
    s = suffix.strip().lower()
    if s in ('a', 'vara', 'var a', 'varianta', 'variancea', 'siga', 'sig a'):
        return [msg_var_a()]
    if s in ('b', 'varb', 'var b', 'variantb', 'varianceb', 'sigb', 'sig b'):
        return [msg_var_b()]
    return [msg_var_a(), msg_var_b()]
