# backtester.py
import pandas as pd
from data_fetcher import fetch_real_futures_data
from strategy import process_market
import config

def calculate_position_size(balance: float, current_price: float, sl_distance_price: float):
    """
    Professional Position Sizing Formula:
    Size = (Account * Risk%) / Distance to Stop Loss
    """
    risk_amount_usdt = balance * config.ACCOUNT_RISK_PER_TRADE
    
    # Protect against zero division
    if sl_distance_price <= 0:
        return 0.0, 0.0
        
    position_size_crypto = risk_amount_usdt / sl_distance_price
    position_value_usdt = position_size_crypto * current_price
    
    # Calculate required leverage
    required_leverage = position_value_usdt / balance
    
    # Cap the position size if it exceeds our max allowed leverage
    if required_leverage > config.MAX_LEVERAGE:
        position_value_usdt = balance * config.MAX_LEVERAGE
        position_size_crypto = position_value_usdt / current_price
        
    return position_value_usdt, required_leverage

def run_enterprise_backtest():
    print(f"🚀 Initializing Enterprise Backtest Engine v4.0...")
    df = fetch_real_futures_data()
    if df is None or df.empty: return
    
    df = process_market(df)
    
    balance = config.INITIAL_BALANCE
    max_balance = balance
    max_drawdown_pct = 0.0
    trades = []
    
    in_position = False
    pos = {}

    print("⚙️ Simulating executions with realistic slippage and fees...")
    
    for idx, row in df.iterrows():
        # Update Drawdown
        if balance > max_balance:
            max_balance = balance
        current_dd = (max_balance - balance) / max_balance * 100
        if current_dd > max_drawdown_pct:
            max_drawdown_pct = current_dd

        # --- EXIT LOGIC ---
        if in_position:
            exit_price = 0.0
            reason = ""
            
            if pos['type'] == 'Long':
                if row['low'] <= pos['sl_price']:
                    # Simulate slippage on stop loss
                    exit_price = pos['sl_price'] * (1 - config.SLIPPAGE_PCT)
                    reason = "Stop Loss"
                elif row['high'] >= pos['tp_price']:
                    exit_price = pos['tp_price']
                    reason = "Take Profit"
                    
            elif pos['type'] == 'Short':
                if row['high'] >= pos['sl_price']:
                    # Simulate slippage on stop loss
                    exit_price = pos['sl_price'] * (1 + config.SLIPPAGE_PCT)
                    reason = "Stop Loss"
                elif row['low'] <= pos['tp_price']:
                    exit_price = pos['tp_price']
                    reason = "Take Profit"

            if exit_price > 0:
                if pos['type'] == 'Long':
                    pnl_pct = (exit_price - pos['entry_price']) / pos['entry_price']
                else:
                    pnl_pct = (pos['entry_price'] - exit_price) / pos['entry_price']
                
                gross_pnl = pos['value_usdt'] * pnl_pct
                
                # Deduct fees for entry and exit
                total_fees = (pos['value_usdt'] * config.TAKER_FEE) + (pos['value_usdt'] * (1 + pnl_pct) * config.TAKER_FEE)
                net_pnl = gross_pnl - total_fees
                
                balance += net_pnl
                
                trades.append({
                    'Entry Time': pos['entry_time'],
                    'Exit Time': row['timestamp'],
                    'Type': pos['type'],
                    'Strategy': pos['strategy_name'],
                    'Leverage Used': round(pos['leverage'], 2),
                    'Entry Price': round(pos['entry_price'], 2),
                    'Exit Price': round(exit_price, 2),
                    'Reason': reason,
                    'Net PnL': round(net_pnl, 2),
                    'Balance': round(balance, 2)
                })
                in_position = False

        # --- ENTRY LOGIC ---
        if not in_position and row['signal'] != 0:
            target_price = row['close']
            sl_dist = row['sl_distance_price']
            
            value_usdt, lev = calculate_position_size(balance, target_price, sl_dist)
            
            if value_usdt > 0:
                in_position = True
                is_long = row['signal'] == 1
                
                # Apply entry slippage
                entry_price = target_price * (1 + config.SLIPPAGE_PCT) if is_long else target_price * (1 - config.SLIPPAGE_PCT)
                
                pos = {
                    'type': 'Long' if is_long else 'Short',
                    'strategy_name': row['strategy_type'],
                    'entry_time': row['timestamp'],
                    'entry_price': entry_price,
                    'sl_price': entry_price - sl_dist if is_long else entry_price + sl_dist,
                    'tp_price': entry_price + row['tp_distance_price'] if is_long else entry_price - row['tp_distance_price'],
                    'value_usdt': value_usdt,
                    'leverage': lev
                }

    # --- METRICS & REPORTING ---
    if trades:
        trades_df = pd.DataFrame(trades)
        trades_df.to_csv("enterprise_backtest.csv", index=False)
        
        wins = trades_df[trades_df['Net PnL'] > 0]
        losses = trades_df[trades_df['Net PnL'] <= 0]
        
        win_rate = (len(wins) / len(trades_df)) * 100
        gross_profit = wins['Net PnL'].sum()
        gross_loss = abs(losses['Net PnL'].sum())
        profit_factor = gross_profit / gross_loss if gross_loss != 0 else float('inf')
        
        print("\n" + "="*40)
        print(" INSTITUTIONAL BACKTEST METRICS ")
        print("="*40)
        print(f"Total Trades Executed: {len(trades_df)}")
        print(f"Win Rate:              {win_rate:.2f}%")
        print(f"Profit Factor:         {profit_factor:.2f} (Target > 1.5)")
        print(f"Max Drawdown:          {max_drawdown_pct:.2f}% (Target < 20%)")
        print(f"Starting Balance:      ${config.INITIAL_BALANCE:,.2f}")
        print(f"Final Balance:         ${balance:,.2f}")
        print(f"Total Net Return:      {((balance - config.INITIAL_BALANCE) / config.INITIAL_BALANCE) * 100:.2f}%")
        print("="*40)
        print("📂 Results saved to: enterprise_backtest.csv")
    else:
        print("\n⚠️ No trades were executed. The system is waiting for high-probability setups.")

if __name__ == "__main__":
    run_enterprise_backtest()