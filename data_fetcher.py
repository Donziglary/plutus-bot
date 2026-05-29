#!/usr/bin/env python3
"""
Data fetcher module for retrieving historical and live market data from Binance.
Provides full backward compatibility functions required by the main execution engine.
"""

from __future__ import annotations

import logging
import pandas as pd
from typing import Optional
from binance.client import Client
from binance.exceptions import BinanceAPIException, BinanceRequestException

from config import TradingConfig, ExchangeConfig

# Setup module logger
logger = logging.getLogger(__name__)

class DataFetcher:
    """Handles historical and real-time market data extraction from the exchange."""

    def __init__(self, client: Client, trading_cfg: Optional[TradingConfig] = None) -> None:
        """Initialise the data fetcher with an exchange client instance."""
        self.client = client
        self.trading_cfg = trading_cfg or TradingConfig()

    def fetch_historical_klines(self, symbol: Optional[str] = None) -> pd.DataFrame:
        """Fetches historical candlestick (klines) data required for technical analysis."""
        target_symbol = symbol or self.trading_cfg.symbol
        logger.info(
            "Fetching historical klines for %s (Timeframe: %s)",
            target_symbol,
            self.trading_cfg.timeframe
        )

        try:
            # Fetch safe margin for indicators (14 days lookback)
            lookback_string = "14 days ago UTC"
            raw_klines = self.client.get_historical_klines(
                symbol=target_symbol,
                interval=self.trading_cfg.timeframe,
                start_str=lookback_string
            )

            if not raw_klines:
                logger.error("Exchange returned empty data array for %s.", target_symbol)
                return pd.DataFrame()

            df = pd.DataFrame(
                raw_klines,
                columns=[
                    "timestamp", "open", "high", "low", "close", "volume",
                    "close_time", "quote_volume", "trades", "taker_buy_base",
                    "taker_buy_quote", "ignore"
                ]
            )

            df["timestamp"] = pd.to_datetime(df["timestamp"], unit="ms")
            df.set_index("timestamp", inplace=True)
            
            numeric_columns = ["open", "high", "low", "close", "volume"]
            df[numeric_columns] = df[numeric_columns].apply(pd.to_numeric, errors="coerce")
            
            return df[numeric_columns].sort_index()

        except (BinanceAPIException, BinanceRequestException) as exchange_err:
            logger.error("Binance API exception encountered for %s: %s", target_symbol, exchange_err)
            return pd.DataFrame()
        except Exception as general_err:
            logger.error("Unexpected crash during data retrieval: %s", general_err)
            return pd.DataFrame()


# ===========================================================================
# BACKWARD COMPATIBILITY ENGINE (EXPLICITLY REQUIRED BY MAIN.PY)
# ===========================================================================

def create_client() -> Client:
    """
    Creates and returns an authenticated Binance Client instance.
    Invoked directly by main.py to handle infrastructure startup.
    """
    ex_cfg = ExchangeConfig()
    logger.info("Initializing connection to Binance (Testnet=%s)...", ex_cfg.testnet)
    try:
        client = Client(
            api_key=ex_cfg.api_key,
            api_secret=ex_cfg.api_secret,
            testnet=ex_cfg.testnet,
            tld=ex_cfg.tld
        )
        # Verify connection status implicitly
        client.get_system_status()
        logger.info("Binance Client successfully authenticated and verified.")
        return client
    except Exception as e:
        logger.critical("Fatal: Failed to establish secure connection to Binance: %s", e)
        raise e

def fetch_klines(client: Client, symbol: str) -> pd.DataFrame:
    """
    Wrapper function that main.py uses to fetch the standardized OHLCV data.
    """
    fetcher = DataFetcher(client=client)
    return fetcher.fetch_historical_klines(symbol=symbol)

def get_current_price(client: Client, symbol: str) -> float:
    """
    Fetches the latest real-time ticker price for a specific symbol.
    Invoked by main.py for live execution valuation.
    """
    try:
        ticker = client.get_symbol_ticker(symbol=symbol)
        return float(ticker["price"])
    except (BinanceAPIException, BinanceRequestException) as exchange_err:
        logger.error("Failed to fetch live price for %s: %s", symbol, exchange_err)
        return 0.0
    except Exception as e:
        logger.error("Unexpected error fetching price for %s: %s", symbol, e)
        return 0.0