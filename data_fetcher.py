# data_fetcher.py (Anti-403 Cloud Engine Version)
import requests
import pandas as pd
import config
import time

def convert_timeframe_to_bybit(tf_str):
    tf_str = tf_str.lower()
    if 'm' in tf_str: return tf_str.replace('m', '')
    if 'h' in tf_str: return str(int(tf_str.replace('h', '')) * 60)
    return tf_str

def fetch_from_bybit(clean_symbol, bybit_interval, limit, headers):
    """Attempt 1: Fetching from Bybit with Spoofed Headers."""
    url = "https://api.bybit.com/v5/market/kline"
    params = {"category": "linear", "symbol": clean_symbol, "interval": bybit_interval, "limit": str(limit)}
    
    response = requests.get(url, params=params, headers=headers, timeout=10)
    response.raise_for_status()
    data = response.json()
    
    if data and data.get('retCode') == 0:
        raw_candles = data['result']['list']
        df = pd.DataFrame(raw_candles, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume', 'turnover'])
        df = df[['timestamp', 'open', 'high', 'low', 'close', 'volume']]
        df = df.iloc[::-1].reset_index(drop=True)
        return df
    return None

def fetch_from_kucoin_fallback(clean_symbol, interval, limit, headers):
    """Attempt 2: Cloud-Friendly KuCoin Institutional Node."""
    # Convert symbol formatting for KuCoin (e.g., SOLUSDT -> SOL-USDT)
    kucoin_symbol = f"{clean_symbol[:-4]}-{clean_symbol[-4:]}"
    
    # Format timeframe for KuCoin (e.g., 5m -> 5min, 1h -> 1hour)
    kucoin_interval = interval.replace('m', 'min').replace('h', 'hour')
    
    print(f"🔄 [Fallback Route] Bybit restricted. Routing to KuCoin Cloud Node for {kucoin_symbol}...")
    
    url = "https://api.kucoin.com/api/v1/market/candles"
    
    # KuCoin uses start/end timestamps instead of limits sometimes, 
    # but their endpoint also supports time range estimation.
    # To keep it simple and fast, we calculate roughly the start time.
    minutes_per_candle = 5 if '5m' in interval else 60
    start_time = int(time.time()) - (limit * minutes_per_candle * 60)
    
    params = {
        "symbol": kucoin_symbol,
        "type": kucoin_interval,
        "startAt": start_time
    }
    
    response = requests.get(url, params=params, headers=headers, timeout=10)
    response.raise_for_status()
    data = response.json()
    
    if data and data.get('code') == '200000':
        raw_candles = data['data']
        # KuCoin format: [time, open, close, high, low, volume, turnover]
        df = pd.DataFrame(raw_candles, columns=['timestamp', 'open', 'close', 'high', 'low', 'volume', 'turnover'])
        df = df[['timestamp', 'open', 'high', 'low', 'close', 'volume']]
        
        # KuCoin returns data from newest to oldest, reverse it
        df = df.iloc[::-1].reset_index(drop=True)
        return df
    return None

def fetch_real_futures_data(symbol=config.SYMBOL, interval=config.TIMEFRAME, limit=config.DATA_LIMIT):
    clean_symbol = symbol.replace("/", "").replace(":", "").replace("-", "").upper()
    bybit_interval = convert_timeframe_to_bybit(interval)
    
    # 🕵️‍♂️ BROWSER SPOOFING HEADERS: Bypasses Cloudflare 403 Forbidden blocks on cloud platforms
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "application/json",
        "Accept-Language": "en-US,en;q=0.9"
    }
    
    # Try Primary Source (Bybit with Headers)
    try:
        print(f"🌍 [Railway Cloud Engine] Connecting to Bybit Premium Gateway for {clean_symbol}...")
        df = fetch_from_bybit(clean_symbol, bybit_interval, limit, headers)
        if df is not None and not df.empty:
            df['timestamp'] = pd.to_datetime(df['timestamp'].astype(float), unit='ms')
            for col in ['open', 'high', 'low', 'close', 'volume']:
                df[col] = df[col].astype(float)
            print(f"✅ Loaded {len(df)} candles via Bybit Spoofed Pipeline.")
            return df
    except Exception as e:
        print(f"⚠️ Bybit Firewall triggered: {e}")
        
    # Try Secondary Backup Source (KuCoin Network)
    try:
        df = fetch_from_kucoin_fallback(clean_symbol, interval, limit, headers)
        if df is not None and not df.empty:
            # KuCoin timestamps are in seconds, not milliseconds
            df['timestamp'] = pd.to_datetime(df['timestamp'].astype(float), unit='s')
            for col in ['open', 'high', 'low', 'close', 'volume']:
                df[col] = df[col].astype(float)
            print(f"✅ Loaded {len(df)} candles via KuCoin Institutional Pipeline.")
            return df
    except Exception as e:
        print(f"❌ All cloud data nodes rejected the request: {e}")
        return None