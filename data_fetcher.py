# data_fetcher.py (Clean European VPS Version)
import requests
import pandas as pd
import config

def fetch_real_futures_data(symbol=config.SYMBOL, interval=config.TIMEFRAME, limit=config.DATA_LIMIT):
    """
    Fetches clean, real-time futures data directly via raw HTTP.
    No proxies, no fallbacks needed on a European VPS.
    """
    print(f"🌍 Fetching REAL Market Data for {symbol} ({interval})...")
    
    # Binance Futures Public Endpoint (Extremely fast & stable in Europe)
    url = "https://fapi.binance.com/fapi/v1/klines"
    params = {
        "symbol": symbol.replace("/", "").replace(":", "").replace("-", ""), # e.g. SOLUSDT
        "interval": interval,
        "limit": limit
    }
    
    try:
        response = requests.get(url, params=params, timeout=5)
        response.raise_for_status()
        data = response.json()
        
        # Parse data
        df = pd.DataFrame(data, columns=[
            'timestamp', 'open', 'high', 'low', 'close', 'volume', 
            'close_time', 'quote_vol', 'trades', 'taker_buy_base', 'taker_buy_quote', 'ignore'
        ])
        
        df = df[['timestamp', 'open', 'high', 'low', 'close', 'volume']]
        for col in ['open', 'high', 'low', 'close', 'volume']:
            df[col] = df[col].astype(float)
            
        df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
        print(f"✅ Loaded {len(df)} candles with ~1ms ping!")
        return df

    except Exception as e:
        print(f"❌ Failed to fetch data: {e}")
        return None