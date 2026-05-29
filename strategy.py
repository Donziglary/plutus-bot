# strategy.py
import pandas as pd
import pandas_ta as ta
import config

def calculate_indicators(df: pd.DataFrame) -> pd.DataFrame:
    """Calculates Trend Breakout indicators."""
    df.columns = [col.lower() for col in df.columns]
    
    # Bollinger Bands
    bb = df.ta.bbands(length=config.BB_PERIOD, std=config.BB_STD)
    col_bbl = [c for c in bb.columns if 'bbl' in c.lower()][0]
    col_bbu = [c for c in bb.columns if 'bbu' in c.lower()][0]
    df['bbl_band'] = bb[col_bbl]
    df['bbu_band'] = bb[col_bbu]
    
    # RSI
    df['rsi'] = df.ta.rsi(length=config.RSI_PERIOD)
    
    # Volume SMA
    df['vol_sma'] = df['volume'].rolling(window=config.VOLUME_PERIOD).mean()
    
    # ATR
    df['atr'] = df.ta.atr(length=config.ATR_PERIOD)
    
    df.dropna(inplace=True)
    return df

def generate_signals(df: pd.DataFrame) -> pd.DataFrame:
    """Momentum Breakout Logic."""
    close = df['close']
    bbl = df['bbl_band']
    bbu = df['bbu_band']
    rsi = df['rsi']
    volume = df['volume']
    vol_sma = df['vol_sma']
    atr = df['atr']

    df['signal'] = 0
    df['strategy_type'] = 'None'

    # Volume Climax = Smart Money Footprint
    volume_surge = volume > (vol_sma * config.VOLUME_MULT)

    # --- THE HIJACKER CONDITIONS ---
    # Long: Breaking UPPER band, RSI shows strength, Volume surging
    long_cond = (close > bbu) & (rsi > config.RSI_OB) & volume_surge
    
    # Short: Breaking LOWER band, RSI shows weakness, Volume surging
    short_cond = (close < bbl) & (rsi < config.RSI_OS) & volume_surge

    # Apply Signals
    df.loc[long_cond, 'signal'] = 1
    df.loc[long_cond, 'strategy_type'] = 'Breakout_Long'
    
    df.loc[short_cond, 'signal'] = -1
    df.loc[short_cond, 'strategy_type'] = 'Breakout_Short'

    # Mathematical Stops
    df['sl_distance_price'] = atr * config.ATR_SL_MULTIPLIER
    df['tp_distance_price'] = atr * config.ATR_TP_MULTIPLIER

    return df

def process_market(df: pd.DataFrame) -> pd.DataFrame:
    df = calculate_indicators(df)
    return generate_signals(df)