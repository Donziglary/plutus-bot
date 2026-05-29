#!/usr/bin/env python3
"""
Offline Data Pipeline for Portfolio Backtesting.
Downloads 1 year of 15m klines for 15 major assets with rate-limit protection.
Saves them locally as CSV files in the 'data/' directory.
"""

from __future__ import annotations

import os
import time
import logging
from typing import List

import pandas as pd
from binance.client import Client
from binance.exceptions import BinanceAPIException, BinanceRequestException

from config import ExchangeConfig

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("data-downloader")

# 15 High-Volume / High-Volatility Pairs
PORTFOLIO_ASSETS: List[str] = [
    "BTCUSDT", "ETHUSDT", "SOLUSDT", "BNBUSDT", "XRPUSDT",
    "ADAUSDT", "AVAXUSDT", "DOGEUSDT", "LINKUSDT", "DOTUSDT",
    "MATICUSDT", "LTCUSDT", "BCHUSDT", "APTUSDT", "INJUSDT"
]
TIMEFRAME = "15m"
DAYS_TO_FETCH = 365
DATA_DIR = "data"

def fetch_historical_klines(client: Client, symbol: str, timeframe: str, days: int) -> pd.DataFrame:
    """Fetch historical klines from Binance and return a clean DataFrame."""
    logger.info("Fetching %s days of %s data for %s...", days, timeframe, symbol)
    try:
        # Binance format: "1 year ago UTC" or "365 days ago UTC"
        start_str = f"{days} days ago UTC"
        raw = client.get_historical_klines(symbol, timeframe, start_str)
        
        if not raw:
            logger.warning("No data returned for %s", symbol)
            return pd.DataFrame()

        df = pd.DataFrame(
            raw,
            columns=[
                "timestamp", "open", "high", "low", "close", "volume",
                "close_time", "quote_volume", "trades", "taker_buy_base",
                "taker_buy_quote", "ignore",
            ],
        )
        numeric_cols = ["open", "high", "low", "close", "volume", "quote_volume"]
        df[numeric_cols] = df[numeric_cols].apply(pd.to_numeric, axis=1)
        df["timestamp"] = pd.to_datetime(df["timestamp"], unit="ms")
        df.set_index("timestamp", inplace=True)
        df.sort_index(inplace=True)
        
        # Keep only necessary columns to save disk space
        return df[["open", "high", "low", "close", "volume"]]
        
    except (BinanceAPIException, BinanceRequestException) as e:
        logger.error("Failed to fetch %s: %s", symbol, e)
        return pd.DataFrame()

def main() -> None:
    """Main execution loop for the data downloader."""
    if not os.path.exists(DATA_DIR):
        os.makedirs(DATA_DIR)
        
    cfg = ExchangeConfig()
    client = Client(api_key=cfg.api_key, api_secret=cfg.api_secret, testnet=cfg.testnet, tld=cfg.tld)

    for symbol in PORTFOLIO_ASSETS:
        file_path = os.path.join(DATA_DIR, f"{symbol}_{TIMEFRAME}.csv")
        
        # Skip if already downloaded to save API limits
        if os.path.exists(file_path):
            logger.info("File %s already exists. Skipping.", file_path)
            continue
            
        df = fetch_historical_klines(client, symbol, TIMEFRAME, DAYS_TO_FETCH)
        
        if not df.empty:
            df.to_csv(file_path)
            logger.info("Saved %s rows to %s", len(df), file_path)
            
        # Crucial: Sleep to respect exchange rate limits and avoid IP bans
        logger.info("Sleeping for 3 seconds to respect rate limits...")
        time.sleep(3)
        
    logger.info("Data pipeline execution complete. All portfolio assets downloaded.")

if __name__ == "__main__":
    main()