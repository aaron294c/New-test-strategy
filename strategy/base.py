import pandas as pd
import numpy as np
from abc import ABC, abstractmethod

class BaseStrategy(ABC):
    def __init__(self, lookback_window=252):
        self.lookback_window = lookback_window
        
    @abstractmethod
    def generate_signals(self, data: pd.DataFrame) -> pd.DataFrame:
        """Generate trading signals based on strategy rules"""
        pass
    
    @abstractmethod
    def calculate_metrics(self, data: pd.DataFrame) -> dict:
        """Calculate strategy performance metrics"""
        pass
    
    def calculate_expectancy(self, returns: pd.Series) -> tuple:
        """Calculate win rate, avg gain/loss, and expectancy"""
        wins = returns[returns > 0]
        losses = returns[returns < 0]
        
        win_rate = len(wins) / len(returns)
        avg_gain = wins.mean() if len(wins) > 0 else 0
        avg_loss = abs(losses.mean()) if len(losses) > 0 else 0
        expectancy = (win_rate * avg_gain) - ((1 - win_rate) * avg_loss)
        
        return win_rate, avg_gain, avg_loss, expectancy
