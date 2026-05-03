"""
logger.py
---------
Saves each simulation run to logs/simulations.csv.

Why log?
  - Compare slippage across different order sizes (does 10 BTC cost 2× more
    slippage than 5 BTC, or much more?)
  - Track how market conditions affect execution quality
  - Build a personal dataset for future analysis
"""

import csv
import os
from datetime import datetime

from src.execution_engine import ExecutionResult


LOG_DIR  = os.path.join(os.path.dirname(__file__), "..", "logs")
LOG_FILE = os.path.join(LOG_DIR, "simulations.csv")

HEADERS = [
    "timestamp", "symbol", "source", "side",
    "order_size", "filled_size", "best_price",
    "avg_fill_price", "total_cost", "slippage_abs",
    "slippage_pct", "levels_consumed", "partial_fill",
]


def init_logger():
    """Create logs directory and CSV header if needed."""
    os.makedirs(LOG_DIR, exist_ok=True)
    if not os.path.exists(LOG_FILE) or os.path.getsize(LOG_FILE) == 0:
        with open(LOG_FILE, "w", newline="") as f:
            csv.DictWriter(f, fieldnames=HEADERS).writeheader()


def log_result(result: ExecutionResult, symbol: str, source: str):
    """Append one simulation run to the CSV log."""
    row = {
        "timestamp":       datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "symbol":          symbol.upper(),
        "source":          source,
        "side":            result.side,
        "order_size":      result.order_size,
        "filled_size":     result.filled_size,
        "best_price":      result.best_price,
        "avg_fill_price":  result.average_fill_price,
        "total_cost":      result.total_cost,
        "slippage_abs":    result.slippage_abs,
        "slippage_pct":    result.slippage_pct,
        "levels_consumed": result.levels_consumed,
        "partial_fill":    result.partial_fill,
    }
    with open(LOG_FILE, "a", newline="") as f:
        csv.DictWriter(f, fieldnames=HEADERS).writerow(row)
