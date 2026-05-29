# strategy.py
import pandas as pd
import pandas_ta as ta
import numpy as np
import config


def calculate_indicators(df: pd.DataFrame) -> pd.DataFrame:
    """Calculates Regime and Smart Breakout Indicators."""
    df.columns = [col.lower() for col in df.columns]

    # 1. Macro Filters
    df["ema_macro"] = df.ta.ema(length=config.EMA_MACRO_PERIOD)
    df.ta.adx(length=config.ADX_PERIOD, append=True)

    # Extract ADX column dynamically
    col_adx = [c for c in df.columns if "adx" in c.lower()][0]
    df["adx_val"] = df[col_adx]

    # 2. Bollinger Bands
    bb = df.ta.bbands(length=config.BB_PERIOD, std=config.BB_STD)
    col_bbl = [c for c in bb.columns if "bbl" in c.lower()][0]
    col_bbu = [c for c in bb.columns if "bbu" in c.lower()][0]
    df["bbl"] = bb[col_bbl]
    df["bbu"] = bb[col_bbu]

    # 3. Momentum & Volume
    df["rsi"] = df.ta.rsi(length=config.RSI_PERIOD)
    df["vol_sma"] = df["volume"].rolling(window=config.VOLUME_PERIOD).mean()

    # 4. Volatility
    df["atr"] = df.ta.atr(length=config.ATR_PERIOD)

    df.dropna(inplace=True)
    return df


def generate_signals(df: pd.DataFrame) -> pd.DataFrame:
    """Smart Breakout Logic with Fakeout Protection."""
    close = df["close"]
    open_p = df["open"]
    high = df["high"]
    low = df["low"]

    bbl = df["bbl"]
    bbu = df["bbu"]
    rsi = df["rsi"]
    volume = df["volume"]
    vol_sma = df["vol_sma"]
    atr = df["atr"]

    ema = df["ema_macro"]
    adx = df["adx_val"]

    df["signal"] = 0
    df["strategy_type"] = "None"

    # --- FAKEOUT PROTECTION (Candle Structure) ---
    # Ensure the breakout candle has a strong body and closes near its extreme
    candle_range = high - low
    # Avoid zero division
    candle_range = candle_range.replace(0, 0.00001)

    bullish_close_pct = (close - low) / candle_range
    bearish_close_pct = (high - close) / candle_range

    # A strong breakout candle should close in the upper 30% of its range (for longs)
    strong_bull_candle = bullish_close_pct > 0.70
    strong_bear_candle = bearish_close_pct > 0.70

    # --- REGIME FILTERS ---
    trending_market = adx > config.ADX_MIN_TREND
    uptrend = close > ema
    downtrend = close < ema

    volume_surge = volume > (vol_sma * config.VOLUME_MULT)

    # --- THE SMART ENTRY LOGIC ---
    # Long: Market trending up, strong body closes above upper band, volume supports it
    long_cond = (
        trending_market
        & uptrend
        & (close > bbu)
        & (rsi > config.RSI_BULL_CONFIRM)
        & volume_surge
        & strong_bull_candle
    )

    # Short: Market trending down, strong body closes below lower band, volume supports it
    short_cond = (
        trending_market
        & downtrend
        & (close < bbl)
        & (rsi < config.RSI_BEAR_CONFIRM)
        & volume_surge
        & strong_bear_candle
    )

    # Apply Signals
    df.loc[long_cond, "signal"] = 1
    df.loc[long_cond, "strategy_type"] = "Smart_BO_Long"

    df.loc[short_cond, "signal"] = -1
    df.loc[short_cond, "strategy_type"] = "Smart_BO_Short"

    # Mathematical Stops
    df["sl_distance_price"] = atr * config.ATR_SL_MULTIPLIER
    df["tp_distance_price"] = atr * config.ATR_TP_MULTIPLIER

    return df


def process_market(df: pd.DataFrame) -> pd.DataFrame:
    df = calculate_indicators(df)
    return generate_signals(df)
