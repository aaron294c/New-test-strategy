"""
Stock Statistics and Multi-Timeframe Analysis
Complete statistical data for NVDA, MSFT, GOOGL, AAPL
"""

from dataclasses import dataclass
from typing import Dict, List, Optional
from enum import Enum


class SignalStrength(Enum):
    VERY_STRONG = "✅✅✅"
    STRONG = "✅✅"
    SIGNIFICANT = "✅"
    MARGINAL = "⚠️"
    WEAK = "❌"


@dataclass
class BinStatistics:
    """Statistics for a single percentile bin"""
    bin_range: str
    mean: float
    median: Optional[float]
    std: float
    sample_size: int
    se: float
    t_score: float
    percentile_5th: Optional[float]
    percentile_95th: Optional[float]
    upside: Optional[float]
    downside: Optional[float]

    @property
    def is_significant(self) -> bool:
        """Check if t-score indicates statistical significance"""
        return abs(self.t_score) >= 2.0

    @property
    def significance_level(self) -> SignalStrength:
        """Categorize signal strength"""
        t = abs(self.t_score)
        if t >= 4.0:
            return SignalStrength.VERY_STRONG
        elif t >= 3.0:
            return SignalStrength.STRONG
        elif t >= 2.0:
            return SignalStrength.SIGNIFICANT
        elif t >= 1.5:
            return SignalStrength.MARGINAL
        else:
            return SignalStrength.WEAK

    @property
    def confidence_interval_95(self) -> tuple[float, float]:
        """Calculate 95% confidence interval"""
        margin = 1.96 * self.se
        return (self.mean - margin, self.mean + margin)


# ============================================
# NVIDIA (NVDA) DATA
# ============================================

NVDA_4H_DATA = {
    "0-5": BinStatistics("0-5%", 6.26, 5.53, 7.02, 9, 2.34, 2.67, -1.24, 6.64, 3.54, 1.26),
    "5-15": BinStatistics("5-15%", 2.08, 2.74, 6.20, 31, 1.11, 1.87, -4.15, 3.96, 2.43, 2.90),
    "15-25": BinStatistics("15-25%", 0.43, 2.51, 7.66, 27, 1.47, 0.29, -5.81, 3.65, 2.31, 1.99),
    "25-50": BinStatistics("25-50%", 3.91, 3.81, 5.78, 89, 0.61, 6.41, -3.64, 6.37, 2.77, 1.91),
    "50-75": BinStatistics("50-75%", 1.65, 1.58, 5.80, 90, 0.61, 2.70, -6.38, 5.97, 2.48, 3.44),
    "75-85": BinStatistics("75-85%", -0.18, 0.88, 4.79, 27, 0.92, 0.20, -3.71, 5.26, 2.33, 1.54),
    "85-95": BinStatistics("85-95%", -1.23, -0.03, 5.06, 27, 0.97, 1.27, -3.83, 4.62, 2.25, 2.26),
    "95-100": BinStatistics("95-100%", 0.28, 1.46, 4.10, 15, 1.06, 0.26, -4.60, 2.66, 1.60, 2.03),
}

NVDA_DAILY_DATA = {
    "0-5": BinStatistics("0-5%", 3.87, 3.75, 7.30, 37, 0.97, 3.30, -4.47, 14.23, 5.40, 3.54),
    "5-15": BinStatistics("5-15%", 0.40, 0.73, 7.62, 83, 0.56, 0.86, -6.89, 10.26, 4.40, 2.92),
    "15-25": BinStatistics("15-25%", 2.91, 3.74, 8.34, 78, 0.64, 1.91, -6.91, 10.18, 4.74, 2.99),
    "25-50": BinStatistics("25-50%", 2.51, 2.36, 8.36, 215, 0.57, 4.40, -8.89, 10.92, 5.06, 3.71),
    "50-75": BinStatistics("50-75%", 2.34, 2.26, 8.16, 209, 0.33, 2.70, -7.11, 9.17, 4.20, 2.95),
    "75-85": BinStatistics("75-85%", 1.47, 1.53, 8.66, 93, 0.57, 0.93, -8.65, 8.49, 4.28, 3.37),
    "85-95": BinStatistics("85-95%", 4.04, 4.91, 8.68, 70, 0.64, 1.70, -7.95, 10.55, 4.71, 3.43),
    "95-100": BinStatistics("95-100%", 3.17, 3.44, 7.54, 37, 0.80, 0.09, -8.53, 4.97, 2.77, 4.99),
}

# ============================================
# MICROSOFT (MSFT) DATA
# ============================================

MSFT_4H_DATA = {
    "0-5": BinStatistics("0-5%", 1.63, 0.57, 5.88, 9, 1.96, 0.83, -1.74, 2.23, 1.52, 0.74),
    "5-15": BinStatistics("5-15%", 1.84, 1.85, 2.99, 28, 0.56, 3.29, -1.23, 2.66, 1.43, 1.64),
    "15-25": BinStatistics("15-25%", 1.55, 1.58, 2.69, 26, 0.53, 2.92, -2.07, 1.78, 1.26, 1.28),
    "25-50": BinStatistics("25-50%", 1.17, 1.40, 2.43, 103, 0.24, 4.88, -3.08, 2.86, 1.19, 1.28),
    "50-75": BinStatistics("50-75%", 0.90, 0.80, 3.69, 71, 0.44, 2.05, -1.96, 3.06, 1.56, 0.83),
    "75-85": BinStatistics("75-85%", 1.55, 0.75, 4.33, 32, 0.77, 2.01, -2.19, 4.03, 2.11, 1.06),
    "85-95": BinStatistics("85-95%", 0.16, -1.02, 5.20, 33, 0.91, 0.18, -1.75, 1.64, 0.76, 0.70),
    "95-100": BinStatistics("95-100%", -0.20, 0.30, 2.55, 13, 0.71, 0.28, -1.94, 2.15, 1.03, 0.74),
}

MSFT_DAILY_DATA = {
    "0-5": BinStatistics("0-5%", 0.73, 0.25, 4.33, 34, 0.44, 1.68, -2.47, 3.47, 2.01, 1.00),
    "5-15": BinStatistics("5-15%", 0.84, 0.63, 3.96, 78, 0.33, 1.48, -3.46, 6.60, 2.68, 1.28),
    "15-25": BinStatistics("15-25%", 1.43, 0.92, 4.51, 76, 0.33, 2.64, -3.06, 5.55, 2.61, 1.47),
    "25-50": BinStatistics("25-50%", 0.89, 0.92, 3.54, 231, 0.23, 3.87, -3.42, 4.64, 1.89, 1.57),
    "50-75": BinStatistics("50-75%", 0.62, 0.82, 3.72, 195, 0.20, 1.40, -4.55, 4.69, 2.24, 1.89),
    "75-85": BinStatistics("75-85%", 0.69, 0.75, 4.17, 83, 0.34, 1.21, -4.87, 4.24, 2.19, 1.96),
    "85-95": BinStatistics("85-95%", 0.37, 1.06, 4.29, 81, 0.30, 0.60, -5.00, 3.02, 1.56, 2.30),
    "95-100": BinStatistics("95-100%", -0.56, 0.17, 4.48, 44, 0.39, 1.26, -5.90, 2.12, 1.10, 2.59),
}

# ============================================
# GOOGLE (GOOGL) DATA
# ============================================

GOOGL_4H_DATA = {
    "0-5": BinStatistics("0-5%", 3.10, 5.01, 5.17, 18, 1.22, 2.54, -1.37, 3.46, 1.93, 0.79),
    "5-15": BinStatistics("5-15%", 3.33, 3.75, 4.81, 29, 0.89, 3.74, -4.01, 3.44, 2.70, 1.50),
    "15-25": BinStatistics("15-25%", 1.77, 2.77, 4.67, 37, 0.77, 2.30, -4.98, 4.73, 2.10, 1.78),
    "25-50": BinStatistics("25-50%", 1.75, 1.70, 4.49, 73, 0.53, 3.30, -4.19, 4.01, 1.85, 1.87),
    "50-75": BinStatistics("50-75%", 1.31, 1.78, 3.84, 78, 0.43, 3.05, -3.01, 3.40, 1.71, 1.94),
    "75-85": BinStatistics("75-85%", 0.51, 0.58, 4.61, 33, 0.80, 0.64, -3.00, 3.98, 2.11, 1.53),
    "85-95": BinStatistics("85-95%", 0.07, 0.43, 4.42, 34, 0.76, 0.09, -2.33, 2.66, 1.35, 1.17),
    "95-100": BinStatistics("95-100%", 1.23, 3.09, 5.41, 13, 1.50, 0.82, -3.16, 2.33, 1.71, 1.24),
}

GOOGL_DAILY_DATA = {
    "0-5": BinStatistics("0-5%", 2.01, 1.67, 4.81, 31, 0.39, 3.56, -1.90, 5.49, 2.15, 0.63),
    "5-15": BinStatistics("5-15%", 1.16, 0.65, 4.74, 75, 0.37, 3.16, -3.44, 6.23, 3.15, 1.62),
    "15-25": BinStatistics("15-25%", 1.09, 0.90, 4.55, 77, 0.35, 1.34, -4.11, 5.14, 2.56, 1.59),
    "25-50": BinStatistics("25-50%", 1.05, 1.25, 5.38, 205, 0.26, 1.12, -6.47, 5.79, 2.96, 2.54),
    "50-75": BinStatistics("50-75%", 0.93, 1.42, 4.90, 214, 0.25, 2.82, -5.62, 7.08, 2.97, 2.26),
    "75-85": BinStatistics("75-85%", 0.85, 1.05, 4.28, 96, 0.32, 1.59, -4.66, 5.24, 2.55, 2.11),
    "85-95": BinStatistics("85-95%", -0.99, -0.68, 4.83, 71, 0.41, 2.41, -7.83, 3.87, 1.65, 2.90),
    "95-100": BinStatistics("95-100%", 0.37, 0.66, 5.48, 53, 0.43, 0.02, -4.95, 4.43, 2.06, 2.56),
}

# ============================================
# APPLE (AAPL) DATA
# ============================================

AAPL_4H_DATA = {
    "0-5": BinStatistics("0-5%", 3.99, 4.48, 6.80, 17, 1.65, 2.42, -9.35, 3.87, 2.30, 3.87),
    "5-15": BinStatistics("5-15%", 3.55, 3.15, 4.81, 28, 0.91, 3.90, -3.97, 5.85, 3.09, 1.19),
    "15-25": BinStatistics("15-25%", 1.85, 1.89, 5.07, 34, 0.87, 2.13, -3.05, 3.75, 1.79, 1.17),
    "25-50": BinStatistics("25-50%", -0.27, 0.69, 5.08, 81, 0.56, 0.48, -2.48, 5.71, 1.81, 1.04),
    "50-75": BinStatistics("50-75%", -1.07, -0.56, 6.15, 77, 0.70, 1.53, -3.76, 3.33, 1.48, 2.66),
    "75-85": BinStatistics("75-85%", -0.76, 0.85, 5.74, 28, 1.08, 0.70, -6.96, 2.44, 1.27, 2.92),
    "85-95": BinStatistics("85-95%", -1.02, -0.89, 5.28, 28, 1.00, 1.02, -1.36, 3.76, 1.74, 0.65),
    "95-100": BinStatistics("95-100%", 1.36, 0.87, 3.09, 22, 0.66, 2.06, -1.51, 4.28, 2.10, 0.61),
}

AAPL_DAILY_DATA = {
    "0-5": BinStatistics("0-5%", 1.13, -0.03, 5.48, 39, 0.62, 0.98, -3.53, 6.16, 3.41, 1.43),
    "5-15": BinStatistics("5-15%", 0.55, 0.31, 4.88, 84, 0.39, 0.72, -3.89, 5.18, 2.62, 2.77),
    "15-25": BinStatistics("15-25%", 1.55, 2.02, 4.48, 78, 0.38, 2.16, -4.30, 6.35, 3.13, 1.71),
    "25-50": BinStatistics("25-50%", 0.67, 1.24, 4.59, 203, 0.32, 2.09, -5.44, 4.56, 2.18, 2.09),
    "50-75": BinStatistics("50-75%", 0.62, 0.54, 4.03, 213, 0.19, 1.76, -4.42, 4.93, 2.16, 1.82),
    "75-85": BinStatistics("75-85%", 0.39, 0.78, 4.85, 89, 0.40, 1.59, -4.13, 3.99, 2.10, 4.21),
    "85-95": BinStatistics("85-95%", 0.20, 0.67, 4.66, 80, 0.26, 1.70, -3.31, 3.56, 1.77, 1.76),
    "95-100": BinStatistics("95-100%", 0.33, 1.00, 3.87, 36, 0.40, 0.68, -4.80, 2.72, 1.67, 2.08),
}


# ============================================
# STOCK METADATA
# ============================================

@dataclass
class StockMetadata:
    """Metadata about stock trading characteristics"""
    ticker: str
    name: str
    personality: str
    reliability_4h: str
    reliability_daily: str
    tradeable_4h_zones: List[str]
    dead_zones_4h: List[str]
    best_4h_bin: str
    best_4h_t_score: float
    ease_rating: int  # 1-5 stars

    # Characteristics
    is_mean_reverter: bool
    is_momentum: bool
    volatility_level: str  # "High", "Medium", "Low"

    # Trading guidance
    entry_guidance: str
    avoid_guidance: str
    special_notes: str


STOCK_METADATA = {
    "NVDA": StockMetadata(
        ticker="NVDA",
        name="NVIDIA",
        personality="Selective Bouncer",
        reliability_4h="⭐⭐⭐ Good (37.5% coverage)",
        reliability_daily="⭐⭐⭐⭐ Very Good",
        tradeable_4h_zones=["0-5%", "25-75%"],
        dead_zones_4h=["5-25%", "75-100%"],
        best_4h_bin="25-50%",
        best_4h_t_score=6.41,
        ease_rating=3,
        is_mean_reverter=True,
        is_momentum=False,
        volatility_level="High",
        entry_guidance="Wait for 4H @ 25-50% for best risk/reward or aggressive buying at 0-5%",
        avoid_guidance="Don't trade 4H 5-25% (no edge) or 75-100% (trim/exit)",
        special_notes="Highest t-score of all stocks at 25-50% sweet spot"
    ),
    "MSFT": StockMetadata(
        ticker="MSFT",
        name="Microsoft",
        personality="Steady Eddie",
        reliability_4h="⭐⭐⭐⭐⭐ Excellent (75% coverage)",
        reliability_daily="⭐⭐⭐⭐ Very Good",
        tradeable_4h_zones=["5-85%"],
        dead_zones_4h=["0-5%", "85-100%"],
        best_4h_bin="25-50%",
        best_4h_t_score=4.88,
        ease_rating=5,
        is_mean_reverter=True,
        is_momentum=False,
        volatility_level="Medium",
        entry_guidance="Can enter almost anywhere 5-75%, target 25-50% for optimal entry",
        avoid_guidance="Skip extreme dips 0-5% (small sample) and 85-100% (no edge)",
        special_notes="Most reliable stock - works across widest range"
    ),
    "GOOGL": StockMetadata(
        ticker="GOOGL",
        name="Google",
        personality="Mean Reverter",
        reliability_4h="⭐⭐⭐⭐ Very Good (62.5% coverage)",
        reliability_daily="⭐⭐⭐ Good",
        tradeable_4h_zones=["0-75%"],
        dead_zones_4h=["75-100%"],
        best_4h_bin="5-15%",
        best_4h_t_score=3.74,
        ease_rating=4,
        is_mean_reverter=True,
        is_momentum=False,
        volatility_level="Medium",
        entry_guidance="Wait for 4H @ 5-15% for best bounce, aggressive buying below 25%",
        avoid_guidance="NEVER enter when 4H > 75% (zero edge)",
        special_notes="Strong mean reversion below 75%, upper range completely fails"
    ),
    "AAPL": StockMetadata(
        ticker="AAPL",
        name="Apple",
        personality="The Extremist",
        reliability_4h="⭐⭐ Poor (50% but patchy)",
        reliability_daily="⭐⭐⭐ Good",
        tradeable_4h_zones=["0-25%", "95-100%"],
        dead_zones_4h=["25-95%"],
        best_4h_bin="5-15%",
        best_4h_t_score=3.90,
        ease_rating=2,
        is_mean_reverter=False,
        is_momentum=True,
        volatility_level="Medium-High",
        entry_guidance="ONLY trade 4H extremes (0-25%), be patient for good setups",
        avoid_guidance="NEVER trade 4H 25-95% range (62.5% of time - no statistical edge)",
        special_notes="U-shaped curve - mid-range has zero predictive power, median/mean divergence common"
    )
}


# ============================================
# HELPER FUNCTIONS
# ============================================

def get_stock_data(ticker: str, timeframe: str) -> Dict[str, BinStatistics]:
    """Get statistical data for a stock and timeframe"""
    data_map = {
        ("NVDA", "4H"): NVDA_4H_DATA,
        ("NVDA", "Daily"): NVDA_DAILY_DATA,
        ("MSFT", "4H"): MSFT_4H_DATA,
        ("MSFT", "Daily"): MSFT_DAILY_DATA,
        ("GOOGL", "4H"): GOOGL_4H_DATA,
        ("GOOGL", "Daily"): GOOGL_DAILY_DATA,
        ("AAPL", "4H"): AAPL_4H_DATA,
        ("AAPL", "Daily"): AAPL_DAILY_DATA,
    }

    key = (ticker, timeframe)
    if key not in data_map:
        raise ValueError(f"Unknown ticker/timeframe: {ticker}/{timeframe}")

    return data_map[key]


def calculate_position_size(daily_t: float, fourh_t: float) -> Dict:
    """Calculate recommended position size based on combined t-scores"""
    daily_score = min(max(daily_t / 2.0, 0), 2)
    fourh_score = min(max(fourh_t / 2.0, 0), 2)

    # Determine position size
    if daily_score < 1.0:
        return {
            "position": 0,
            "confidence": "NO TRADE",
            "action": "SKIP - Daily signal too weak"
        }

    if daily_score >= 1.5:
        if fourh_score >= 1.5:
            return {"position": 70, "confidence": "VERY HIGH", "action": "ENTER"}
        elif fourh_score >= 1.0:
            return {"position": 50, "confidence": "HIGH", "action": "ENTER"}
        else:
            return {"position": 30, "confidence": "MEDIUM", "action": "WAIT for better 4H"}

    if daily_score >= 1.0:
        if fourh_score >= 1.5:
            return {"position": 40, "confidence": "MEDIUM", "action": "Short-term trade"}
        else:
            return {"position": 0, "confidence": "LOW", "action": "SKIP"}

    return {"position": 0, "confidence": "NO TRADE", "action": "SKIP"}


def get_action_for_4h_bin(bin_range: str, stats: BinStatistics) -> Dict:
    """Determine trading action for a 4H bin"""
    bin_num = int(bin_range.split("-")[0].replace("%", ""))

    if stats.t_score >= 2.0:
        if bin_num < 25:
            return {"action": "Enter / Aggressive Add", "size": "60-70%", "color": "success"}
        elif bin_num < 50:
            return {"action": "Enter / Good Add", "size": "50-60%", "color": "success"}
        elif bin_num < 75:
            return {"action": "Enter / Acceptable", "size": "30-50%", "color": "info"}
        else:
            return {"action": "Trim if in position", "size": "10-30%", "color": "warning"}
    else:
        if bin_num < 75:
            return {"action": "Wait (no edge)", "size": "0%", "color": "error"}
        else:
            return {"action": "Avoid / Trim", "size": "Trim 30-50%", "color": "error"}
