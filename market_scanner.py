# market_scanner.py
import requests

def test_endpoint(name, url, params):
    print(f"🔍 Testing {name}...")
    try:
        response = requests.get(url, params=params, timeout=7)
        if response.status_code == 200:
            print(f"✅ {name} is WIDE OPEN! (Status 200)")
            return True
        else:
            print(f"❌ {name} returned status code: {response.status_code}")
            return False
    except Exception as e:
        print(f"🚨 {name} FAILED (Timeout/Connection Error)")
        return False

print("=== COALITION NETWORK DIAGNOSTICS ===")

# 1. Test Bybit Futures (Highly stable, often completely unblocked in Iran)
bybit_url = "https://api.bybit.com/v5/market/kline"
bybit_params = {"category": "linear", "symbol": "BTCUSDT", "interval": "60", "limit": "5"}
bybit_res = test_endpoint("Bybit Futures Direct API", bybit_url, bybit_params)

# 2. Test XT.COM Futures Direct (Bypassing CCXT's wallet checks)
xt_url = "https://fapi.xt.com/future/market/v1/public/q/kline"
xt_params = {"symbol": "btc_usdt", "num": "5", "period": "1h"}
xt_res = test_endpoint("XT.COM Futures Direct API", xt_url, xt_params)

# 3. Test Binance Futures Direct 
binance_url = "https://fapi.binance.com/fapi/v1/klines"
binance_params = {"symbol": "BTCUSDT", "interval": "1h", "limit": "5"}
binance_res = test_endpoint("Binance Futures Direct API", binance_url, binance_params)

print("\n=====================================")
if not any([bybit_res, xt_res, binance_res]):
    print("💡 Micro-tip: All direct API connections timed out. Your current network/VPN is blocking raw SSL connections. Try changing your VPN protocol to vless/reality or activate Electro DNS.")
else:
    print("👍 We found an open highway! Let's update the data fetcher.")