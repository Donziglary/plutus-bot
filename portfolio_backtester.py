#!/usr/bin/env python3
"""
Vectorized Portfolio Backtesting Engine.
Simulates trading across multiple assets concurrently using offline data.
Enforces max concurrent positions and generates aggregated monthly reports.
"""

from __future__ import annotations

import os
import glob
import logging
from typing import Dict, List, Optional

import pandas as pd
import numpy as np

# Import your strategy and config
from strategy import generate_signals, compute_atr_stop
from config import TradingConfig
from main import PositionManager, ExitState

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("portfolio-backtester")

DATA_DIR = "data"
INITIAL_BALANCE = 10000.0
MAX_CONCURRENT_POSITIONS = 6  # Updated per user request
RISK_PER_TRADE_PCT = 0.01     # 1% risk
TAKER_FEE = 0.0004
SLIPPAGE_PCT = 0.0010

def load_and_prepare_portfolio_data() -> pd.DataFrame:
    """
    Loads all CSV files from the data directory, computes indicators for each,
    and combines them into a single master DataFrame sorted by timestamp.
    """
    all_files = glob.glob(os.path.join(DATA_DIR, "*.csv"))
    if not all_files:
        raise FileNotFoundError(f"No CSV files found in {DATA_DIR}/. Run download_data.py first.")

    portfolio_list = []
    
    for file in all_files:
        symbol = os.path.basename(file).split("_")[0]
        logger.info("Processing indicators for %s...", symbol)
        
        df = pd.read_csv(file)
        df["timestamp"] = pd.to_datetime(df["timestamp"])
        df.set_index("timestamp", inplace=True)
        df.sort_index(inplace=True)
        
        # Apply strategy indicators (Vectorized)
        df = generate_signals(df)
        df.dropna(inplace=True) # Drop NaN rows from EMA warmup
        
        # Add symbol column for identification in the master timeline
        df["symbol"] = symbol
        portfolio_list.append(df)
        
    # Combine all assets into one giant timeline
    logger.info("Merging all assets into master timeline...")
    master_df = pd.concat(portfolio_list)
    master_df.sort_index(inplace=True)
    return master_df

def compute_offline_position_size(balance: float, entry: float, stop: float) -> float:
    """Simplified position sizing for the backtester."""
    risk_amount = balance * RISK_PER_TRADE_PCT
    price_diff = abs(entry - stop)
    if price_diff == 0: return 0.0
    qty = risk_amount / price_diff
    return round(qty, 5)

def run_portfolio_backtest() -> None:
    """Executes the portfolio simulation across all assets chronologically."""
    try:
        master_df = load_and_prepare_portfolio_data()
    except Exception as e:
        logger.error(e)
        return

    balance = INITIAL_BALANCE
    active_positions: Dict[str, PositionManager] = {} # Key: Symbol, Value: PositionManager
    trade_history: List[Dict] = []
    
    logger.info("Starting chronological portfolio simulation (Max %s positions)...", MAX_CONCURRENT_POSITIONS)
    
    # Iterate through time chronologically. 
    # Note: itertuples is much faster than iterrows for large datasets.
    for row in master_df.itertuples():
        current_time = row.Index
        sym = row.symbol
        close_p = row.close
        high_p = row.high
        low_p = row.low
        open_p = row.open
        atr_val = row.atr
        
        # 1. Update Existing Position for this symbol
        if sym in active_positions:
            pos = active_positions[sym]
            exited = pos.update(high=high_p, low=low_p, close=close_p, atr=atr_val)
            
            if exited:
                # Determine Exit Price based on exit reason
                # Simplified heuristic: if long and stop triggered, use stop price.
                if pos.state == ExitState.EXIT_TRIGGERED:
                    exit_price = pos.trailing_stop
                    reason = "Stop/Trailing Hit"
                else: # Default fallback (should be handled better in a real sim)
                    exit_price = close_p
                    reason = "System Exit"
                    
                # Calculate PnL
                if pos.side == "LONG":
                    pnl = ((exit_price - pos.entry_price) / pos.entry_price) * (pos.quantity * pos.entry_price)
                else:
                    pnl = ((pos.entry_price - exit_price) / pos.entry_price) * (pos.quantity * pos.entry_price)
                    
                # Deduct fees and slippage on exit (entry fees factored implicitly or here)
                fee_cost = (pos.quantity * exit_price) * (TAKER_FEE + SLIPPAGE_PCT)
                pnl -= fee_cost
                
                balance += pnl
                trade_history.append({
                    "Symbol": sym,
                    "Exit Time": current_time,
                    "Side": pos.side,
                    "PnL": pnl,
                    "Balance": balance,
                    "Reason": reason
                })
                # Remove closed position
                del active_positions[sym]

        # 2. Check for New Entry Signals (If we have room in the portfolio)
        if sym not in active_positions and len(active_positions) < MAX_CONCURRENT_POSITIONS:
            if row.signal_long and not row.signal_short:
                stop = compute_atr_stop(close_p, atr_val, "LONG")
                qty = compute_offline_position_size(balance, close_p, stop)
                if qty > 0:
                    new_pos = PositionManager()
                    new_pos.open_position("LONG", close_p, stop, qty)
                    active_positions[sym] = new_pos
                    # Deduct entry fees
                    entry_fee = (qty * close_p) * (TAKER_FEE + SLIPPAGE_PCT)
                    balance -= entry_fee
                    
            elif row.signal_short and not row.signal_long:
                stop = compute_atr_stop(close_p, atr_val, "SHORT")
                qty = compute_offline_position_size(balance, close_p, stop)
                if qty > 0:
                    new_pos = PositionManager()
                    new_pos.open_position("SHORT", close_p, stop, qty)
                    active_positions[sym] = new_pos
                    entry_fee = (qty * close_p) * (TAKER_FEE + SLIPPAGE_PCT)
                    balance -= entry_fee

    # ---- Generate Portfolio Report ----
    df_trades = pd.DataFrame(trade_history)
    if df_trades.empty:
        logger.warning("No trades executed during the simulation period.")
        return
        
    wins = df_trades[df_trades["PnL"] > 0]
    win_rate = (len(wins) / len(df_trades)) * 100
    
    logger.info("="*50)
    logger.info(" PORTFOLIO BACKTEST REPORT (1 YEAR - 15 ASSETS)")
    logger.info("="*50)
    logger.info("Total Trades:      %d", len(df_trades))
    logger.info("Win Rate:          %.2f%%", win_rate)
    logger.info("Starting Balance:  $%.2f", INITIAL_BALANCE)
    logger.info("Final Balance:     $%.2f", balance)
    logger.info("Net ROI:           %+.2f%%", ((balance - INITIAL_BALANCE) / INITIAL_BALANCE) * 100)
    logger.info("="*50)
    
    # Monthly Breakdown
    logger.info(" MONTHLY BREAKDOWN ")
    logger.info("="*50)
    df_trades["Month"] = pd.to_datetime(df_trades["Exit Time"]).dt.strftime('%Y-%m')
    monthly = df_trades.groupby("Month")["PnL"].sum()
    for month, pnl in monthly.items():
        logger.info("Month: %s | Net PnL: $%+8.2f", month, pnl)
        
    df_trades.to_csv("portfolio_results.csv", index=False)
    logger.info("Detailed trade history saved to portfolio_results.csv")

if __name__ == "__main__":
    run_portfolio_backtest()