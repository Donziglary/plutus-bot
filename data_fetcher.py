#!/usr/bin/env python3
"""
Data fetcher module for retrieving historical and live market data from Binance.
Fully integrated with the object-oriented configuration dataclasses.
"""

from __future__ import annotations

import logging
import pandas as pd
from typing import Optional
from binance.client import Client
from binance.exceptions import BinanceAPIException, BinanceRequestException

from config import TradingConfig

# Setup module logger
logger = logging.getLogger(__name__)

class DataFetcher:
    """Handles historical and real-time market data extraction from the exchange."""

    def __init__(self, client: Client, trading_cfg: Optional[TradingConfig] = None) -> None:
        """
        Initialise the data fetcher with an exchange client instance.
        
        Args:
            client: An active instances of the Binance python Client.
            trading_cfg: Optional trading configurations dataclass.
        """
        self.client = client
        self.trading_cfg = trading_cfg or TradingConfig()

    def fetch_historical_klines(self, symbol: Optional[str] = None) -> pd.DataFrame:
        """
        Fetches historical candlestick (klines) data required for technical analysis.
        
        Args:
            symbol: Optional symbol override. If None, uses default from config.
            
        Returns:
            A pandas DataFrame containing standardized OHLCV historical data.
        """
        target_symbol = symbol or self.trading_cfg.symbol
        logger.info(
            "Fetching historical klines for %s (Timeframe: %s, Lookback Window: %d candles)",
            target_symbol,
            self.trading_cfg.timeframe,
            self.trading_cfg.lookback_candles
        )

        try:
            # Compute a safe chronological buffer to ensure enough data for EMA/RSI warmups.
            # 500 candles of 15m is roughly 5.2 days. Fetching 14 days provides a very safe margin.
            lookback_string = "14 days ago UTC"

            raw_klines = self.client.get_historical_klines(
                symbol=target_symbol,
                interval=self.trading_cfg.timeframe,
                start_str=lookback_string
            )

            if not raw_klines:
                logger.error("Exchange returned empty data array for %s.", target_symbol)
                return pd.DataFrame()

            # Build structural pandas dataframe from raw exchange response
            df = pd.DataFrame(
                raw_klines,
                columns=[
                    "timestamp", "open", "high", "low", "close", "volume",
                    "close_time", "quote_volume", "trades", "taker_buy_base",
                    "taker_buy_quote", "ignore"
                ]
            )

            # Perform explicit data conversions and processing
            df["timestamp"] = pd.to_datetime(df["timestamp"], unit="ms")
            df.set_index("timestamp", inplace=True)
            
            numeric_columns = ["open", "high", "low", "close", "volume"]
            df[numeric_columns] = df[numeric_columns].apply(pd.to_numeric, errors="coerce")
            
            # Standardise and slice data down to clean OHLCV parameters
            clean_df = df[numeric_columns].sort_index()
            
            # Return the required subset or the full safe history for technical analysis
            return clean_df

        except (BinanceAPIException, BinanceRequestException) as exchange_err:
            logger.error("Binance network/API exception encountered for %s: %s", target_symbol, exchange_err)
            return pd.DataFrame()
        except Exception as general_err:
            logger.error("Unexpected pipeline crash during historical data retrieval: %s", general_err)
            return pd.DataFrame()

def get_market_data(client: Client, symbol: Optional[str] = None) -> pd.DataFrame:
    """
    Functional backward-compatibility wrapper for fetching historical market data.
    Instantiates the DataFetcher internally.
    """
    fetcher = DataFetcher(client=client)
    return fetcher.fetch_historical_klines(symbol=symbol)