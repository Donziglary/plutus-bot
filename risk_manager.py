# risk_manager.py
import numpy as np

def calculate_position_size(balance, atr, price, risk_pct=0.03, max_leverage=15):
    """
    Dynamically calculates position size and leverage based on fixed account risk 
    and market volatility (ATR).
    """
    if atr == 0 or price == 0:
        return 0.0, 1.0
    
    risk_amount = balance * risk_pct
    sl_pct = (atr * 1.5) / price
    
    if sl_pct == 0:
        return 0.0, 1.0
        
    position_size_usd = risk_amount / sl_pct
    required_leverage = position_size_usd / balance
    
    if required_leverage > max_leverage:
        required_leverage = float(max_leverage)
        position_size_usd = balance * max_leverage
        
    return float(position_size_usd), float(required_leverage)