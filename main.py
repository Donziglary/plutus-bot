# main.py
import pandas as pd
import numpy as np
import data_fetcher
import strategy
import config
import risk_manager

def run_enterprise_backtest():
    print("=" * 50)
    print("🤖 PLUTUS QUANT TRADING ENGINE v10.0 - ACTIVE")
    print("=" * 50)
    print("🚀 Initializing Squeeze Sniper Optimization Engine...")
    
    try:
        df = data_fetcher.fetch_real_futures_data(config.SYMBOL, config.TIMEFRAME, config.DATA_LIMIT)
    except Exception as e:
        print(f"❌ Data fetch failed: {e}")
        return

    if df is None or df.empty:
        print("❌ No data returned from exchange.")
        return

    print("⚙️ Simulating executions with ADVANCED Trailing Stop & Dynamic Risk...")
    df = strategy.process_market(df)
    
    balance = config.INITIAL_BALANCE
    trades = []
    active_position = None
    
    for i in range(len(df)):
        current_time = df['timestamp'].iloc[i] 
        current_row = df.iloc[i]
        
        if active_position:
            high = current_row['high']
            low = current_row['low']
            close = current_row['close']
            
            if active_position['type'] == 'Long':
                # Update highest price for Trailing Stop
                if close > active_position['highest_price']:
                    active_position['highest_price'] = close
                    # Live trailing stop logic
                    new_sl = close - (current_row['atr'] * 1.5)
                    if new_sl > active_position['sl']:
                        active_position['sl'] = new_sl
                
                # Check Stop Loss / Trailing Stop
                if low <= active_position['sl']:
                    pnl = ((active_position['sl'] - active_position['entry_price']) / active_position['entry_price']) * active_position['size']
                    pnl -= active_position['size'] * (config.TAKER_FEE + config.SLIPPAGE_PCT)
                    balance += pnl
                    trades.append({
                        'Entry Time': active_position['entry_time'], 'Exit Time': current_time,
                        'Type': 'Long', 'Entry Price': active_position['entry_price'],
                        'Exit Price': active_position['sl'], 'Reason': 'Trailing SL/Stop Loss', 
                        'Net PnL': pnl, 'Balance': balance
                    })
                    active_position = None
                    
                # Check Take Profit
                elif high >= active_position['tp']:
                    pnl = ((active_position['tp'] - active_position['entry_price']) / active_position['entry_price']) * active_position['size']
                    pnl -= active_position['size'] * (config.TAKER_FEE + config.SLIPPAGE_PCT)
                    balance += pnl
                    trades.append({
                        'Entry Time': active_position['entry_time'], 'Exit Time': current_time,
                        'Type': 'Long', 'Entry Price': active_position['entry_price'],
                        'Exit Price': active_position['tp'], 'Reason': 'Take Profit', 
                        'Net PnL': pnl, 'Balance': balance
                    })
                    active_position = None
                    
            elif active_position['type'] == 'Short':
                # Update lowest price for Trailing Stop
                if close < active_position['lowest_price']:
                    active_position['lowest_price'] = close
                    # Live trailing stop logic
                    new_sl = close + (current_row['atr'] * 1.5)
                    if new_sl < active_position['sl']:
                        active_position['sl'] = new_sl
                        
                # Check Stop Loss / Trailing Stop
                if high >= active_position['sl']:
                    pnl = ((active_position['entry_price'] - active_position['sl']) / active_position['entry_price']) * active_position['size']
                    pnl -= active_position['size'] * (config.TAKER_FEE + config.SLIPPAGE_PCT)
                    balance += pnl
                    trades.append({
                        'Entry Time': active_position['entry_time'], 'Exit Time': current_time,
                        'Type': 'Short', 'Entry Price': active_position['entry_price'],
                        'Exit Price': active_position['sl'], 'Reason': 'Trailing SL/Stop Loss', 
                        'Net PnL': pnl, 'Balance': balance
                    })
                    active_position = None
                    
                # Check Take Profit
                elif low <= active_position['tp']:
                    pnl = ((active_position['entry_price'] - active_position['tp']) / active_position['entry_price']) * active_position['size']
                    pnl -= active_position['size'] * (config.TAKER_FEE + config.SLIPPAGE_PCT)
                    balance += pnl
                    trades.append({
                        'Entry Time': active_position['entry_time'], 'Exit Time': current_time,
                        'Type': 'Short', 'Entry Price': active_position['entry_price'],
                        'Exit Price': active_position['tp'], 'Reason': 'Take Profit', 
                        'Net PnL': pnl, 'Balance': balance
                    })
                    active_position = None

        # Check for new signals
        if active_position is None and current_row['signal'] != 0:
            pos_size, lev = risk_manager.calculate_position_size(
                balance, current_row['atr'], current_row['close'], 
                config.ACCOUNT_RISK_PER_TRADE, config.MAX_LEVERAGE
            )
            
            if pos_size > 0:
                if current_row['signal'] == 1:
                    active_position = {
                        'type': 'Long', 'entry_price': current_row['close'], 'entry_time': current_time,
                        'size': pos_size, 'highest_price': current_row['close'],
                        'sl': current_row['close'] - current_row['sl_distance_price'],
                        'tp': current_row['close'] + current_row['tp_distance_price']
                    }
                elif current_row['signal'] == -1:
                    active_position = {
                        'type': 'Short', 'entry_price': current_row['close'], 'entry_time': current_time,
                        'size': pos_size, 'lowest_price': current_row['close'],
                        'sl': current_row['close'] + current_row['sl_distance_price'],
                        'tp': current_row['close'] - current_row['tp_distance_price']
                    }

    # Generate Report
    df_trades = pd.DataFrame(trades)
    if not df_trades.empty:
        df_trades.to_csv("enterprise_backtest.csv", index=False)
        wins = df_trades[df_trades['Net PnL'] > 0]
        losses = df_trades[df_trades['Net PnL'] <= 0]
        
        win_rate = (len(wins) / len(df_trades)) * 100
        total_gross_profit = wins['Net PnL'].sum()
        total_gross_loss = abs(losses['Net PnL'].sum())
        profit_factor = total_gross_profit / total_gross_loss if total_gross_loss > 0 else np.inf
        
        df_trades['cum_max'] = df_trades['Balance'].cummax()
        df_trades['drawdown'] = ((df_trades['cum_max'] - df_trades['Balance']) / df_trades['cum_max']) * 100
        max_dd = df_trades['drawdown'].max()
        
        print("\n" + "="*40)
        print(" INSTITUTIONAL OPTIMIZED METRICS ")
        print("="*40)
        print(f"Total Trades Executed: {len(df_trades)}")
        print(f"Win Rate:              {win_rate:.2f}%")
        print(f"Profit Factor:         {profit_factor:.2f} (Target > 1.5)")
        print(f"Max Drawdown:          {max_dd:.2f}%")
        print(f"Starting Balance:      ${config.INITIAL_BALANCE:,.2f}")
        print(f"Final Balance:         ${balance:,.2f}")
        print(f"Total Net Return:      {((balance - config.INITIAL_BALANCE)/config.INITIAL_BALANCE)*100:.2f}%")
        print("="*40)
        print("📂 Results saved to: enterprise_backtest.csv")
    else:
        print("❌ No trades executed during this backtest period.")

if __name__ == "__main__":
    run_enterprise_backtest()