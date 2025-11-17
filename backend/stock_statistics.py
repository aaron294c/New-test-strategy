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
# GOLD (GLD) DATA
# ============================================

GLD_4H_DATA = {
    "0-5": BinStatistics("0-5%", 0.33, -0.1, 2.48, 57, 0.33, 1.01, -2.62, 5.21, 2.2, -1.35),
    "5-15": BinStatistics("5-15%", 0.25, 0.07, 1.73, 115, 0.16, 1.52, -2.33, 2.92, 1.53, -1.11),
    "15-25": BinStatistics("15-25%", 0.12, 0.01, 1.71, 118, 0.16, 0.79, -2.88, 3.05, 1.45, -1.21),
    "25-50": BinStatistics("25-50%", 0.4, 0.31, 1.73, 282, 0.1, 3.92, -2.29, 3.07, 1.55, -1.24),
    "50-75": BinStatistics("50-75%", 0.5, 0.45, 1.69, 311, 0.1, 5.22, -2.11, 3.05, 1.45, -1.12),
    "75-85": BinStatistics("75-85%", 0.52, 0.37, 1.63, 127, 0.14, 3.56, -1.91, 3.39, 1.53, -1.0),
    "85-95": BinStatistics("85-95%", 0.6, 0.73, 1.82, 123, 0.16, 3.67, -2.46, 3.49, 1.57, -1.41),
    "95-100": BinStatistics("95-100%", 0.93, 1.11, 1.86, 58, 0.24, 3.82, -2.29, 3.34, 2.04, -1.17),
}

GLD_DAILY_DATA = {
    "0-5": BinStatistics("0-5%", 1.67, 1.4, 3.59, 36, 0.6, 2.8, -2.82, 7.65, 3.39, -1.75),
    "5-15": BinStatistics("5-15%", 0.36, 0.28, 2.1, 76, 0.24, 1.5, -2.48, 4.27, 1.88, -1.46),
    "15-25": BinStatistics("15-25%", 0.76, 0.47, 2.38, 79, 0.27, 2.86, -2.78, 5.07, 2.2, -1.46),
    "25-50": BinStatistics("25-50%", 0.47, 0.36, 2.52, 218, 0.17, 2.76, -4.02, 4.29, 2.01, -1.73),
    "50-75": BinStatistics("50-75%", 0.78, 0.65, 2.57, 208, 0.18, 4.41, -2.96, 5.56, 2.46, -1.59),
    "75-85": BinStatistics("75-85%", 0.64, 0.86, 2.65, 90, 0.28, 2.28, -3.35, 4.5, 2.57, -1.9),
    "85-95": BinStatistics("85-95%", 0.82, 0.77, 2.89, 82, 0.32, 2.57, -3.89, 6.03, 2.62, -1.99),
    "95-100": BinStatistics("95-100%", 1.32, 1.35, 2.34, 40, 0.37, 3.58, -1.64, 5.06, 2.39, -1.49),
}

# ============================================
# SILVER (SLV) DATA
# ============================================

SLV_4H_DATA = {
    "0-5": BinStatistics("0-5%", -0.21, 0.02, 3.02, 59, 0.39, -0.54, -4.69, 4.88, 2.1, -2.61),
    "5-15": BinStatistics("5-15%", 0.23, -0.21, 3.21, 102, 0.32, 0.72, -4.56, 5.46, 3.0, -2.43),
    "15-25": BinStatistics("15-25%", -0.4, -0.2, 3.49, 115, 0.33, -1.22, -5.67, 4.92, 2.45, -2.91),
    "25-50": BinStatistics("25-50%", 0.47, 0.45, 3.4, 285, 0.2, 2.32, -4.49, 6.1, 2.71, -2.61),
    "50-75": BinStatistics("50-75%", 0.57, 0.5, 3.4, 321, 0.19, 3.02, -4.91, 6.4, 2.9, -2.42),
    "75-85": BinStatistics("75-85%", 0.74, 0.61, 3.14, 128, 0.28, 2.65, -4.63, 5.69, 2.55, -2.19),
    "85-95": BinStatistics("85-95%", 0.73, 0.52, 2.62, 122, 0.24, 3.06, -3.73, 5.09, 2.19, -1.7),
    "95-100": BinStatistics("95-100%", 1.75, 1.7, 2.85, 58, 0.37, 4.68, -2.29, 6.14, 3.04, -1.38),
}

SLV_DAILY_DATA = {
    "0-5": BinStatistics("0-5%", 1.91, 2.5, 4.04, 35, 0.68, 2.8, -3.39, 8.69, 4.68, -2.24),
    "5-15": BinStatistics("5-15%", 0.71, 0.24, 4.38, 73, 0.51, 1.38, -4.8, 9.15, 3.88, -2.93),
    "15-25": BinStatistics("15-25%", 1.23, 0.78, 4.51, 74, 0.52, 2.35, -5.31, 9.33, 4.02, -2.87),
    "25-50": BinStatistics("25-50%", 1.0, 0.7, 5.38, 228, 0.36, 2.81, -7.56, 10.09, 4.98, -3.57),
    "50-75": BinStatistics("50-75%", 0.69, 0.33, 4.78, 211, 0.33, 2.09, -6.79, 8.78, 4.11, -3.49),
    "75-85": BinStatistics("75-85%", -0.42, -0.57, 5.47, 97, 0.56, -0.76, -9.66, 8.0, 4.36, -4.73),
    "85-95": BinStatistics("85-95%", 1.51, 1.59, 3.88, 75, 0.45, 3.37, -5.0, 7.63, 3.77, -2.76),
    "95-100": BinStatistics("95-100%", 1.07, 1.84, 4.33, 40, 0.68, 1.56, -7.51, 7.0, 3.72, -3.86),
}

# ============================================
# Tesla, Inc. (TSLA) DATA
# ============================================

TSLA_4H_DATA = {
    "0-5": BinStatistics("0-5%", 1.31, 0.75, 4.73, 53, 0.65, 2.02, -7.09, 8.26, 4.21, -3.11),
    "5-15": BinStatistics("5-15%", 0.1, 0.01, 7.05, 123, 0.64, 0.15, -10.67, 12.19, 5.48, -5.38),
    "15-25": BinStatistics("15-25%", 0.07, -0.57, 6.17, 124, 0.55, 0.13, -9.32, 8.49, 5.44, -4.36),
    "25-50": BinStatistics("25-50%", 0.25, -0.07, 7.45, 308, 0.42, 0.6, -11.39, 11.81, 5.98, -5.32),
    "50-75": BinStatistics("50-75%", 0.33, -0.48, 6.87, 300, 0.4, 0.84, -9.88, 12.49, 5.6, -4.46),
    "75-85": BinStatistics("75-85%", 1.56, 1.43, 7.37, 114, 0.69, 2.26, -9.87, 15.14, 6.0, -4.77),
    "85-95": BinStatistics("85-95%", 1.79, 0.7, 6.79, 113, 0.64, 2.79, -7.64, 15.06, 6.26, -3.85),
    "95-100": BinStatistics("95-100%", 2.26, 1.56, 7.2, 57, 0.95, 2.37, -6.89, 16.24, 7.01, -3.82),
}

TSLA_DAILY_DATA = {
    "0-5": BinStatistics("0-5%", -2.06, -1.08, 8.97, 40, 1.42, -1.45, -14.97, 14.77, 6.34, -7.66),
    "5-15": BinStatistics("5-15%", 0.15, -1.19, 10.33, 79, 1.16, 0.13, -15.09, 16.25, 8.97, -7.62),
    "15-25": BinStatistics("15-25%", -2.22, -4.4, 9.69, 81, 1.08, -2.06, -18.72, 14.3, 7.26, -8.74),
    "25-50": BinStatistics("25-50%", 0.82, 0.63, 10.91, 208, 0.76, 1.09, -16.2, 20.35, 8.48, -7.94),
    "50-75": BinStatistics("50-75%", 1.39, 1.39, 10.08, 209, 0.7, 2.0, -14.46, 19.73, 8.23, -7.14),
    "75-85": BinStatistics("75-85%", 0.31, -0.95, 9.58, 102, 0.95, 0.33, -15.14, 18.84, 8.53, -6.18),
    "85-95": BinStatistics("85-95%", 4.06, 2.66, 11.51, 71, 1.37, 2.97, -12.48, 30.44, 11.31, -5.84),
    "95-100": BinStatistics("95-100%", 8.66, 7.71, 11.21, 41, 1.75, 4.95, -6.77, 26.2, 14.45, -3.79),
}

# ============================================
# Netflix Inc. (NFLX) DATA
# ============================================

NFLX_4H_DATA = {
    "0-5": BinStatistics("0-5%", 0.12, -0.58, 3.76, 64, 0.47, 0.26, -4.85, 6.74, 3.73, -2.35),
    "5-15": BinStatistics("5-15%", 1.15, 0.91, 4.13, 118, 0.38, 3.02, -4.02, 7.74, 3.49, -2.52),
    "15-25": BinStatistics("15-25%", 0.37, -0.1, 3.2, 120, 0.29, 1.25, -3.82, 5.67, 2.8, -1.91),
    "25-50": BinStatistics("25-50%", 0.24, 0.38, 3.55, 299, 0.21, 1.18, -5.2, 5.15, 2.62, -2.77),
    "50-75": BinStatistics("50-75%", 0.78, 0.61, 3.78, 300, 0.22, 3.56, -4.83, 6.44, 3.01, -2.35),
    "75-85": BinStatistics("75-85%", 0.75, 0.48, 3.87, 115, 0.36, 2.08, -4.42, 5.61, 3.22, -2.35),
    "85-95": BinStatistics("85-95%", 0.98, 0.99, 4.24, 114, 0.4, 2.48, -5.8, 7.22, 3.31, -3.0),
    "95-100": BinStatistics("95-100%", 0.75, 1.38, 4.01, 60, 0.52, 1.44, -7.86, 5.69, 3.06, -2.97),
}

NFLX_DAILY_DATA = {
    "0-5": BinStatistics("0-5%", 0.84, -0.67, 6.89, 38, 1.12, 0.75, -7.63, 14.38, 6.92, -4.09),
    "5-15": BinStatistics("5-15%", 1.2, 0.67, 6.9, 80, 0.77, 1.56, -8.58, 14.61, 6.1, -4.21),
    "15-25": BinStatistics("15-25%", 2.35, 2.18, 5.88, 86, 0.63, 3.7, -6.81, 11.21, 5.66, -3.83),
    "25-50": BinStatistics("25-50%", 2.08, 1.47, 6.96, 222, 0.47, 4.45, -7.08, 16.03, 6.17, -3.92),
    "50-75": BinStatistics("50-75%", 1.35, 0.81, 6.47, 204, 0.45, 2.98, -9.02, 11.9, 5.66, -4.01),
    "75-85": BinStatistics("75-85%", 1.86, 0.89, 6.45, 92, 0.67, 2.77, -8.22, 13.76, 5.85, -3.79),
    "85-95": BinStatistics("85-95%", 1.35, 1.67, 6.17, 73, 0.72, 1.87, -10.91, 10.19, 4.91, -5.08),
    "95-100": BinStatistics("95-100%", 2.37, 2.23, 3.37, 40, 0.53, 4.46, -2.56, 8.58, 3.84, -1.49),
}

# ============================================
# Berkshire Hathaway Inc. Class B (BRK-B) DATA
# ============================================

BRKB_4H_DATA = {
    "0-5": BinStatistics("0-5%", 0.11, -0.23, 2.78, 50, 0.39, 0.27, -3.48, 4.74, 2.23, -1.85),
    "5-15": BinStatistics("5-15%", -0.07, -0.29, 1.8, 122, 0.16, -0.42, -2.97, 3.06, 1.41, -1.37),
    "15-25": BinStatistics("15-25%", 0.22, 0.3, 1.81, 126, 0.16, 1.35, -2.51, 2.9, 1.55, -1.39),
    "25-50": BinStatistics("25-50%", 0.12, 0.03, 2.04, 291, 0.12, 1.01, -2.88, 3.0, 1.61, -1.38),
    "50-75": BinStatistics("50-75%", 0.28, 0.24, 1.61, 316, 0.09, 3.09, -2.45, 3.04, 1.36, -1.14),
    "75-85": BinStatistics("75-85%", 0.28, 0.38, 1.72, 124, 0.15, 1.79, -2.41, 2.96, 1.35, -1.31),
    "85-95": BinStatistics("85-95%", 0.4, 0.26, 1.89, 109, 0.18, 2.22, -2.01, 4.14, 1.66, -1.2),
    "95-100": BinStatistics("95-100%", 0.53, 0.31, 1.84, 54, 0.25, 2.12, -1.84, 4.27, 1.62, -1.06),
}

BRKB_DAILY_DATA = {
    "0-5": BinStatistics("0-5%", 0.95, 1.1, 3.15, 35, 0.53, 1.79, -4.35, 5.88, 2.38, -3.18),
    "5-15": BinStatistics("5-15%", 0.58, 0.29, 2.15, 73, 0.25, 2.32, -2.57, 4.46, 1.94, -1.36),
    "15-25": BinStatistics("15-25%", 0.47, 0.81, 2.58, 77, 0.29, 1.61, -4.07, 4.11, 2.0, -2.36),
    "25-50": BinStatistics("25-50%", 0.7, 0.38, 2.66, 228, 0.18, 3.95, -3.06, 5.44, 2.54, -1.66),
    "50-75": BinStatistics("50-75%", 0.33, 0.31, 2.78, 214, 0.19, 1.72, -3.64, 4.99, 2.28, -2.12),
    "75-85": BinStatistics("75-85%", 0.66, 0.45, 2.74, 83, 0.3, 2.2, -3.21, 4.31, 2.4, -2.12),
    "85-95": BinStatistics("85-95%", 0.07, 0.27, 2.5, 86, 0.27, 0.25, -3.95, 3.65, 2.12, -2.18),
    "95-100": BinStatistics("95-100%", 0.62, 0.81, 2.28, 35, 0.39, 1.61, -2.75, 3.86, 2.15, -1.67),
}

# ============================================
# Walmart Inc. (WMT) DATA
# ============================================

WMT_4H_DATA = {
    "0-5": BinStatistics("0-5%", 0.62, 0.22, 2.93, 55, 0.4, 1.57, -2.95, 4.88, 2.33, -1.49),
    "5-15": BinStatistics("5-15%", 0.29, 0.29, 2.38, 124, 0.21, 1.34, -2.9, 3.67, 1.77, -1.64),
    "15-25": BinStatistics("15-25%", 0.24, 0.38, 2.46, 119, 0.23, 1.06, -3.32, 4.29, 1.7, -1.93),
    "25-50": BinStatistics("25-50%", 0.19, 0.2, 2.28, 304, 0.13, 1.49, -3.11, 3.36, 1.7, -1.59),
    "50-75": BinStatistics("50-75%", 0.62, 0.49, 2.11, 285, 0.12, 4.99, -2.26, 4.18, 1.81, -1.29),
    "75-85": BinStatistics("75-85%", 0.39, 0.32, 2.59, 108, 0.25, 1.57, -3.02, 4.17, 2.1, -1.67),
    "85-95": BinStatistics("85-95%", 0.7, 0.7, 2.27, 131, 0.2, 3.55, -2.3, 3.78, 1.84, -1.47),
    "95-100": BinStatistics("95-100%", 0.71, 0.99, 1.91, 59, 0.25, 2.83, -2.47, 3.49, 1.8, -1.28),
}

WMT_DAILY_DATA = {
    "0-5": BinStatistics("0-5%", 0.47, 0.47, 2.54, 41, 0.4, 1.18, -3.19, 3.66, 1.97, -1.89),
    "5-15": BinStatistics("5-15%", 0.35, 0.41, 3.61, 75, 0.42, 0.83, -4.21, 5.36, 3.02, -2.56),
    "15-25": BinStatistics("15-25%", 1.44, 1.05, 3.88, 79, 0.44, 3.31, -3.59, 7.87, 3.56, -1.83),
    "25-50": BinStatistics("25-50%", 0.77, 0.72, 3.32, 223, 0.22, 3.47, -3.94, 6.54, 2.8, -2.17),
    "50-75": BinStatistics("50-75%", 0.95, 0.99, 2.96, 206, 0.21, 4.61, -3.48, 6.12, 2.72, -1.95),
    "75-85": BinStatistics("75-85%", 0.37, 0.73, 3.35, 84, 0.37, 1.01, -5.76, 5.71, 2.47, -2.88),
    "85-95": BinStatistics("85-95%", 1.07, 1.17, 2.94, 84, 0.32, 3.34, -4.42, 5.86, 2.29, -2.58),
    "95-100": BinStatistics("95-100%", 1.7, 1.61, 2.47, 39, 0.4, 4.3, -2.52, 5.25, 2.91, -1.4),
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
    # Market Indices - Broad Market Exposure
    "SPY": StockMetadata(
        ticker="SPY",
        name="S&P 500 ETF",
        personality="Market Benchmark",
        reliability_4h="⭐⭐⭐⭐ Very Good",
        reliability_daily="⭐⭐⭐⭐⭐ Excellent",
        tradeable_4h_zones=["0-75%"],
        dead_zones_4h=["75-100%"],
        best_4h_bin="5-25%",
        best_4h_t_score=0.0,  # Will be calculated from real data
        ease_rating=5,
        is_mean_reverter=True,
        is_momentum=False,
        volatility_level="Low",
        entry_guidance="Buy market dips at ≤15% percentile for mean reversion plays",
        avoid_guidance="Avoid entering above 75% percentile - limited upside",
        special_notes="Tracks broad market, excellent for mean reversion at extreme lows"
    ),
    "QQQ": StockMetadata(
        ticker="QQQ",
        name="Nasdaq 100 ETF",
        personality="Tech Momentum Leader",
        reliability_4h="⭐⭐⭐⭐ Very Good",
        reliability_daily="⭐⭐⭐⭐⭐ Excellent",
        tradeable_4h_zones=["0-75%"],
        dead_zones_4h=["75-100%"],
        best_4h_bin="5-25%",
        best_4h_t_score=0.0,  # Will be calculated from real data
        ease_rating=5,
        is_mean_reverter=True,
        is_momentum=True,  # Can exhibit both behaviors
        volatility_level="Medium",
        entry_guidance="Buy tech dips at ≤15% percentile, can ride momentum above 50%",
        avoid_guidance="Avoid entering above 75% without momentum confirmation",
        special_notes="Tech-heavy, higher beta than SPY, good for both mean reversion and momentum"
    ),

    # Individual Stocks
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
    ),
    "GLD": StockMetadata(
        ticker="GLD",
        name="SPDR Gold Trust",
        personality="Safe Haven - Momentum Trending",
        reliability_4h="High",
        reliability_daily="High",
        tradeable_4h_zones=['25-50', '50-75', '75-85', '85-95', '95-100'],
        dead_zones_4h=['0-5', '15-25'],
        best_4h_bin="50-75",
        best_4h_t_score=5.22,
        ease_rating=5,
        is_mean_reverter=False,
        is_momentum=True,
        volatility_level="Low",
        entry_guidance="Enter LONG when percentile < 25 (oversold). Gold shows mean reversion at extremes.",
        avoid_guidance="Avoid trading in 0-25 range at 4H - weak signals. Be cautious in high volatility periods.",
        special_notes="Gold is a safe haven asset. Best during market uncertainty. Works well for swing trades (7-14 day holds). Daily shows strong edge across most bins."
    ),
    "SLV": StockMetadata(
        ticker="SLV",
        name="iShares Silver Trust",
        personality="Volatile Safe Haven - Momentum",
        reliability_4h="High",
        reliability_daily="High",
        tradeable_4h_zones=['25-50', '50-75', '75-85', '85-95', '95-100'],
        dead_zones_4h=['0-5', '5-15', '15-25'],
        best_4h_bin="95-100",
        best_4h_t_score=4.68,
        ease_rating=4,
        is_mean_reverter=False,
        is_momentum=True,
        volatility_level="Medium",
        entry_guidance="Enter LONG when percentile < 25 (oversold). Silver shows stronger mean reversion than gold.",
        avoid_guidance="Avoid 0-25 range at 4H - weak/negative signals. Be cautious of high volatility (>5% daily moves).",
        special_notes="Silver is more volatile than gold. Strong mean reversion at extremes (0-25%ile on Daily). Best for 7-14 day holds. 95-100 4H zone is strongest."
    ),
    "TSLA": StockMetadata(
        ticker="TSLA",
        name="Tesla, Inc.",
        personality="High Volatility Momentum - Strong trending behavior",
        reliability_4h="High",
        reliability_daily="High",
        tradeable_4h_zones=['0-5', '75-85', '85-95', '95-100'],
        dead_zones_4h=['5-15', '15-25', '25-50', '50-75'],
        best_4h_bin="85-95",
        best_4h_t_score=2.79,
        ease_rating=8,
        is_mean_reverter=False,
        is_momentum=True,
        volatility_level="High",
        entry_guidance="Enter LONG when momentum is confirmed (percentile > 75). TSLA shows strong trending behavior. Avoid catching falling knives.",
        avoid_guidance="Avoid trading in 25-50 range - weak signals. Never fight the trend. Be cautious during earnings.",
        special_notes="TSLA is extremely volatile and momentum-driven. Best for trend following strategies. Use wider stops. Works well for 7-14 day momentum plays. High news sensitivity."
    ),
    "NFLX": StockMetadata(
        ticker="NFLX",
        name="Netflix Inc.",
        personality="High Volatility Momentum - Earnings Driven",
        reliability_4h="High",
        reliability_daily="High",
        tradeable_4h_zones=['5-15', '50-75', '75-85', '85-95'],
        dead_zones_4h=['0-5', '15-25', '25-50', '95-100'],
        best_4h_bin="50-75",
        best_4h_t_score=3.56,
        ease_rating=9,
        is_mean_reverter=False,
        is_momentum=True,
        volatility_level="High",
        entry_guidance="Enter LONG when percentile > 75 (momentum plays). NFLX shows strong momentum characteristics. Watch for earnings catalysts.",
        avoid_guidance="Avoid trading in 0-5, 15-25, 25-50, 95-100 ranges - weak signals. Exercise extreme caution around earnings dates (high volatility).",
        special_notes="NFLX is highly volatile (avg daily std > 5%) Strong momentum characteristics - trends can persist Earnings-driven stock with unpredictable reactions to quarterly reports Best for experienced traders comfortable with high volatility Consider position sizing due to large price swings Best 4H trading zones: 5-15, 50-75, 75-85, 85-95"
    ),
    "AMZN": StockMetadata(
        ticker="AMZN",
        name="Amazon.com Inc.",
        personality="Mean Reversion - High Volume Leader",
        reliability_4h="⭐⭐⭐⭐ Very Good",
        reliability_daily="⭐⭐⭐⭐⭐ Excellent",
        tradeable_4h_zones=["0-75%"],
        dead_zones_4h=["75-100%"],
        best_4h_bin="5-15%",
        best_4h_t_score=0.0,  # Will be calculated from real data
        ease_rating=4,
        is_mean_reverter=True,
        is_momentum=False,
        volatility_level="Medium",
        entry_guidance="Buy at ≤15% percentile for mean reversion plays, strong bounce potential",
        avoid_guidance="Avoid entering above 75% percentile - limited upside potential",
        special_notes="Large cap with strong mean reversion characteristics, excellent liquidity for swing trading"
    ),
    "BRK-B": StockMetadata(
        ticker="BRK-B",
        name="Berkshire Hathaway Inc. Class B",
        personality="Momentum Trending",
        reliability_4h="High",
        reliability_daily="Medium",
        tradeable_4h_zones=['50-75', '85-95', '95-100'],
        dead_zones_4h=['0-5', '5-15', '15-25', '25-50'],
        best_4h_bin="50-75",
        best_4h_t_score=3.09,
        ease_rating=6,
        is_mean_reverter=False,
        is_momentum=True,
        volatility_level="Low",
        entry_guidance="Standard entry rules apply",
        avoid_guidance="Avoid weak signal zones",
        special_notes="Trade based on t-score strength"
    ),
    "WMT": StockMetadata(
        ticker="WMT",
        name="Walmart Inc.",
        personality="Momentum Trending",
        reliability_4h="High",
        reliability_daily="High",
        tradeable_4h_zones=['50-75', '85-95', '95-100'],
        dead_zones_4h=['5-15', '15-25', '25-50'],
        best_4h_bin="50-75",
        best_4h_t_score=4.99,
        ease_rating=8,
        is_mean_reverter=False,
        is_momentum=True,
        volatility_level="Medium",
        entry_guidance="Standard entry rules apply",
        avoid_guidance="Avoid weak signal zones",
        special_notes="Trade based on t-score strength"
    ),
    "UNH": StockMetadata(
        ticker="UNH",
        name="UnitedHealth Group Inc.",
        personality="Momentum Trending",
        reliability_4h="Medium",
        reliability_daily="Low",
        tradeable_4h_zones=['85-95', '95-100'],
        dead_zones_4h=['5-15', '50-75', '75-85'],
        best_4h_bin="95-100",
        best_4h_t_score=2.66,
        ease_rating=3,
        is_mean_reverter=False,
        is_momentum=True,
        volatility_level="High",
        entry_guidance="Standard entry rules apply",
        avoid_guidance="Avoid weak signal zones",
        special_notes="Trade based on t-score strength"
    ),
    "AVGO": StockMetadata(
        ticker="AVGO",
        name="Broadcom Inc.",
        personality="Momentum Trending",
        reliability_4h="High",
        reliability_daily="High",
        tradeable_4h_zones=['0-5', '50-75', '75-85'],
        dead_zones_4h=['5-15', '15-25', '25-50'],
        best_4h_bin="50-75",
        best_4h_t_score=4.96,
        ease_rating=10,
        is_mean_reverter=False,
        is_momentum=True,
        volatility_level="High",
        entry_guidance="Standard entry rules apply",
        avoid_guidance="Avoid weak signal zones",
        special_notes="Trade based on t-score strength"
    ),
    "LLY": StockMetadata(
        ticker="LLY",
        name="Eli Lilly and Company",
        personality="Momentum Trending",
        reliability_4h="Medium",
        reliability_daily="Medium",
        tradeable_4h_zones=['85-95', '95-100'],
        dead_zones_4h=['5-15', '15-25', '25-50'],
        best_4h_bin="95-100",
        best_4h_t_score=5.38,
        ease_rating=5,
        is_mean_reverter=False,
        is_momentum=True,
        volatility_level="High",
        entry_guidance="Standard entry rules apply",
        avoid_guidance="Avoid weak signal zones",
        special_notes="Trade based on t-score strength"
    ),
    "TSM": StockMetadata(
        ticker="TSM",
        name="Taiwan Semiconductor",
        personality="Momentum Trending",
        reliability_4h="High",
        reliability_daily="High",
        tradeable_4h_zones=['0-5', '5-15', '15-25', '50-75'],
        dead_zones_4h=['25-50', '75-85', '85-95', '95-100'],
        best_4h_bin="5-15",
        best_4h_t_score=3.69,
        ease_rating=9,
        is_mean_reverter=False,
        is_momentum=True,
        volatility_level="High",
        entry_guidance="Standard entry rules apply",
        avoid_guidance="Avoid weak signal zones",
        special_notes="Trade based on t-score strength"
    ),
    "ORCL": StockMetadata(
        ticker="ORCL",
        name="Oracle Corporation",
        personality="Momentum Trending",
        reliability_4h="High",
        reliability_daily="High",
        tradeable_4h_zones=['0-5', '85-95', '95-100'],
        dead_zones_4h=['5-15', '15-25', '25-50', '50-75', '75-85'],
        best_4h_bin="0-5",
        best_4h_t_score=3.81,
        ease_rating=8,
        is_mean_reverter=False,
        is_momentum=True,
        volatility_level="High",
        entry_guidance="Standard entry rules apply",
        avoid_guidance="Avoid weak signal zones",
        special_notes="Trade based on t-score strength"
    ),
    "OXY": StockMetadata(
        ticker="OXY",
        name="Occidental Petroleum",
        personality="Momentum Trending",
        reliability_4h="Low",
        reliability_daily="Medium",
        tradeable_4h_zones=['25-50'],
        dead_zones_4h=['5-15', '15-25', '75-85', '85-95', '95-100'],
        best_4h_bin="25-50",
        best_4h_t_score=-2.59,
        ease_rating=4,
        is_mean_reverter=False,
        is_momentum=True,
        volatility_level="Medium",
        entry_guidance="Standard entry rules apply",
        avoid_guidance="Avoid weak signal zones",
        special_notes="Trade based on t-score strength"
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
        ("GLD", "4H"): GLD_4H_DATA,
        ("GLD", "Daily"): GLD_DAILY_DATA,
        ("SLV", "4H"): SLV_4H_DATA,
        ("SLV", "Daily"): SLV_DAILY_DATA,
        ("TSLA", "4H"): TSLA_4H_DATA,
        ("TSLA", "Daily"): TSLA_DAILY_DATA,
        ("NFLX", "4H"): NFLX_4H_DATA,
        ("NFLX", "Daily"): NFLX_DAILY_DATA,
        ("BRK-B", "4H"): BRKB_4H_DATA,
        ("BRK-B", "Daily"): BRKB_DAILY_DATA,
        ("WMT", "4H"): WMT_4H_DATA,
        ("WMT", "Daily"): WMT_DAILY_DATA,
        ("UNH", "4H"): UNH_4H_DATA,
        ("UNH", "Daily"): UNH_DAILY_DATA,
        ("AVGO", "4H"): AVGO_4H_DATA,
        ("AVGO", "Daily"): AVGO_DAILY_DATA,
        ("LLY", "4H"): LLY_4H_DATA,
        ("LLY", "Daily"): LLY_DAILY_DATA,
        ("TSM", "4H"): TSM_4H_DATA,
        ("TSM", "Daily"): TSM_DAILY_DATA,
        ("ORCL", "4H"): ORCL_4H_DATA,
        ("ORCL", "Daily"): ORCL_DAILY_DATA,
        ("OXY", "4H"): OXY_4H_DATA,
        ("OXY", "Daily"): OXY_DAILY_DATA,
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

# ============================================
# UnitedHealth Group Inc. (UNH) DATA
# ============================================

UNH_4H_DATA = {
    "0-5": BinStatistics("0-5%", -1.05, -1.29, 5.0, 63, 0.63, -1.67, -7.42, 4.49, 3.29, -3.55),
    "5-15": BinStatistics("5-15%", -0.27, 0.09, 4.0, 118, 0.37, -0.73, -7.29, 4.52, 2.43, -3.06),
    "15-25": BinStatistics("15-25%", 0.61, 0.28, 3.47, 125, 0.31, 1.96, -4.62, 7.21, 2.58, -1.9),
    "25-50": BinStatistics("25-50%", -0.57, 0.07, 4.97, 283, 0.3, -1.92, -6.27, 4.48, 2.2, -3.48),
    "50-75": BinStatistics("50-75%", -0.34, 0.34, 4.75, 304, 0.27, -1.24, -6.93, 4.59, 2.04, -3.44),
    "75-85": BinStatistics("75-85%", -0.16, 0.18, 3.78, 117, 0.35, -0.45, -6.37, 4.48, 2.1, -2.88),
    "85-95": BinStatistics("85-95%", 0.84, 0.25, 4.34, 122, 0.39, 2.13, -5.53, 9.36, 3.55, -2.36),
    "95-100": BinStatistics("95-100%", 2.01, 0.06, 5.69, 57, 0.75, 2.66, -4.31, 13.76, 5.85, -1.98),
}

UNH_DAILY_DATA = {
    "0-5": BinStatistics("0-5%", -0.34, 0.1, 4.11, 44, 0.62, -0.55, -6.51, 4.97, 2.73, -3.7),
    "5-15": BinStatistics("5-15%", 0.66, 1.38, 5.25, 70, 0.63, 1.05, -6.83, 10.67, 3.81, -4.06),
    "15-25": BinStatistics("15-25%", 0.22, 0.79, 4.77, 78, 0.54, 0.41, -7.11, 6.59, 3.08, -3.89),
    "25-50": BinStatistics("25-50%", -0.77, -0.08, 5.97, 219, 0.4, -1.91, -11.55, 6.3, 3.05, -4.42),
    "50-75": BinStatistics("50-75%", 0.66, 0.56, 6.23, 213, 0.43, 1.54, -7.61, 12.14, 4.45, -4.06),
    "75-85": BinStatistics("75-85%", -0.37, 0.42, 5.5, 82, 0.61, -0.6, -7.52, 5.92, 2.91, -4.55),
    "85-95": BinStatistics("85-95%", 0.46, 0.3, 4.69, 83, 0.51, 0.9, -7.08, 8.59, 3.16, -3.42),
    "95-100": BinStatistics("95-100%", -2.92, -1.56, 7.97, 40, 1.26, -2.31, -26.56, 3.84, 2.35, -5.75),
}

# ============================================
# Broadcom Inc. (AVGO) DATA
# ============================================

AVGO_4H_DATA = {
    "0-5": BinStatistics("0-5%", 1.63, 1.14, 5.45, 54, 0.74, 2.19, -4.55, 9.87, 4.55, -2.96),
    "5-15": BinStatistics("5-15%", 0.58, 0.35, 5.05, 127, 0.45, 1.3, -6.1, 7.93, 4.35, -3.37),
    "15-25": BinStatistics("15-25%", -0.21, -0.28, 4.32, 119, 0.4, -0.54, -5.83, 7.71, 3.22, -3.06),
    "25-50": BinStatistics("25-50%", 0.47, 0.08, 5.54, 295, 0.32, 1.44, -7.49, 10.2, 4.58, -3.73),
    "50-75": BinStatistics("50-75%", 1.71, 1.36, 6.14, 317, 0.34, 4.96, -6.81, 11.99, 4.93, -3.43),
    "75-85": BinStatistics("75-85%", 1.17, 0.48, 5.77, 111, 0.55, 2.14, -6.79, 10.02, 4.63, -3.22),
    "85-95": BinStatistics("85-95%", 1.27, 0.29, 7.11, 115, 0.66, 1.91, -7.28, 8.05, 5.26, -3.09),
    "95-100": BinStatistics("95-100%", 1.42, 2.18, 5.3, 53, 0.73, 1.95, -6.07, 8.55, 4.89, -3.47),
}

AVGO_DAILY_DATA = {
    "0-5": BinStatistics("0-5%", 5.03, 4.65, 8.75, 38, 1.42, 3.54, -8.0, 21.35, 8.86, -5.68),
    "5-15": BinStatistics("5-15%", 3.04, 2.57, 6.28, 78, 0.71, 4.27, -5.16, 14.88, 6.02, -3.66),
    "15-25": BinStatistics("15-25%", 3.0, 3.04, 6.09, 86, 0.66, 4.57, -6.93, 10.96, 5.76, -4.12),
    "25-50": BinStatistics("25-50%", 0.88, 0.77, 6.37, 216, 0.43, 2.03, -9.02, 11.21, 5.25, -4.39),
    "50-75": BinStatistics("50-75%", 1.42, 0.79, 7.27, 218, 0.49, 2.88, -9.5, 13.26, 5.92, -4.63),
    "75-85": BinStatistics("75-85%", 2.61, 1.1, 6.99, 72, 0.82, 3.17, -7.25, 15.35, 6.64, -3.72),
    "85-95": BinStatistics("85-95%", 3.03, 0.93, 9.88, 82, 1.09, 2.78, -8.08, 23.46, 9.35, -3.93),
    "95-100": BinStatistics("95-100%", 1.47, 1.42, 7.91, 40, 1.25, 1.17, -10.25, 8.88, 5.32, -4.96),
}

# ============================================
# Eli Lilly and Company (LLY) DATA
# ============================================

LLY_4H_DATA = {
    "0-5": BinStatistics("0-5%", -0.72, -0.91, 3.47, 58, 0.46, -1.58, -5.21, 3.99, 2.61, -2.91),
    "5-15": BinStatistics("5-15%", 0.11, 0.29, 3.51, 132, 0.31, 0.36, -6.15, 4.71, 2.48, -2.82),
    "15-25": BinStatistics("15-25%", -0.25, -0.23, 4.51, 110, 0.43, -0.59, -8.6, 6.28, 3.06, -3.22),
    "25-50": BinStatistics("25-50%", 0.36, 0.28, 4.82, 299, 0.28, 1.29, -7.11, 7.96, 3.24, -3.14),
    "50-75": BinStatistics("50-75%", 0.36, 0.49, 4.06, 302, 0.23, 1.55, -6.4, 7.17, 2.88, -2.88),
    "75-85": BinStatistics("75-85%", 0.71, 0.87, 4.3, 119, 0.39, 1.8, -5.42, 6.89, 3.45, -3.49),
    "85-95": BinStatistics("85-95%", 1.38, 1.31, 3.42, 114, 0.32, 4.3, -4.03, 6.52, 3.27, -1.98),
    "95-100": BinStatistics("95-100%", 2.73, 2.52, 3.83, 57, 0.51, 5.38, -3.41, 9.66, 3.82, -2.39),
}

LLY_DAILY_DATA = {
    "0-5": BinStatistics("0-5%", 0.99, 1.81, 5.67, 43, 0.87, 1.14, -6.98, 9.04, 4.87, -4.4),
    "5-15": BinStatistics("5-15%", 3.55, 2.67, 6.91, 66, 0.85, 4.18, -6.19, 15.4, 6.32, -4.42),
    "15-25": BinStatistics("15-25%", 1.58, 0.63, 6.76, 94, 0.7, 2.27, -6.24, 15.36, 5.76, -3.82),
    "25-50": BinStatistics("25-50%", 0.32, 0.59, 5.5, 222, 0.37, 0.87, -9.63, 9.29, 3.87, -4.09),
    "50-75": BinStatistics("50-75%", 0.61, -0.11, 5.55, 202, 0.39, 1.55, -7.74, 10.94, 5.09, -3.53),
    "75-85": BinStatistics("75-85%", 1.15, 1.76, 5.36, 94, 0.55, 2.08, -7.72, 9.21, 4.03, -4.7),
    "85-95": BinStatistics("85-95%", 0.68, 1.16, 4.67, 76, 0.54, 1.26, -5.92, 7.67, 3.97, -3.61),
    "95-100": BinStatistics("95-100%", 1.27, 1.7, 4.0, 37, 0.66, 1.93, -5.52, 7.47, 3.7, -3.22),
}

# ============================================
# Taiwan Semiconductor (TSM) DATA
# ============================================

TSM_4H_DATA = {
    "0-5": BinStatistics("0-5%", 1.56, 1.81, 3.52, 60, 0.45, 3.44, -3.45, 6.95, 3.61, -2.23),
    "5-15": BinStatistics("5-15%", 1.42, 1.59, 4.17, 118, 0.38, 3.69, -5.31, 7.75, 4.19, -2.48),
    "15-25": BinStatistics("15-25%", 1.1, 0.74, 4.26, 128, 0.38, 2.91, -4.85, 8.05, 3.92, -2.77),
    "25-50": BinStatistics("25-50%", 0.34, -0.18, 4.3, 287, 0.25, 1.33, -5.78, 8.18, 3.78, -3.03),
    "50-75": BinStatistics("50-75%", 0.88, 0.67, 4.53, 305, 0.26, 3.4, -5.88, 8.94, 3.96, -3.09),
    "75-85": BinStatistics("75-85%", -0.16, 0.31, 4.35, 127, 0.39, -0.42, -8.59, 5.67, 2.94, -3.73),
    "85-95": BinStatistics("85-95%", 0.4, 0.38, 3.45, 117, 0.32, 1.24, -5.86, 6.11, 2.65, -2.52),
    "95-100": BinStatistics("95-100%", 0.28, 0.35, 4.26, 46, 0.63, 0.44, -5.39, 5.62, 3.28, -3.0),
}

TSM_DAILY_DATA = {
    "0-5": BinStatistics("0-5%", 0.37, 1.07, 4.91, 41, 0.77, 0.48, -7.14, 7.55, 3.84, -4.53),
    "5-15": BinStatistics("5-15%", 2.26, 1.46, 5.37, 73, 0.63, 3.6, -4.59, 13.34, 5.49, -2.65),
    "15-25": BinStatistics("15-25%", 1.94, 1.73, 6.04, 87, 0.65, 2.99, -6.09, 11.96, 5.7, -3.65),
    "25-50": BinStatistics("25-50%", 0.39, -0.45, 6.0, 219, 0.41, 0.96, -8.69, 11.47, 5.43, -4.25),
    "50-75": BinStatistics("50-75%", 1.31, 1.23, 5.96, 206, 0.42, 3.15, -6.99, 10.98, 5.04, -4.11),
    "75-85": BinStatistics("75-85%", 1.24, 0.71, 5.47, 88, 0.58, 2.12, -6.53, 9.0, 5.2, -3.51),
    "85-95": BinStatistics("85-95%", 1.16, 1.17, 5.32, 72, 0.63, 1.86, -6.79, 9.44, 4.63, -3.42),
    "95-100": BinStatistics("95-100%", 4.14, 1.81, 9.31, 46, 1.37, 3.02, -7.61, 26.26, 8.88, -3.94),
}

# ============================================
# Oracle Corporation (ORCL) DATA
# ============================================

ORCL_4H_DATA = {
    "0-5": BinStatistics("0-5%", 1.82, 1.68, 3.35, 49, 0.48, 3.81, -2.51, 7.78, 3.33, -1.94),
    "5-15": BinStatistics("5-15%", 0.41, 0.38, 3.55, 121, 0.32, 1.27, -4.77, 5.98, 3.0, -2.49),
    "15-25": BinStatistics("15-25%", 0.05, -0.08, 3.83, 129, 0.34, 0.14, -5.95, 5.22, 2.97, -2.7),
    "25-50": BinStatistics("25-50%", 0.35, -0.01, 4.99, 304, 0.29, 1.22, -6.09, 7.26, 3.45, -2.75),
    "50-75": BinStatistics("50-75%", 0.37, 0.08, 4.87, 296, 0.28, 1.3, -7.13, 9.81, 3.71, -3.07),
    "75-85": BinStatistics("75-85%", 0.22, 0.81, 5.49, 116, 0.51, 0.43, -10.14, 11.06, 3.68, -4.35),
    "85-95": BinStatistics("85-95%", 2.05, 1.23, 7.26, 117, 0.67, 3.05, -5.3, 12.47, 5.0, -2.67),
    "95-100": BinStatistics("95-100%", 2.97, 2.44, 7.97, 57, 1.06, 2.82, -11.37, 17.98, 6.08, -4.33),
}

ORCL_DAILY_DATA = {
    "0-5": BinStatistics("0-5%", -0.1, 0.52, 5.52, 44, 0.83, -0.12, -9.61, 6.29, 3.99, -5.02),
    "5-15": BinStatistics("5-15%", 2.52, 0.74, 8.92, 77, 1.02, 2.48, -5.75, 19.62, 6.75, -3.11),
    "15-25": BinStatistics("15-25%", 0.01, -0.6, 6.49, 85, 0.7, 0.02, -7.18, 8.56, 4.8, -3.67),
    "25-50": BinStatistics("25-50%", 0.5, 0.09, 5.43, 203, 0.38, 1.31, -7.93, 9.4, 4.47, -3.6),
    "50-75": BinStatistics("50-75%", 2.16, 1.43, 6.85, 213, 0.47, 4.59, -7.35, 14.38, 5.93, -4.12),
    "75-85": BinStatistics("75-85%", 1.74, 1.45, 7.43, 90, 0.78, 2.23, -10.29, 15.27, 5.73, -5.48),
    "85-95": BinStatistics("85-95%", 1.81, 1.45, 5.88, 73, 0.69, 2.63, -7.6, 10.98, 4.29, -4.33),
    "95-100": BinStatistics("95-100%", 2.37, 2.46, 5.07, 48, 0.73, 3.25, -6.05, 11.77, 4.81, -3.55),
}

# ============================================
# Occidental Petroleum (OXY) DATA
# ============================================

OXY_4H_DATA = {
    "0-5": BinStatistics("0-5%", -1.12, -0.18, 4.85, 59, 0.63, -1.77, -8.14, 6.05, 2.09, -3.65),
    "5-15": BinStatistics("5-15%", -0.08, -0.32, 2.83, 115, 0.26, -0.29, -4.43, 4.68, 2.28, -2.17),
    "15-25": BinStatistics("15-25%", -0.11, 0.26, 2.9, 122, 0.26, -0.41, -4.73, 5.03, 2.19, -2.56),
    "25-50": BinStatistics("25-50%", -0.6, -0.42, 4.03, 301, 0.23, -2.59, -6.43, 4.85, 2.48, -3.1),
    "50-75": BinStatistics("50-75%", 0.3, 0.45, 3.22, 300, 0.19, 1.6, -4.96, 4.96, 2.54, -2.44),
    "75-85": BinStatistics("75-85%", 0.02, 0.31, 3.38, 115, 0.31, 0.07, -6.18, 5.16, 2.53, -2.81),
    "85-95": BinStatistics("85-95%", -0.15, -0.53, 2.75, 110, 0.26, -0.59, -4.32, 4.1, 2.34, -2.23),
    "95-100": BinStatistics("95-100%", -0.06, 0.27, 3.29, 67, 0.4, -0.14, -5.41, 5.12, 2.36, -2.87),
}

OXY_DAILY_DATA = {
    "0-5": BinStatistics("0-5%", 2.26, 2.13, 5.74, 40, 0.91, 2.49, -4.23, 12.01, 5.91, -2.67),
    "5-15": BinStatistics("5-15%", 0.31, -0.4, 4.15, 91, 0.43, 0.72, -4.69, 6.64, 3.86, -2.47),
    "15-25": BinStatistics("15-25%", -0.7, -1.18, 4.95, 78, 0.56, -1.25, -8.01, 7.65, 4.41, -3.89),
    "25-50": BinStatistics("25-50%", 0.37, -0.2, 4.87, 199, 0.35, 1.06, -6.32, 8.1, 4.28, -3.39),
    "50-75": BinStatistics("50-75%", 0.26, 0.63, 5.82, 215, 0.4, 0.65, -7.63, 8.53, 4.18, -4.43),
    "75-85": BinStatistics("75-85%", -1.36, -1.55, 4.4, 88, 0.47, -2.91, -7.54, 5.13, 2.83, -4.27),
    "85-95": BinStatistics("85-95%", -1.76, -1.42, 5.05, 81, 0.56, -3.14, -8.26, 4.56, 3.06, -4.75),
    "95-100": BinStatistics("95-100%", -0.96, -0.53, 3.89, 42, 0.6, -1.6, -8.31, 4.55, 2.39, -3.48),
}

