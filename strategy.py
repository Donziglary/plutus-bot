# strategy.py
import pandas as pd
import pandas_ta as ta
import config

def calculate_indicators(df: pd.DataFrame) -> pd.DataFrame:
    """Calculates EXTREME anomaly indicators with Volume Climax."""
    df.columns = [col.lower() for col in df.columns]
    
    # Extreme Bollinger Bands
    bb = df.ta.bbands(length=config.BB_PERIOD, std=config.BB_STD)
    col_bbl = [c for c in bb.columns if 'bbl' in c.lower()][0]
    col_bbu = [c for c in bb.columns if 'bbu' in c.lower()][0]
    df['bbl_extreme'] = bb[col_bbl]
    df['bbu_extreme'] = bb[col_bbu]
    
    # Fast RSI
    df['rsi_fast'] = df.ta.rsi(length=config.RSI_PERIOD)
    
    # Volume Average for Climax Detection
    df['vol_sma'] = df['volume'].rolling(window=config.VOLUME_PERIOD).mean()
    
    # Volatility for Dynamic Stops
    df['atr'] = df.ta.atr(length=config.ATR_PERIOD)
    
    df.dropna(inplace=True)
    return df

def generate_signals(df: pd.DataFrame) -> pd.DataFrame:
    """The Volumetric Rubber Band Reversion Logic."""
    close = df['close']
    bbl = df['bbl_extreme']
    bbu = df['bbu_extreme']
    rsi = df['rsi_fast']
    volume = df['volume']
    vol_sma = df['vol_sma']
    atr = df['atr']

    df['signal'] = 0
    df['strategy_type'] = 'None'

    # Condition: Volume must be an extreme anomaly (Institutional Climax)
    volume_climax = volume > (vol_sma * config.VOLUME_MULT)

    # --- THE VOLUMETRIC RUBBER BAND CONDITIONS ---
    # Long: Dumped outside BB, RSI dead, AND Volume exploded (Panic Selling Climax)
    long_cond = (close < bbl) & (rsi < config.RSI_OS) & volume_climax
    
    # Short: Pumped outside BB, RSI burning, AND Volume exploded (FOMO Buying Climax)
    short_cond = (close > bbu) & (rsi > config.RSI_OB) & volume_climax

    # Apply Signals
    df.loc[long_cond, 'signal'] = 1
    df.loc[long_cond, 'strategy_type'] = 'Vol_Climax_Long'
    
    df.loc[short_cond, 'signal'] = -1
    df.loc[short_cond, 'strategy_type'] = 'Vol_Climax_Short'

    # Mathematically Optimized Stops (Positive Expectancy)
    df['sl_distance_price'] = atr * config.ATR_SL_MULTIPLIER
    df['tp_distance_price'] = atr * config.ATR_TP_MULTIPLIER

    return df

def process_market(df: pd.DataFrame) -> pd.DataFrame:
    df = calculate_indicators(df)
    return generate_signals(df)