"""
execution_engine.py
--------------------
The "brain" of the simulator.

This module walks through the order book level by level and fills
an order exactly the way a real exchange matching engine does.

Key concepts:
  - A BUY  order consumes the ASK side (cheapest asks first)
  - A SELL order consumes the BID side (highest bids first)
  - When one level runs out of liquidity, we move to the next price level
  - The difference between the best price and the average fill price = SLIPPAGE
"""

from dataclasses import dataclass, field
from typing import Literal


# ── Data Structures ────────────────────────────────────────────────────────────

@dataclass
class Level:
    """A single price level in the order book."""
    price: float
    quantity: float


@dataclass
class FillStep:
    """Records exactly how much was filled at each price level."""
    level_index: int          # 0 = best price, 1 = next best, etc.
    price: float              # Price at this level
    quantity_available: float # How much was sitting at this level
    quantity_filled: float    # How much we actually consumed here
    cost: float               # quantity_filled × price


@dataclass
class ExecutionResult:
    """The full result of simulating one trade."""
    side: str                          # "BUY" or "SELL"
    order_size: float                  # What the user requested
    filled_size: float                 # What actually got filled
    best_price: float                  # Top-of-book price (ideal)
    average_fill_price: float          # Actual average across all levels
    total_cost: float                  # Total base currency spent / received
    slippage_pct: float                # (avg_fill - best) / best × 100
    slippage_abs: float                # avg_fill - best  (in price units)
    levels_consumed: int               # How many book levels were needed
    partial_fill: bool                 # True if book ran out of liquidity
    fill_steps: list = field(default_factory=list)  # Level-by-level breakdown


# ── Core Engine ────────────────────────────────────────────────────────────────

def simulate_execution(
    order_book: dict,
    order_size: float,
    side: Literal["buy", "sell"],
) -> ExecutionResult:
    """
    Walk the order book and simulate how a market order gets filled.

    Args:
        order_book : dict with keys "asks" and "bids",
                     each a list of Level objects sorted best-first.
        order_size : How many units (e.g. BTC) the trader wants to buy/sell.
        side       : "buy"  → consumes ask side (cheapest first)
                     "sell" → consumes bid side (highest first)

    Returns:
        ExecutionResult with full breakdown of the simulated fill.
    """

    # BUY  → we walk up the ask side (lowest ask = best for buyer)
    # SELL → we walk down the bid side (highest bid = best for seller)
    levels: list[Level] = order_book["asks"] if side == "buy" else order_book["bids"]

    if not levels:
        raise ValueError(f"Order book has no {'ask' if side == 'buy' else 'bid'} levels.")

    best_price     = levels[0].price   # The ideal price (top of book)
    remaining      = order_size        # How much is still left to fill
    total_cost     = 0.0
    fill_steps     = []

    # Walk through each price level until the order is fully filled
    # or we run out of liquidity in the book
    for i, level in enumerate(levels):

        if remaining <= 0:
            break  # Order fully filled — stop walking

        # How much can we fill at this level?
        fill_qty = min(remaining, level.quantity)
        cost_here = fill_qty * level.price

        # Record this step
        fill_steps.append(FillStep(
            level_index        = i,
            price              = level.price,
            quantity_available = level.quantity,
            quantity_filled    = fill_qty,
            cost               = cost_here,
        ))

        total_cost += cost_here
        remaining  -= fill_qty   # Reduce what's still needed

    # How much did we actually fill?
    filled_size = order_size - remaining

    # Weighted average fill price across all levels touched
    avg_fill_price = total_cost / filled_size if filled_size > 0 else best_price

    # Slippage: how far did we drift from the best price?
    if side == "buy":
        # For buys, we pay MORE than the best ask → slippage is positive
        slippage_abs = avg_fill_price - best_price
    else:
        # For sells, we receive LESS than the best bid → slippage is negative
        slippage_abs = best_price - avg_fill_price

    slippage_pct = (slippage_abs / best_price) * 100 if best_price > 0 else 0.0

    return ExecutionResult(
        side               = side.upper(),
        order_size         = order_size,
        filled_size        = filled_size,
        best_price         = best_price,
        average_fill_price = round(avg_fill_price, 6),
        total_cost         = round(total_cost, 6),
        slippage_pct       = round(slippage_pct, 6),
        slippage_abs       = round(slippage_abs, 6),
        levels_consumed    = len(fill_steps),
        partial_fill       = remaining > 0,
        fill_steps         = fill_steps,
    )
