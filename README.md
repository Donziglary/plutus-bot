# 🤖 PLUTUS QUANT TRADING ENGINE (v8.0 - Squeeze Sniper)

PLUTUS is an automated, enterprise-grade systematic algorithmic trading infrastructure engineered for crypto derivatives execution. Designed specifically for high-risk, high-reward momentum hunting, the framework is optimized to aggressively scale smaller capital deployments by capturing volatile breakout movements while suppressing overtrading during flat market regimes.

---

## 🏛️ System Architecture Overview

The system operates as a modular, decoupled execution pipeline designed for deployment within isolated cloud environments (e.g., Railway Container Engines).

**┌─────────────────┐      ┌──────────────────┐      ┌──────────────────┐
│   Data Layer    │ ───> │ Indicator Engine │ ───> │  Strategy Logic  │
│  (Bybit/KuCoin) │      │  (pandas-ta MTF) │      │ (Volatility SQZ) │
└─────────────────┘      └──────────────────┘      └──────────────────┘
│
v
┌─────────────────┐      ┌──────────────────┐      ┌──────────────────┐
│  Live Execution │ <─── │   Risk Engine    │ <─── │ Backtest Audit   │
│ (Webhooks/REST) │      │ (Dynamic ATR SL) │      │ (Slippage Model) │
└─────────────────┘      └──────────────────┘      └──────────────────┘**

The infrastructure consists of 4 core technical pillars:
1. **Data Acquisition Layer (`data_fetcher.py`):** Establishes premium, low-latency API connections to institutional-grade exchanges (Bybit Premium Gateway / KuCoin Institutional Nodes) with automatic failover fallback routing and firewall bypass handling.
2. **Signal & Indicator Matrix (`strategy.py`):** Translates raw OHLCV market data arrays into technical and statistical indicator matrices using high-performance vectorized operations via `pandas-ta`.
3. **Risk Management Core (`config.py`):** Calculates position sizes dynamically based on account equity, directional risk parameters, and geometric True Range volatility.
4. **Backtest & Simulation Engine (`main.py`):** Implements a discrete-event execution simulation environment that subjects setups to strict friction factors (taker fees, slippage penalties).

---

## 🧠 Core Strategy Mechanics: The Volatility Squeeze

PLUTUS V8.0 abandons naive lagging indicators in favor of a specialized **Volatility Squeeze and Expansion** model (inspired by John Carter's TTM Squeeze), designed to identify periods of extreme market compression and exploit the subsequent asymmetric explosive momentum.

### 1. Macro Trend Alignment (MTF Proxy)
To maintain structural alpha and avoid trading against major institutional order flows, the engine computes a 200-period Exponential Moving Average ($EMA$) on the execution timeframe (15m):
* **Long-only Bias:** $\text{Close} > \text{EMA}_{200}$ (Proxies a 1-Hour $EMA_{50}$ structural uptrend).
* **Short-only Bias:** $\text{Close} < \text{EMA}_{200}$ (Proxies a 1-Hour $EMA_{50}$ structural downtrend).

### 2. Volatility Compression Mechanics
The system measures the mathematical relationship between **Bollinger Bands (BB)** (measuring short-term standard deviation) and **Keltner Channels (KC)** (measuring Average True Range volatility):
$$\text{Squeeze On} = (\text{BB}_{\text{upper}} < \text{KC}_{\text{upper}}) \land (\text{BB}_{\text{lower}} > \text{KC}_{\text{lower}})$$

When Bollinger Bands compress *inside* the Keltner Channels, it signifies that the current market asset is consolidating into an unsustainably tight range—storing kinetic energy like a mechanical spring. The system activates `squeeze_loaded = True` if a squeeze was observed within the trailing 3 candles.

### 3. Explosive Entry Trigger
An execution order is only fired when the compressed spring releases violently, validated by volume and momentum confirmation metrics:
* **Long Entry:** $\text{Squeeze Loaded} \land (\text{Close} > \text{BB}_{\text{upper}}) \land (\text{RSI}_{14} > 55) \land (\text{Volume} > \text{Volume}_{\text{SMA20}} \times 1.3) \land (\text{Close} > \text{EMA}_{200})$
* **Short Entry:** $\text{Squeeze Loaded} \land (\text{Close} < \text{BB}_{\text{lower}}) \land (\text{RSI}_{14} < 45) \land (\text{Volume} > \text{Volume}_{\text{SMA20}} \times 1.3) \land (\text{Close} < \text{EMA}_{200})$

---

## 🛡️ Asymmetric Risk Management Matrix


[Stop Loss: 1.5x ATR] <─────── (Entry Price) ───────> [Take Profit: 3.5x ATR]


* **Dynamic Position Sizing:** Risk per trade is rigorously capped at a hard percentage of total account equity (e.g., 3% via `ACCOUNT_RISK_PER_TRADE`).
* **Volatility-Based SL:** The initial Stop Loss is dynamically derived using $\text{ATR}_{14} \times 1.5$. If a breakout fakes out or reverses, the bot cuts the position quickly before capital destruction occurs.
* **Aggressive Trend Ride (TP):** Take Profit is projected at $\text{ATR}_{14} \times 3.5$. This asymmetric payoff structure ensures that one successful breakout trade mathematically covers multiple minor stop-outs.

---

## 📊 Technical Execution & Performance Auditing

The backtester enforces rigorous institutional realism:
* **Taker Fee Simulation:** Built-in deduction of $0.04\%$ (`TAKER_FEE`) per execution, mirroring market order parameters on tier-1 derivative exchanges.
* **Slippage Modeling:** Applies a mandatory $0.10\%$ (`SLIPPAGE_PCT`) execution slippage penalty to simulate real-world liquidity gaps and order book execution delays during high-volatility spikes.

The historical results and execution logs are dynamically saved after every container run into `enterprise_backtest.csv` for algorithmic auditing.

---

## 🛠️ Repository File Directory & Layout

* `config.py`: Core hyperparameters containing asset specifications, leverage limits, risk tolerances, and mathematical indicator constants.
* `strategy.py`: Vectorized calculation pipelines for indicators (`calculate_indicators`) and the condition evaluator engines (`generate_signals`).
* `data_fetcher.py`: Low-level network interface dealing with exchange REST/WebSocket connections and packet failure management.
* `main.py`: Main container execution routine driving the data loops, invoking backtests, and managing pipeline states.

---

## 🚀 Deployment Instructions

PLUTUS is containerized and cloud-optimized for continuous execution environments.

### Local Development Setup
```bash
# Clone the repository
git clone [https://github.com/Donziglary/plutus-bot.git](https://github.com/Donziglary/plutus-bot.git)
cd plutus-bot

# Install environment dependencies
pip install pandas pandas-ta ccxt requests numpy
