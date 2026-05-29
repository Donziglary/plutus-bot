#!/usr/bin/env python3
"""
Strategy module containing technical indicator calculations and signal generation logic.
Fully integrated with the object-oriented configuration dataclasses.
"""

from __future__ import annotations

import logging
from typing import Optional
import pandas as pd
import numpy as np

from config import StrategyConfig, TradingConfig

# Setup module logger
logger = logging.getLogger(__name__)

def generate_signals(df: pd.DataFrame, config: Optional[StrategyConfig] = None) -> pd.DataFrame:
    """
    Calculates technical indicators (EMA, RSI, Volume MA, ATR) and generates
    trading signals based on the strategy rules.
    
    Args:
        df: A pandas DataFrame with datetime index and columns: open, high, low, close, volume
        config: Optional StrategyConfig instance. If None, default is used.
        
    Returns:
        The DataFrame with added indicator and signal columns.
    """
    if df.empty:
        return df
        
    cfg = config or StrategyConfig()
    t_cfg = TradingConfig()
    
    try:
        # Copy to avoid setting with copy warning
        df = df.copy()
        
        # 1. EMA Calculations
        df["ema_fast"] = df["close"].ewm(span=cfg.ema_fast, adjust=False).mean()
        df["ema_slow"] = df["close"].ewm(span=cfg.ema_slow, adjust=False).mean()
        
        # 2. RSI Calculation (Native pandas implementation for maximum robustness)
        delta = df["close"].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=cfg.rsi_period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=cfg.rsi_period).mean()
        rs = gain / (loss + 1e-10)
        df["rsi"] = 100 - (100 / (1 + rs))
        
        # 3. Volume MA Calculation
        df["volume_ma"] = df["volume"].rolling(window=cfg.volume_ma_period).mean()
        
        # 4. ATR Calculation (True Range and Average True Range)
        high_low = df["high"] - df["low"]
        high_close_prev = (df["high"] - df["close"].shift(1)).abs()
        low_close_prev = (df["low"] - df["close"].shift(1)).abs()
        
        tr = pd.concat([high_low, high_close_prev, low_close_prev], axis=1).max(axis=1)
        df["atr"] = tr.rolling(window=t_cfg.atr_period).mean()
        
        # 5. Signal Generation Logic
        # Long Signal: Fast EMA > Slow EMA & Close > Slow EMA & RSI < Overbought & Volume > Volume MA
        df["signal_long"] = (
            (df["close"] > df["ema_slow"]) & 
            (df["ema_fast"] > df["ema_slow"]) & 
            (df["rsi"] < cfg.rsi_overbought) & 
            (df["volume"] > df["volume_ma"])
        )
        
        # Short Signal: Fast EMA < Slow EMA & Close < Slow EMA & RSI > Oversold & Volume > Volume MA
        df["signal_short"] = (
            (df["close"] < df["ema_slow"]) & 
            (df["ema_fast"] < df["ema_slow"]) & 
            (df["rsi"] > cfg.rsi_oversold) & 
            (df["volume"] > df["volume_ma"])
        )
        
        return df
        
    except Exception as e:
        logger.error("Error generating strategy signals: %s", e)
        # Ensure fallback columns exist so main.py doesn't crash on KeyError
        if "signal_long" not in df.columns:
            df["signal_long"] = False
        if "signal_short" not in df.columns:
            df["signal_short"] = False
        if "atr" not in df.columns:
            df["atr"] = 0.0
        return df

def compute_atr_stop(entry_price: float, atr_value: float, side: str, trading_cfg: Optional[TradingConfig] = None) -> float:
    """
    Computes the absolute stop-loss price level based on entry price, ATR, and multiplier.
    
    Args:
        entry_price: The execution price of the position entry.
        atr_value: The current ATR indicator value.
        side: Position direction, either 'LONG' or 'SHORT'.
        trading_cfg: Optional TradingConfig instance for the ATR multiplier.
        
    Returns:
        The calculated absolute stop-loss price.
    """
    cfg = trading_cfg or TradingConfig()
    multiplier = cfg.atr_multiplier_sl
    
    if side.upper() == "LONG":
        return entry_price - (atr_value * multiplier)
    elif side.upper() == "SHORT":
        return entry_price + (atr_value * multiplier)
    else:
        logger.warning("Invalid position side '%s' passed to compute_atr_stop. Falling back to entry price.", side)
        return entry_price