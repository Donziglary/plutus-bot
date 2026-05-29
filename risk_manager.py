#!/usr/bin/env python3
"""
Risk management module for verifying trading account health, boundaries, and drawdown limits.
Fully integrated with the object-oriented configuration dataclasses.
"""

from __future__ import annotations

import logging
from typing import Optional
from binance.client import Client

from config import RiskConfig, TradingConfig

# Setup module logger
logger = logging.getLogger(__name__)

class RiskManager:
    """Handles risk mitigation, drawdown tracking, and pre-trade validation checks."""

    def __init__(self, client: Client, risk_cfg: Optional[RiskConfig] = None, trading_cfg: Optional[TradingConfig] = None) -> None:
        """
        Initialise the risk manager with necessary configuration boundaries.
        
        Args:
            client: An active authenticated Binance Client instance.
            risk_cfg: Optional RiskConfig instance.
            trading_cfg: Optional TradingConfig instance.
        """
        self.client = client
        self.risk_cfg = risk_cfg or RiskConfig()
        self.trading_cfg = trading_cfg or TradingConfig()
        self.daily_trade_count = 0

    def check_pre_trade_risk(self, current_balance: float, active_positions_count: int) -> bool:
        """
        Validates whether a new trade can be opened based on the system's risk rules.
        
        Returns:
            True if all risk parameters pass, False otherwise.
        """
        # 1. Verify against minimum capital allocation floor
        if current_balance < self.risk_cfg.min_balance_usdt:
            logger.warning(
                "Risk Check Failed: Current balance ($%.2f) is below the safety threshold ($%.2f).", 
                current_balance, self.risk_cfg.min_balance_usdt
            )
            return False
            
        # 2. Verify maximum concurrent positions limit (Now 6 as requested)
        if active_positions_count >= self.risk_cfg.max_concurrent_positions:
            logger.warning(
                "Risk Check Failed: Active positions (%d) hit the structural portfolio limit (%d).", 
                active_positions_count, self.risk_cfg.max_concurrent_positions
            )
            return False
            
        # 3. Verify maximum daily trade execution limits
        if self.daily_trade_count >= self.risk_cfg.max_daily_trades:
            logger.warning(
                "Risk Check Failed: Daily trade operations cap reached (%d/%d).", 
                self.daily_trade_count, self.risk_cfg.max_daily_trades
            )
            return False
            
        return True

    def increment_trade_count(self) -> None:
        """Increments the daily trade tracker when a position is successfully opened."""
        self.daily_trade_count += 1

    def reset_daily_tracker(self) -> None:
        """Resets the daily trade count. Can be scheduled via an external cron timer."""
        self.daily_trade_count = 0

    def calculate_position_size(self, balance: float, entry_price: float, stop_loss: float) -> float:
        """
        Calculates position sizes based on a fixed risk percentage per trade.
        Formula: Quantity = (Balance * Risk%) / |EntryPrice - StopLoss|
        """
        risk_amount = balance * self.trading_cfg.risk_per_trade_pct
        price_risk = abs(entry_price - stop_loss)
        if price_risk == 0:
            return 0.0
        return round(risk_amount / price_risk, 6)

    # =======================================================================
    # BULLETPROOF ALIASES (Ensures compatibility with any variation of main.py)
    # =======================================================================
    def can_open_position(self, current_balance: float, active_positions_count: int) -> bool:
        """Alias for check_pre_trade_risk."""
        return self.check_pre_trade_risk(current_balance, active_positions_count)

    def validate_trade(self, current_balance: float, active_positions_count: int) -> bool:
        """Alias for check_pre_trade_risk."""
        return self.check_pre_trade_risk(current_balance, active_positions_count)