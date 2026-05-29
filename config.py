# config.py
# --- AGGRESSIVE EXPERIMENTAL MODE V5 ---
SYMBOL = "SOLUSDT"         
TIMEFRAME = "5m"           
DATA_LIMIT = 1500

# --- RISK MANAGEMENT ---
INITIAL_BALANCE = 10000.0
ACCOUNT_RISK_PER_TRADE = 0.04  # افزایش ریسک به ۴ درصد برای سودهای بزرگتر
MAX_LEVERAGE = 30              

# --- REALISTIC EXECUTION SIMULATION ---
TAKER_FEE = 0.0004     
SLIPPAGE_PCT = 0.0010  

# --- VOLUMETRIC RUBBER BAND PARAMS ---
BB_PERIOD = 20
BB_STD = 2.8           # کمی بهینه‌تر برای شکار نقاط بازگشتی دقیق‌تر
RSI_PERIOD = 7         
RSI_OB = 80            
RSI_OS = 20            

VOLUME_PERIOD = 20
VOLUME_MULT = 1.8      # حجم کندل باید ۱.۸ برابر میانگین باشد (تاییدیه تزریق پول هوشمند)

# --- THE REWARD REVOLUTION (R:R 1 to 1.33) ---
ATR_PERIOD = 14
ATR_SL_MULTIPLIER = 1.5  # حد ضرر بسیار تنگ (محافظت شدید از سرمایه)
ATR_TP_MULTIPLIER = 2.0  # حد سود بزرگتر برای به دست آوردن سودهای تپل