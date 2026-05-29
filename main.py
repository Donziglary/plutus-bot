# main.py
import pandas as pd
import numpy as np
import data_fetcher
import strategy
import config
import risk_manager

def run_enterprise_backtest():
    print("=" * 50)
    print("🤖 PLUTUS QUANT TRADING ENGINE v11.0 - ACTIVE")
    print("=" * 50)
    print("🚀 Initializing Adaptive State-Machine Exit Engine...")
    
    try:
        # Use your exact data fetcher function name here
        df = data_fetcher.fetch_real_futures_data(config.SYMBOL, config.TIMEFRAME, config.DATA_LIMIT)
    except Exception as e:
        print(f"❌ Data fetch failed: {e}")
        return

    if df is None or df.empty:
        print("❌ No data returned from exchange.")
        return

    print("⚙️ Simulating executions with Multi-Stage Exit Machine & Path Heuristics...")
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
            open_p = current_row['open']
            atr = current_row['atr']
            
            trade_closed = False
            exit_price = 0.0
            exit_reason = ""
            
            if active_position['type'] == 'Long':
                if high > active_position['highest_price']:
                    active_position['highest_price'] = high
                
                unrealized_atr_gain = (active_position['highest_price'] - active_position['entry_price']) / atr if atr > 0 else 0
                
                # 1. Breakeven Migration State
                if active_position['state'] == 'Initial' and unrealized_atr_gain >= config.BREAKEVEN_ACTIVATION_ATR:
                    active_position['state'] = 'Breakeven'
                    active_position['sl'] = active_position['entry_price'] * (1 + config.TAKER_FEE + config.SLIPPAGE_PCT)
                
                # 2. Trailing Activation State
                if active_position['state'] in ['Initial', 'Breakeven'] and unrealized_atr_gain >= config.TRAILING_ACTIVATION_ATR:
                    active_position['state'] = 'Trailing'
                
                # 3. Dynamic Trailing SL Calculation
                if active_position['state'] == 'Trailing':
                    calculated_sl = active_position['highest_price'] - (atr * config.TRAILING_DISTANCE_ATR)
                    if calculated_sl > active_position['sl']:
                        active_position['sl'] = calculated_sl
                
                # Evaluate Exit Conditions
                is_stop_hit = (low <= active_position['sl'])
                is_tp_hit = (high >= active_position['tp'])
                
                if is_stop_hit and is_tp_hit:
                    # Path heuristic based on candle color structure
                    if close >= open_p:
                        exit_price = active_position['tp']
                        exit_reason = f"Take Profit (Heuristic - {active_position['state']})"
                        trade_closed = True
                    else:
                        exit_price = active_position['sl']
                        exit_reason = f"Stop/Trailing Hit (Heuristic - {active_position['state']})"
                        trade_closed = True
                elif is_tp_hit:
                    exit_price = active_position['tp']
                    exit_reason = "Take Profit"
                    trade_closed = True
                elif is_stop_hit:
                    exit_price = active_position['sl']
                    exit_reason = f"Stop/Trailing Hit ({active_position['state']})"
                    trade_closed = True
                    
                if trade_closed:
                    pnl = ((exit_price - active_position['entry_price']) / active_position['entry_price']) * active_position['size']
                    pnl -= active_position['size'] * (config.TAKER_FEE + config.SLIPPAGE_PCT)
                    balance += pnl
                    trades.append({
                        'Entry Time': active_position['entry_time'], 'Exit Time': current_time,
                        'Type': 'Long', 'Entry Price': active_position['entry_price'],
                        'Exit Price': exit_price, 'Reason': exit_reason, 
                        'Net PnL': pnl, 'Balance': balance
                    })
                    active_position = None
                    
            elif active_position['type'] == 'Short':
                if low < active_position['lowest_price']:
                    active_position['lowest_price'] = low
                
                unrealized_atr_gain = (active_position['entry_price'] - active_position['lowest_price']) / atr if atr > 0 else 0
                
                # 1. Breakeven Migration State
                if active_position['state'] == 'Initial' and unrealized_atr_gain >= config.BREAKEVEN_ACTIVATION_ATR:
                    active_position['state'] = 'Breakeven'
                    active_position['sl'] = active_position['entry_price'] * (1 - (config.TAKER_FEE + config.SLIPPAGE_PCT))
                
                # 2. Trailing Activation State
                if active_position['state'] in ['Initial', 'Breakeven'] and unrealized_atr_gain >= config.TRAILING_ACTIVATION_ATR:
                    active_position['state'] = 'Trailing'
                
                # 3. Dynamic Trailing SL Calculation
                if active_position['state'] == 'Trailing':
                    calculated_sl = active_position['lowest_price'] + (atr * config.TRAILING_DISTANCE_ATR)
                    if calculated_sl < active_position['sl']:
                        active_position['sl'] = calculated_sl
                
                # Evaluate Exit Conditions
                is_stop_hit = (high >= active_position['sl'])
                is_tp_hit = (low <= active_position['tp'])
                
                if is_stop_hit and is_tp_hit:
                    if close <= open_p:
                        exit_price = active_position['tp']
                        exit_reason = f"Take Profit (Heuristic - {active_position['state']})"
                        trade_closed = True
                    else:
                        exit_price = active_position['sl']
                        exit_reason = f"Stop/Trailing Hit (Heuristic - {active_position['state']})"
                        trade_closed = True
                elif is_tp_hit:
                    exit_price = active_position['tp']
                    exit_reason = "Take Profit"
                    trade_closed = True
                elif is_stop_hit:
                    exit_price = active_position['sl']
                    exit_reason = f"Stop/Trailing Hit ({active_position['state']})"
                    trade_closed = True
                    
                if trade_closed:
                    pnl = ((active_position['entry_price'] - exit_price) / active_position['entry_price']) * active_position['size']
                    pnl -= active_position['size'] * (config.TAKER_FEE + config.SLIPPAGE_PCT)
                    balance += pnl
                    trades.append({
                        'Entry Time': active_position['entry_time'], 'Exit Time': current_time,
                        'Type': 'Short', 'Entry Price': active_position['entry_price'],
                        'Exit Price': exit_price, 'Reason': exit_reason, 
                        'Net PnL': pnl, 'Balance': balance
                    })
                    active_position = None

        # Check for incoming entry signals
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
                        'tp': current_row['close'] + current_row['tp_distance_price'],
                        'state': 'Initial'
                    }
                elif current_row['signal'] == -1:
                    active_position = {
                        'type': 'Short', 'entry_price': current_row['close'], 'entry_time': current_time,
                        'size': pos_size, 'lowest_price': current_row['close'],
                        'sl': current_row['close'] + current_row['sl_distance_price'],
                        'tp': current_row['close'] - current_row['tp_distance_price'],
                        'state': 'Initial'
                    }

    # Post-Execution Analytical Reporting Engine
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
        
        # Monthly Performance Breakdown Interface
        print("\n" + "="*40)
        print(" MONTHLY PERFORMANCE BREAKDOWN ")
        print("="*40)
        df_trades['Month'] = pd.to_datetime(df_trades['Entry Time']).dt.strftime('%Y-%m')
        grouped = df_trades.groupby('Month')
        for month, group in grouped:
            month_pnl = group['Net PnL'].sum()
            month_trades = len(group)
            month_wins = len(group[group['Net PnL'] > 0])
            month_wr = (month_wins / month_trades) * 100 if month_trades > 0 else 0
            month_ret_pct = (month_pnl / config.INITIAL_BALANCE) * 100
            print(f"Month: {month} | Trades: {month_trades} | Win Rate: {month_wr:.2f}% | Net PnL: ${month_pnl:,.2f} ({month_ret_pct:+.2f}%)")
        print("="*40)
        print("📂 Results saved to: enterprise_backtest.csv")
    else:
        print("❌ No trades executed during this backtest period.")

if __name__ == "__main__":
    run_enterprise_backtest()