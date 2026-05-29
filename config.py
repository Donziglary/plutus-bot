#!/usr/bin/env python3
"""
Trading system configuration module.
All sensitive credentials are loaded from environment variables.
"""

import os
import logging
from dataclasses import dataclass, field
from typing import Optional, Final

# ---------------------------------------------------------------------------
# Logging setup
# ---------------------------------------------------------------------------
logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class ExchangeConfig:
    """Immutable exchange connection parameters."""

    api_key: Final[str] = field(
        default_factory=lambda: os.getenv("BINANCE_API_KEY", "")
    )
    api_secret: Final[str] = field(
        default_factory=lambda: os.getenv("BINANCE_API_SECRET", "")
    )
    testnet: Final[bool] = field(
        default_factory=lambda: os.getenv("EXCHANGE_TESTNET", "True").lower() == "true"
    )
    tld: Final[str] = "com"  # Binance top-level domain
    recv_window: Final[int] = 60000


@dataclass(frozen=True)
class TradingConfig:
    """Core trading parameters, immutable after initialisation."""

    symbol: Final[str] = "BTCUSDT"
    timeframe: Final[str] = "15m"  # Set to 15-minute candles
    max_position_pct: Final[float] = 0.98  # Maximum capital allocation (98 %)
    risk_per_trade_pct: Final[float] = 0.01  # 1 % risk per trade
    leverage: Final[int] = 1
    atr_period: Final[int] = 14
    atr_multiplier_sl: Final[float] = 2.0  # Stop-loss distance multiplier
    trailing_activation_pct: Final[float] = (
        0.005  # 0.5 % profit to activate trailing stop
    )
    breakeven_activation_pct: Final[float] = 0.003  # 0.3 % profit to move SL to entry
    lookback_candles: Final[int] = 500  # Historical data window
    max_slippage_pct: Final[float] = 0.001  # 0.1 % allowed slippage
    order_timeout_seconds: Final[int] = 10


@dataclass(frozen=True)
class StrategyConfig:
    """Strategy indicator parameters."""

    rsi_period: Final[int] = 14
    rsi_oversold: Final[int] = 30
    rsi_overbought: Final[int] = 70
    ema_fast: Final[int] = 12
    ema_slow: Final[int] = 26
    volume_ma_period: Final[int] = 20


@dataclass(frozen=True)
class RiskConfig:
    """Risk management boundaries."""

    max_daily_trades: Final[int] = 10
    max_drawdown_pct: Final[float] = 0.15  # 15 % max drawdown before shutdown
    min_balance_usdt: Final[float] = 50.0
    max_concurrent_positions: Final[int] = 6  # Set to 6 per your request


def validate_config() -> None:
    """Quick sanity checks on the configuration values."""
    if not ExchangeConfig().api_key or not ExchangeConfig().api_secret:
        logger.warning(
            "API credentials are missing. Set BINANCE_API_KEY and BINANCE_API_SECRET environment variables."
        )
    if (
        TradingConfig().risk_per_trade_pct <= 0
        or TradingConfig().risk_per_trade_pct > 0.1
    ):
        logger.warning(
            "Risk per trade is set to %0.4f, which is unusually high.",
            TradingConfig().risk_per_trade_pct,
        )
