# config.py
# --- SMART CONFIRMED BREAKOUT V7 ---
SYMBOL = "SOLUSDT"
TIMEFRAME = "15m"  # Changed to 15m to reduce noise and fakeouts
DATA_LIMIT = 1500

# --- RISK MANAGEMENT ---
INITIAL_BALANCE = 10000.0
ACCOUNT_RISK_PER_TRADE = 0.03
MAX_LEVERAGE = 20  # Reduced max leverage slightly for 15m stability

# --- REALISTIC EXECUTION SIMULATION ---
TAKER_FEE = 0.0004
SLIPPAGE_PCT = 0.0010

# --- MARKET REGIME & TREND FILTERS ---
EMA_MACRO_PERIOD = 200  # Macro trend filter
ADX_PERIOD = 14
ADX_MIN_TREND = 20  # Minimum trend strength to trade

# --- BREAKOUT PARAMS ---
BB_PERIOD = 20
BB_STD = 2.0  # Standard deviation (entering earlier)

RSI_PERIOD = 14
RSI_BULL_CONFIRM = 55  # Earlier entry confirmation
RSI_BEAR_CONFIRM = 45

VOLUME_PERIOD = 20
VOLUME_MULT = 1.3  # Require 30% above average volume (not extreme climax)

# --- REWARD MATH (Optimized Expectancy) ---
ATR_PERIOD = 14
ATR_SL_MULTIPLIER = 1.8  # Stop loss wide enough to survive pullbacks
ATR_TP_MULTIPLIER = 3.0  # Take profit realistic for 15m (R:R approx 1:1.66)
