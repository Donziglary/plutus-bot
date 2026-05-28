# strategy.py
import pandas as pd
import pandas_ta as ta
import config

def calculate_indicators(df: pd.DataFrame) -> pd.DataFrame:
    """Calculates EXTREME anomaly indicators."""
    df.columns = [col.lower() for col in df.columns]
    
    # Extreme Bollinger Bands (StdDev 3.0 captures 99.7% of data)
    bb = df.ta.bbands(length=config.BB_PERIOD, std=config.BB_STD)
    
    # Dynamic column extraction for Bollinger
    col_bbl = [c for c in bb.columns if 'bbl' in c.lower()][0]
    col_bbu = [c for c in bb.columns if 'bbu' in c.lower()][0]
    
    df['bbl_extreme'] = bb[col_bbl]
    df['bbu_extreme'] = bb[col_bbu]
    
    # Fast Momentum RSI
    df['rsi_fast'] = df.ta.rsi(length=config.RSI_PERIOD)
    
    # Volatility for Dynamic Stops
    df['atr'] = df.ta.atr(length=config.ATR_PERIOD)
    
    df.dropna(inplace=True)
    return df

def generate_signals(df: pd.DataFrame) -> pd.DataFrame:
    """The Rubber Band Reversion Logic."""
    close = df['close']
    bbl = df['bbl_extreme']
    bbu = df['bbu_extreme']
    rsi = df['rsi_fast']
    atr = df['atr']

    df['signal'] = 0
    df['strategy_type'] = 'None'

    # --- THE RUBBER BAND CONDITIONS ---
    # Long: Price is brutally dumped outside the 3rd StdDev AND RSI is dead (< 15)
    long_cond = (close < bbl) & (rsi < config.RSI_OS)
    
    # Short: Price pumped like crazy outside 3rd StdDev AND RSI is overheated (> 85)
    short_cond = (close > bbu) & (rsi > config.RSI_OB)

    # Apply Signals
    df.loc[long_cond, 'signal'] = 1
    df.loc[long_cond, 'strategy_type'] = 'RubberBand_Long'
    
    df.loc[short_cond, 'signal'] = -1
    df.loc[short_cond, 'strategy_type'] = 'RubberBand_Short'

    # High Win-Rate Setup: Small Target, Wide Breathable Stop
    df['sl_distance_price'] = atr * config.ATR_SL_MULTIPLIER
    df['tp_distance_price'] = atr * config.ATR_TP_MULTIPLIER

    return df

def process_market(df: pd.DataFrame) -> pd.DataFrame:
    df = calculate_indicators(df)
    return generate_signals(df)