# main.py
import sys
from backtester import run_enterprise_backtest

def main():
    print("==================================================")
    print("🤖 PLUTUS QUANT TRADING ENGINE v4.0 - ACTIVE")
    print("==================================================")
    
    try:
        # Run the backtest sequence
        run_enterprise_backtest()
        print("\n🎯 Backtest sequence finished inside cloud container.")
    except Exception as e:
        print(f"🚨 Critical Failure in Main Loop: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()