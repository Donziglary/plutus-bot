#!/usr/bin/env python3
"""
Production‑grade trading core with state‑machine exit engine, trailing stops,
breakeven migration, and robust order execution.
"""

from __future__ import annotations

import logging
import time
from typing import Optional, Dict, Any, Tuple, Literal

import pandas as pd
from binance.client import Client
from binance.enums import (
    ORDER_TYPE_MARKET,
    ORDER_TYPE_STOP_LOSS_LIMIT,
    SIDE_BUY,
    SIDE_SELL,
    TIME_IN_FORCE_GTC,
)

from config import TradingConfig, validate_config
from data_fetcher import create_client, fetch_klines, get_current_price
from strategy import generate_signals, compute_atr_stop
from risk_manager import RiskManager

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("plutus-core")


# ---------------------------------------------------------------------------
# State‑Machine Exit Engine
# ---------------------------------------------------------------------------
class ExitState:
    """Enumeration of position exit states."""

    IDLE = "IDLE"
    ACTIVE = "ACTIVE"
    TRAILING = "TRAILING"
    BREAKEVEN = "BREAKEVEN"
    EXIT_TRIGGERED = "EXIT_TRIGGERED"


class PositionManager:
    """
    Manages the lifecycle of a single open position.
    Implements a strict state machine for trailing stops and breakeven migration,
    free from look‑ahead bias.
    """

    def __init__(self) -> None:
        self.state: ExitState = ExitState.IDLE
        self.side: Optional[Literal["LONG", "SHORT"]] = None
        self.entry_price: float = 0.0
        self.initial_stop: float = 0.0
        self.trailing_stop: float = 0.0
        self.quantity: float = 0.0  # Tracks the precise size of the active position
        self.highest_high: Optional[float] = None
        self.lowest_low: Optional[float] = None

    def open_position(
        self, side: Literal["LONG", "SHORT"], entry: float, stop: float, qty: float
    ) -> None:
        """Initialise a new position and set the initial stop loss."""
        self.state = ExitState.ACTIVE
        self.side = side
        self.entry_price = entry
        self.initial_stop = stop
        self.trailing_stop = stop
        self.quantity = qty
        if side == "LONG":
            self.highest_high = entry
            self.lowest_low = None
        else:
            self.lowest_low = entry
            self.highest_high = None

    def update(self, high: float, low: float, close: float, atr: float) -> bool:
        """
        Process a new candle and return True if the position has been closed.

        The update order eliminates look‑ahead bias:
          1. Check if the exit was triggered intra‑bar by price touching the trailing stop.
          2. Update trailing extremes (high/low).
          3. Adjust stop according to ATR and activation thresholds.
        """
        if self.state in (ExitState.IDLE, ExitState.EXIT_TRIGGERED):
            return True

        cfg = TradingConfig()
        exit_triggered = False

        # ---- Intra‑bar exit check (using the candle's low/high vs current stop) ----
        if self.side == "LONG":
            if low <= self.trailing_stop:
                logger.info(
                    "Long trailing stop hit. Low: %.4f <= Stop: %.4f",
                    low,
                    self.trailing_stop,
                )
                exit_triggered = True
        else:  # SHORT
            if high >= self.trailing_stop:
                logger.info(
                    "Short trailing stop hit. High: %.4f >= Stop: %.4f",
                    high,
                    self.trailing_stop,
                )
                exit_triggered = True

        if exit_triggered:
            self.state = ExitState.EXIT_TRIGGERED
            return True

        # ---- Update extreme prices ----
        if self.side == "LONG":
            if high > (self.highest_high or 0):
                self.highest_high = high
        else:
            if low < (self.lowest_low or float("inf")):
                self.lowest_low = low

        # ---- Trailing stop logic ----
        if self.side == "LONG":
            profit_pct = (self.highest_high - self.entry_price) / self.entry_price
            if profit_pct >= cfg.trailing_activation_pct:
                if self.state != ExitState.TRAILING:
                    self.state = ExitState.TRAILING
                    logger.debug("Activated trailing stop for long.")
                new_stop = self.highest_high - atr * cfg.atr_multiplier_sl
                if new_stop > self.trailing_stop:
                    self.trailing_stop = new_stop
        else:  # SHORT
            profit_pct = (self.entry_price - self.lowest_low) / self.entry_price
            if profit_pct >= cfg.trailing_activation_pct:
                if self.state != ExitState.TRAILING:
                    self.state = ExitState.TRAILING
                    logger.debug("Activated trailing stop for short.")
                new_stop = self.lowest_low + atr * cfg.atr_multiplier_sl
                if new_stop < self.trailing_stop:
                    self.trailing_stop = new_stop

        # ---- Breakeven migration (moves SL to entry when profit exceeds threshold) ----
        if self.state == ExitState.TRAILING:
            if self.side == "LONG":
                if (
                    profit_pct >= cfg.breakeven_activation_pct
                    and self.trailing_stop < self.entry_price
                ):
                    self.trailing_stop = self.entry_price
                    self.state = ExitState.BREAKEVEN
                    logger.info(
                        "Moved stop to breakeven (entry price) for long position."
                    )
            else:  # SHORT
                if (
                    profit_pct >= cfg.breakeven_activation_pct
                    and self.trailing_stop > self.entry_price
                ):
                    self.trailing_stop = self.entry_price
                    self.state = ExitState.BREAKEVEN
                    logger.info(
                        "Moved stop to breakeven (entry price) for short position."
                    )

        return False  # Position still open


# ---------------------------------------------------------------------------
# Order Execution Helpers
# ---------------------------------------------------------------------------
def place_market_order(
    client: Client, side: str, quantity: float
) -> Optional[Dict[str, Any]]:
    """Place a market order with timeout and error handling."""
    try:
        order = client.create_order(
            symbol=TradingConfig().symbol,
            side=side,
            type=ORDER_TYPE_MARKET,
            quantity=quantity,
            newOrderRespType="FULL",
        )
        logger.info("Market %s order filled: %s", side, order["status"])
        return order
    except Exception as e:
        logger.error("Market order failed: %s", e)
        return None


def place_stop_loss_order(
    client: Client, side: str, quantity: float, stop_price: float
) -> Optional[Dict[str, Any]]:
    """
    Place a stop‑loss limit order.
    For a long exit, side = SELL; for short exit, side = BUY.
    """
    try:
        order = client.create_order(
            symbol=TradingConfig().symbol,
            side=side,
            type=ORDER_TYPE_STOP_LOSS_LIMIT,
            quantity=quantity,
            price=(
                round(stop_price * 0.999, 2)
                if side == SIDE_SELL
                else round(stop_price * 1.001, 2)
            ),
            stopPrice=stop_price,
            timeInForce=TIME_IN_FORCE_GTC,
        )
        logger.info("Stop‑loss order placed at %.4f.", stop_price)
        return order
    except Exception as e:
        logger.error("Stop‑loss order failed: %s", e)
        return None


# ---------------------------------------------------------------------------
# Main Trading Loop
# ---------------------------------------------------------------------------
def main() -> None:
    """Infinite trading loop: fetch data, evaluate signals, manage risk and orders."""
    validate_config()
    client = create_client()
    risk_mgr = RiskManager(client)
    position = PositionManager()

    logger.info("Plutus trading engine started. Symbol: %s", TradingConfig().symbol)

    while True:
        try:
            # ----- 1. Fetch latest market data -----
            df = fetch_klines(client)
            if len(df) < TradingConfig().lookback_candles:
                logger.warning("Insufficient data; waiting for next cycle.")
                time.sleep(60)
                continue

            # ----- 2. Generate signals -----
            df_signals = generate_signals(df)
            latest = df_signals.iloc[-1]  # newest completed candle

            # ----- 3. Position management (exit logic) -----
            if (
                position.state != ExitState.IDLE
                and position.state != ExitState.EXIT_TRIGGERED
            ):
                prev_candle = df_signals.iloc[-2]  # second last candle
                atr_now = latest["atr"]
                exited = position.update(
                    high=prev_candle["high"],
                    low=prev_candle["low"],
                    close=prev_candle["close"],
                    atr=atr_now if not pd.isna(atr_now) else 0.0,
                )
                if exited:
                    logger.info(
                        "Position closed by exit engine. Executing market order..."
                    )
                    if position.side == "LONG":
                        place_market_order(client, SIDE_SELL, position.quantity)
                    else:
                        place_market_order(client, SIDE_BUY, position.quantity)
                    position = PositionManager()  # reset state to IDLE

            # ----- 4. Entry signal evaluation -----
            if position.state == ExitState.IDLE and risk_mgr.can_place_trade():
                entry_price = get_current_price(client)
                atr_val = latest["atr"]
                if pd.isna(atr_val):
                    time.sleep(10)
                    continue

                # Long Entry Condition
                if latest["signal_long"] and not latest["signal_short"]:
                    stop = compute_atr_stop(entry_price, atr_val, "LONG")
                    size_info = risk_mgr.compute_position_size(
                        entry_price, stop, "LONG"
                    )
                    if size_info:
                        qty, notional = size_info
                        order = place_market_order(client, SIDE_BUY, qty)
                        if order:
                            position.open_position("LONG", entry_price, stop, qty)
                            place_stop_loss_order(client, SIDE_SELL, qty, stop)
                            risk_mgr.record_trade()

                # Short Entry Condition
                elif latest["signal_short"] and not latest["signal_long"]:
                    stop = compute_atr_stop(entry_price, atr_val, "SHORT")
                    size_info = risk_mgr.compute_position_size(
                        entry_price, stop, "SHORT"
                    )
                    if size_info:
                        qty, notional = size_info
                        order = place_market_order(client, SIDE_SELL, qty)
                        if order:
                            position.open_position("SHORT", entry_price, stop, qty)
                            place_stop_loss_order(client, SIDE_BUY, qty, stop)
                            risk_mgr.record_trade()

            # Wait 10 seconds before polling for new micro-changes or next candle
            time.sleep(10)

        except Exception as e:
            logger.error("Error in main loop: %s", e)
            time.sleep(10)


if __name__ == "__main__":
    main()
