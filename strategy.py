# strategy.py
import pandas as pd
import pandas_ta as ta
import config

def calculate_indicators(df: pd.DataFrame) -> pd.DataFrame:
    """Calculates Multi-Timeframe Trend and Volatility Squeeze Indicators."""
    df.columns = [col.lower() for col in df.columns]
    
    # 1. Macro Trend Filter (15m EMA 200 ~= 1H EMA 50)
    df['ema_macro'] = df.ta.ema(length=config.EMA_MACRO_PERIOD)
    
    # 2. Bollinger Bands (Short-term Volatility)
    bb = df.ta.bbands(length=config.BB_PERIOD, std=config.BB_STD)
    col_bbl = [c for c in bb.columns if 'bbl' in c.lower()][0]
    col_bbu = [c for c in bb.columns if 'bbu' in c.lower()][0]
    df['bbl'] = bb[col_bbl]
    df['bbu'] = bb[col_bbu]
    
    # 3. Keltner Channels (Average True Range Volatility)
    kc = df.ta.kc(length=config.KC_PERIOD, scalar=config.KC_MULT)
    col_kcl = [c for c in kc.columns if 'kcl' in c.lower()][0]
    col_kcu = [c for c in kc.columns if 'kcu' in c.lower()][0]
    df['kcl'] = kc[col_kcl]
    df['kcu'] = kc[col_kcu]
    
    # 4. Momentum & Confirmation
    df['rsi'] = df.ta.rsi(length=config.RSI_PERIOD)
    df['vol_sma'] = df['volume'].rolling(window=config.VOLUME_PERIOD).mean()
    df['atr'] = df.ta.atr(length=config.ATR_PERIOD)
    
    df.dropna(inplace=True)
    return df

def generate_signals(df: pd.DataFrame) -> pd.DataFrame:
    """TTM Squeeze Breakout Logic with Macro Trend Alignment."""
    close = df['close']
    bbl, bbu = df['bbl'], df['bbu']
    kcl, kcu = df['kcl'], df['kcu']
    rsi = df['rsi']
    volume, vol_sma = df['volume'], df['vol_sma']
    atr, ema = df['atr'], df['ema_macro']

    df['signal'] = 0
    df['strategy_type'] = 'None'

    # --- THE SQUEEZE DETECTOR ---
    # Squeeze is ON when Bollinger Bands are completely INSIDE Keltner Channels
    df['squeeze_on'] = (bbu < kcu) & (bbl > kcl)
    
    # We want to fire when Squeeze WAS on recently, but is now breaking out
    # If any of the last 3 candles had a squeeze, the spring is loaded
    squeeze_loaded = df['squeeze_on'].rolling(window=3).max() > 0

    # --- MACRO ALIGNMENT & MOMENTUM ---
    macro_uptrend = close > ema
    macro_downtrend = close < ema
    volume_surge = volume > (vol_sma * config.VOLUME_MULT)

    # --- THE SNIPER ENTRY LOGIC ---
    # Long: Macro is UP, spring is loaded, price breaks UPPER Bollinger, Volume confirms
    long_cond = macro_uptrend & squeeze_loaded & (close > bbu) & (rsi > 55) & volume_surge
    
    # Short: Macro is DOWN, spring is loaded, price breaks LOWER Bollinger, Volume confirms
    short_cond = macro_downtrend & squeeze_loaded & (close < bbl) & (rsi < 45) & volume_surge

    # Apply Signals
    df.loc[long_cond, 'signal'] = 1
    df.loc[long_cond, 'strategy_type'] = 'Squeeze_Long'
    
    df.loc[short_cond, 'signal'] = -1
    df.loc[short_cond, 'strategy_type'] = 'Squeeze_Short'

    # Asymmetric Risk Management
    df['sl_distance_price'] = atr * config.ATR_SL_MULTIPLIER
    df['tp_distance_price'] = atr * config.ATR_TP_MULTIPLIER

    return df

def process_market(df: pd.DataFrame) -> pd.DataFrame:
    df = calculate_indicators(df)
    return generate_signals(df)