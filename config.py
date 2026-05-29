```python
# config.py
# --- V9: VELOCITY & GEOMETRY SNIPER ---
SYMBOL = "SOLUSDT"         
TIMEFRAME = "15m"          
DATA_LIMIT = 1500

# --- RISK MANAGEMENT ---
INITIAL_BALANCE = 10000.0
ACCOUNT_RISK_PER_TRADE = 0.03  
MAX_LEVERAGE = 15          

# --- REALISTIC EXECUTION SIMULATION ---
TAKER_FEE = 0.0004     
SLIPPAGE_PCT = 0.0010  

# --- MACRO TREND FILTER ---
EMA_MACRO_PERIOD = 200     

# --- THE SQUEEZE PARAMS ---
BB_PERIOD = 20
BB_STD = 2.0               
KC_PERIOD = 20
KC_MULT = 1.5              

# --- MOMENTUM & VOLUME ---
RSI_PERIOD = 14            
VOLUME_PERIOD = 20
VOLUME_MULT = 1.3          

# --- CANDLE GEOMETRY FILTERS (NEW) ---
# Body efficiency: the candle body must be at least 60% of the total candle range
# (indicating strong buyer/seller momentum)
MIN_BODY_EFFICIENCY = 0.60  

# Max wick ratio: the wick in the breakout direction must not exceed 25%
# (helps filter stop hunts and fake breakouts)
MAX_WICK_RATIO = 0.25      

# --- ASYMMETRIC REWARD MATH ---
ATR_PERIOD = 14
ATR_SL_MULTIPLIER = 1.5    
ATR_TP_MULTIPLIER = 3.5
```
