# strategy.py
import pandas as pd
import pandas_ta as ta
import numpy as np
import config

def calculate_indicators(df: pd.DataFrame) -> pd.DataFrame:
    """Calculates MTF Trend, Squeeze, and Candle Geometry Indicators."""
    df.columns = [col.lower() for col in df.columns]
    
    # Macro Trend
    df['ema_macro'] = df.ta.ema(length=config.EMA_MACRO_PERIOD)
    
    # Squeeze Components
    bb = df.ta.bbands(length=config.BB_PERIOD, std=config.BB_STD)
    df['bbl'] = bb[f'BBL_{config.BB_PERIOD}_{config.BB_STD}.0'] if f'BBL_{config.BB_PERIOD}_{config.BB_STD}.0' in bb.columns else bb.iloc[:, 0]
    df['bbu'] = bb[f'BBU_{config.BB_PERIOD}_{config.BB_STD}.0'] if f'BBU_{config.BB_PERIOD}_{config.BB_STD}.0' in bb.columns else bb.iloc[:, 2]
    
    kc = df.ta.kc(length=config.KC_PERIOD, scalar=config.KC_MULT)
    col_kcl = [c for c in kc.columns if 'kcl' in c.lower()][0]
    col_kcu = [c for c in kc.columns if 'kcu' in c.lower()][0]
    df['kcl'] = kc[col_kcl]
    df['kcu'] = kc[col_kcu]
    
    # Momentum & Volatility
    df['rsi'] = df.ta.rsi(length=config.RSI_PERIOD)
    df['vol_sma'] = df['volume'].rolling(window=config.VOLUME_PERIOD).mean()
    df['atr'] = df.ta.atr(length=config.ATR_PERIOD)
    
    # Candle Geometry Math
    candle_range = (df['high'] - df['low']).replace(0, 0.00001)
    df['body_efficiency'] = abs(df['close'] - df['open']) / candle_range
    df['upper_wick_ratio'] = (df['high'] - df[['open', 'close']].max(axis=1)) / candle_range
    df['lower_wick_ratio'] = (df[['open', 'close']].min(axis=1) - df['low']) / candle_range
    
    df.dropna(inplace=True)
    return df

def generate_signals(df: pd.DataFrame) -> pd.DataFrame:
    """TTM Squeeze + Candle Geometry Anti-Fakeout Logic."""
    close = df['close']
    bbl, bbu = df['bbl'], df['bbu']
    kcl, kcu = df['kcl'], df['kcu']
    rsi = df['rsi']
    volume, vol_sma = df['volume'], df['vol_sma']
    atr, ema = df['atr'], df['ema_macro']

    df['signal'] = 0
    df['strategy_type'] = 'None'

    # Squeeze Detection
    df['squeeze_on'] = (bbu < kcu) & (bbl > kcl)
    squeeze_loaded = df['squeeze_on'].rolling(window=3).max() > 0

    # Flow & Surge
    macro_uptrend = close > ema
    macro_downtrend = close < ema
    volume_surge = volume > (vol_sma * config.VOLUME_MULT)

    # Geometry Filters
    strong_body = df['body_efficiency'] > config.MIN_BODY_EFFICIENCY
    no_top_rejection = df['upper_wick_ratio'] < config.MAX_WICK_RATIO
    no_bottom_rejection = df['lower_wick_ratio'] < config.MAX_WICK_RATIO

    # Entry Logic
    long_cond = (
        macro_uptrend & 
        squeeze_loaded & 
        (close > bbu) & 
        (rsi > 55) & 
        volume_surge & 
        strong_body & 
        no_top_rejection
    )
    
    short_cond = (
        macro_downtrend & 
        squeeze_loaded & 
        (close < bbl) & 
        (rsi < 45) & 
        volume_surge & 
        strong_body & 
        no_bottom_rejection
    )

    df.loc[long_cond, 'signal'] = 1
    df.loc[long_cond, 'strategy_type'] = 'Geom_Sqz_Long'
    
    df.loc[short_cond, 'signal'] = -1
    df.loc[short_cond, 'strategy_type'] = 'Geom_Sqz_Short'

    df['sl_distance_price'] = atr * config.ATR_SL_MULTIPLIER
    df['tp_distance_price'] = atr * config.ATR_TP_MULTIPLIER

    return df

def process_market(df: pd.DataFrame) -> pd.DataFrame:
    df = calculate_indicators(df)
    return generate_signals(df)