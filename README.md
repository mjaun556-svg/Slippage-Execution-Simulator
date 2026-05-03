# 📉 Slippage & Execution Simulator

A Python CLI tool that simulates how a **market order gets filled against a real order book** — showing the average execution price, total slippage, and a step-by-step breakdown of which price levels were consumed.

Works with **hardcoded sample data** (zero setup) or a **live Binance order book** (no API key needed).

---

## 🧠 What Is Slippage?

When you place a **market order** on an exchange, you don't always get the price you see on screen.

Here's why:

> Imagine BTC is showing **$67,450** (best ask). You want to buy **5 BTC**.  
> But there's only **0.12 BTC** available at $67,450.  
> The next level has **0.34 BTC** at $67,451.50.  
> The next has **0.87 BTC** at $67,453.00 … and so on.  
>  
> Your order "eats through" multiple levels until it's fully filled.  
> Your **actual average price** ends up being **$67,462** — not $67,450.  
>  
> That $12 difference is **slippage**.

### The Formula

```
Slippage (abs) = Average Fill Price − Best Price
Slippage (%)   = (Slippage abs / Best Price) × 100
```

---

## 💡 Why Liquidity Impacts Execution

**Liquidity** = how much volume is sitting at each price level in the order book.

| Scenario | Effect on Execution |
|----------|---------------------|
| Deep book (lots of volume at each level) | Small slippage — your order gets filled near the best price |
| Thin book (low volume per level) | Large slippage — your order jumps across many levels |
| Large order on a thin book | Severe slippage — potentially moves the market against you |
| Small order on any book | Near-zero slippage — fits in the first level |

This is why professionals **split large orders** into smaller chunks (a strategy called **TWAP** or **VWAP**), and why liquidity is the most important factor when evaluating execution quality.

---

## 🌍 Real-World Relevance

| Who cares | Why |
|-----------|-----|
| **Retail traders** | Understand why your fill is worse than the displayed price |
| **Algo traders** | Model execution costs before deploying a strategy |
| **Quants** | Slippage is a direct drag on backtested P&L |
| **Market makers** | Slippage models determine bid-ask spread pricing |
| **Risk managers** | Large liquidations have predictable slippage costs |

Even a **0.1% slippage** on a $100,000 trade = $100 lost per trade. At 10 trades/day that's $1,000/day — which is why execution quality matters as much as alpha.

---

## 🚀 Quick Start

### 1. Clone the repo
```bash
git clone https://github.com/YOUR_USERNAME/slippage-execution-simulator.git
cd slippage-execution-simulator
```

### 2. Install dependencies
```bash
pip install -r requirements.txt
```

### 3. Run the simulator

```bash
# Interactive mode — prompts you for inputs
python main.py

# Buy 2 BTC using sample data
python main.py --side buy --size 2.0

# Sell 5 ETH using sample data
python main.py --side sell --size 5.0 --symbol ETHUSDT

# Buy 0.5 BTC using live Binance order book
python main.py --side buy --size 0.5 --source live

# Run without saving to CSV
python main.py --side buy --size 1.0 --no-log
```

> **No API key required.** The live source uses Binance's free public REST endpoint.

---

## 📺 Sample Output

```
╔══════════════════════════════════════════════╗
║   Slippage & Execution Simulator             ║
║   Real-world order book fill simulation      ║
╚══════════════════════════════════════════════╝

──────────────────────────────────────────────────────────────
  📖 ORDER BOOK SNAPSHOT — BTCUSDT
──────────────────────────────────────────────────────────────
       ASK PRICE     ASK QTY       BID PRICE     BID QTY
──────────────────────────────────────────────────────────────
       67,450.00      0.1210       67,449.00      0.0950  ← best bid
       67,451.50      0.3400       67,447.50      0.2100
       67,453.00      0.8750       67,446.00      0.5800
       67,455.00      1.2000       67,444.00      1.1000
       ...

  ⚡ EXECUTION WALKTHROUGH  (BUY order — consuming ASK side)
──────────────────────────────────────────────────────────────
  Level         Price   Available     Filled  Cost (USDT)   Remaining
──────────────────────────────────────────────────────────────
      0     67,450.00      0.1210      0.1210    8,161.45      1.8790
      1     67,451.50      0.3400      0.3400   22,933.51      1.5390
      2     67,453.00      0.8750      0.8750   59,021.38      0.6640
      3     67,455.00      1.2000      0.6640   44,789.92      0.0000

  📊 EXECUTION SUMMARY
══════════════════════════════════════════════════════════════
  Side                           BUY
  Order Size                     2.0000 units
  Filled Size                    2.0000 units
  Best Price (top of book)      67,450.0000 USDT
  Average Fill Price            67,452.8818 USDT
  Total Cost / Proceeds        134,906.26 USDT
  Levels Consumed               4

  💸 SLIPPAGE ANALYSIS
  Absolute Slippage              2.8818 USDT per unit
  Slippage %                     0.0043%

  ✅  Excellent execution — minimal slippage.
══════════════════════════════════════════════════════════════
```

---

## 📁 Project Structure

```
slippage-execution-simulator/
│
├── main.py                      # CLI entry point & interactive prompts
│
├── src/
│   ├── execution_engine.py      # Core fill simulation logic (walks the book)
│   ├── order_book.py            # Sample data + live Binance REST fetch
│   ├── display.py               # All terminal output & formatting
│   └── logger.py                # CSV logger → logs/simulations.csv
│
├── tests/
│   └── test_execution_engine.py # Unit tests (10 test cases)
│
├── logs/
│   └── simulations.csv          # Auto-generated at runtime (gitignored)
│
├── requirements.txt             # Only pytest needed (no heavy libraries)
├── .gitignore
└── README.md
```

---

## ⚙️ How the Engine Works

```
User Input (side, size)
        │
        ▼
  Get Order Book ──── sample: hardcoded realistic data
        │          └── live:   Binance REST /api/v3/depth
        ▼
  simulate_execution()              ← execution_engine.py
  │
  │  for each price level:
  │    fill = min(remaining, level.quantity)
  │    cost += fill × price
  │    remaining -= fill
  │    record FillStep
  │
  └─ avg_price = total_cost / filled_size
     slippage  = avg_price − best_price
        │
        ▼
  print_order_book()               ← display.py
  print_fill_steps()
  print_summary()
        │
        ▼
  log_result()                     ← logger.py → CSV
```

---

## 🧪 Running Tests

```bash
python -m pytest tests/ -v
```

Covers: single-level fills, multi-level spills, partial fills, buy/sell slippage direction, and edge cases.

---

## 📈 Ideas to Extend

| Extension | Difficulty |
|-----------|------------|
| Plot slippage vs order size curve (`matplotlib`) | ⭐ Easy |
| Simulate TWAP: split order into N chunks | ⭐⭐ Medium |
| Compare slippage across multiple symbols | ⭐⭐ Medium |
| Add WebSocket (live streaming book updates) | ⭐⭐⭐ Hard |
| Model market impact (price permanently moves) | ⭐⭐⭐ Hard |

---

## 📦 Dependencies

| Library | Purpose | Version |
|---------|---------|---------|
| `pytest` | Unit testing (optional) | 8.3.5 |

Everything else uses Python's standard library: `json`, `csv`, `urllib`, `argparse`, `dataclasses`, `datetime`.

---

## 🔗 Data Source

Live mode uses Binance's free public REST API:
```
GET https://api.binance.com/api/v3/depth?symbol=BTCUSDT&limit=20
```
No authentication needed. Full docs: [Binance API — Order Book](https://binance-docs.github.io/apidocs/spot/en/#order-book)

---

## 📄 License

MIT — free to use, fork, and extend.
