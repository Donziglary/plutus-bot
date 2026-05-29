# config.py
# --- V8: THE SQUEEZE SNIPER (MTF & Volatility Compression) ---
SYMBOL = "SOLUSDT"         
TIMEFRAME = "15m"          # تایم فریم طلایی برای فرار از نویز
DATA_LIMIT = 1500

# --- RISK MANAGEMENT ---
INITIAL_BALANCE = 10000.0
ACCOUNT_RISK_PER_TRADE = 0.03  
MAX_LEVERAGE = 15          # لوریج کنترل‌شده برای تایم فریم بالاتر

# --- REALISTIC EXECUTION SIMULATION ---
TAKER_FEE = 0.0004     
SLIPPAGE_PCT = 0.0010  

# --- MACRO TREND FILTER ---
EMA_MACRO_PERIOD = 200     # در چارت 15 دقیقه، این معادل EMA 50 یک ساعته است (فیلتر جهت کلان)

# --- THE SQUEEZE PARAMS (Bollinger vs Keltner) ---
BB_PERIOD = 20
BB_STD = 2.0               # باند بولینگر استاندارد

KC_PERIOD = 20
KC_MULT = 1.5              # کانال کلتنر (اگر بولینگر بیاید داخل این، بازار فشرده است)

# --- MOMENTUM & VOLUME CONFIRMATION ---
RSI_PERIOD = 14            
VOLUME_PERIOD = 20
VOLUME_MULT = 1.3          # تایید ورود پول در لحظه شکست فشردگی

# --- ASYMMETRIC REWARD MATH ---
ATR_PERIOD = 14
ATR_SL_MULTIPLIER = 1.5    # استاپ بسیار تنگ (اگر فنر فیک باز شد، سریع خارج می‌شویم)
ATR_TP_MULTIPLIER = 3.5    # تارگت بسیار بزرگ (شکار کل روند انفجاری - نسبت 1 به 2.3)