# config.py
# --- MOMENTUM HIJACKER MODE V6 ---
SYMBOL = "SOLUSDT"         
TIMEFRAME = "5m"           
DATA_LIMIT = 1500

# --- RISK MANAGEMENT ---
INITIAL_BALANCE = 10000.0
ACCOUNT_RISK_PER_TRADE = 0.03  # ریسک ۳ درصد
MAX_LEVERAGE = 30              

# --- REALISTIC EXECUTION SIMULATION ---
TAKER_FEE = 0.0004     
SLIPPAGE_PCT = 0.0010  

# --- VOLUMETRIC BREAKOUT PARAMS ---
BB_PERIOD = 20
BB_STD = 2.5           # انحراف ۲.۵ (زودتر سوار روند می‌شویم)
RSI_PERIOD = 14        # RSI استاندارد
RSI_OB = 65            # تایید مومنتوم صعودی
RSI_OS = 35            # تایید مومنتوم نزولی

VOLUME_PERIOD = 20
VOLUME_MULT = 1.8      # تایید ورود نهنگ‌ها

# --- THE TREND RIDER REWARD MATH ---
ATR_PERIOD = 14
ATR_SL_MULTIPLIER = 2.0  # استاپ بازتر (اجازه نفس کشیدن به پوزیشن)
ATR_TP_MULTIPLIER = 4.0  # تارگت عظیم (ریسک به ریوارد ۱ به ۲)