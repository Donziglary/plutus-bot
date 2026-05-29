# data_fetcher.py
import requests
import pandas as pd
import config

def convert_timeframe_to_bybit(tf_str):
    """Converts standard timeframes like '5m' or '1h' to Bybit Format."""
    tf_str = tf_str.lower()
    if 'm' in tf_str:
        return tf_str.replace('m', '')
    if 'h' in tf_str:
        hours = int(tf_str.replace('h', ''))
        return str(hours * 60)
    return tf_str

def fetch_real_futures_data(symbol=config.SYMBOL, interval=config.TIMEFRAME, limit=config.DATA_LIMIT):
    """
    Cloud-Friendly Data Fetcher using Bybit Institutional Nodes.
    Bypasses Binance 451 legal restrictions on cloud platforms like Railway.
    """
    # Standardize symbol for Bybit (e.g., SOLUSDT)
    clean_symbol = symbol.replace("/", "").replace(":", "").replace("-", "").upper()
    bybit_interval = convert_timeframe_to_bybit(interval)
    
    print(f"🌍 [Railway Cloud Engine] Fetching data for {clean_symbol} (Interval: {interval})...")
    
    url = "https://api.bybit.com/v5/market/kline"
    params = {
        "category": "linear",
        "symbol": clean_symbol,
        "interval": bybit_interval,
        "limit": str(limit)
    }
    
    try:
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        if data and data.get('retCode') == 0:
            raw_candles = data['result']['list']
            # Bybit format: [startTime, open, high, low, close, volume, turnover]
            df = pd.DataFrame(raw_candles, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume', 'turnover'])
            df = df[['timestamp', 'open', 'high', 'low', 'close', 'volume']]
            
            # Convert types
            for col in ['open', 'high', 'low', 'close', 'volume']:
                df[col] = df[col].astype(float)
                
            # Reverse to chronological order (past to present)
            df = df.iloc[::-1].reset_index(drop=True)
            df['timestamp'] = pd.to_datetime(df['timestamp'].astype(float), unit='ms')
            
            print(f"✅ Successfully loaded {len(df)} candles from cloud node.")
            return df
        else:
            print(f"❌ Bybit API Error: {data.get('retMsg')}")
            return None
            
    except Exception as e:
        print(f"❌ Network/API Error on Cloud: {e}")
        return None