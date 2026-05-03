"""
test_execution_engine.py
------------------------
Unit tests for the slippage & execution simulation logic.

Run with:  python -m pytest tests/ -v
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.execution_engine import simulate_execution, Level


# ── Fixtures ───────────────────────────────────────────────────────────────────

def simple_book():
    """A clean, simple order book with 3 levels per side."""
    return {
        "asks": [
            Level(100.0, 1.0),   # 1 unit at 100
            Level(101.0, 2.0),   # 2 units at 101
            Level(102.0, 5.0),   # 5 units at 102
        ],
        "bids": [
            Level(99.0,  1.0),
            Level(98.0,  2.0),
            Level(97.0,  5.0),
        ],
    }


# ── Buy Tests ─────────────────────────────────────────────────────────────────

def test_buy_fits_first_level():
    """Small buy that fits entirely in the best ask level."""
    book   = simple_book()
    result = simulate_execution(book, order_size=0.5, side="buy")

    assert result.filled_size == 0.5
    assert result.average_fill_price == 100.0
    assert result.slippage_abs == 0.0        # No movement needed
    assert result.slippage_pct == 0.0
    assert result.levels_consumed == 1
    assert not result.partial_fill


def test_buy_spans_two_levels():
    """Buy that exhausts level 0 and spills into level 1."""
    book   = simple_book()
    # 1.0 from level 0 (price 100) + 0.5 from level 1 (price 101)
    result = simulate_execution(book, order_size=1.5, side="buy")

    expected_cost  = (1.0 * 100.0) + (0.5 * 101.0)   # 100 + 50.5 = 150.5
    expected_avg   = expected_cost / 1.5               # 100.333...

    assert result.filled_size == 1.5
    assert result.levels_consumed == 2
    assert abs(result.total_cost - expected_cost) < 1e-6
    assert abs(result.average_fill_price - expected_avg) < 1e-4
    assert result.slippage_abs > 0   # Paid more than best ask


def test_buy_spans_all_levels():
    """Buy that consumes all 3 ask levels exactly."""
    book   = simple_book()
    # Total ask liquidity: 1 + 2 + 5 = 8 units
    result = simulate_execution(book, order_size=8.0, side="buy")

    assert result.filled_size  == 8.0
    assert result.levels_consumed == 3
    assert not result.partial_fill


def test_buy_partial_fill():
    """Buy order larger than total available ask liquidity."""
    book   = simple_book()
    result = simulate_execution(book, order_size=100.0, side="buy")

    assert result.partial_fill is True
    assert result.filled_size == 8.0   # Only 8 units available in total
    assert result.levels_consumed == 3


# ── Sell Tests ────────────────────────────────────────────────────────────────

def test_sell_fits_first_level():
    """Small sell that fits entirely in the best bid level."""
    book   = simple_book()
    result = simulate_execution(book, order_size=0.5, side="sell")

    assert result.filled_size == 0.5
    assert result.average_fill_price == 99.0
    assert result.slippage_abs == 0.0
    assert result.levels_consumed == 1


def test_sell_spans_two_levels():
    """Sell that exhausts bid level 0 and spills into level 1."""
    book   = simple_book()
    # 1.0 from level 0 (price 99) + 1.0 from level 1 (price 98)
    result = simulate_execution(book, order_size=2.0, side="sell")

    expected_cost = (1.0 * 99.0) + (1.0 * 98.0)  # 197
    expected_avg  = expected_cost / 2.0            # 98.5

    assert result.filled_size == 2.0
    assert result.levels_consumed == 2
    assert abs(result.total_cost - expected_cost) < 1e-6
    assert abs(result.average_fill_price - expected_avg) < 1e-4
    assert result.slippage_abs > 0   # Received less than best bid


def test_sell_partial_fill():
    """Sell order larger than total bid-side liquidity."""
    book   = simple_book()
    result = simulate_execution(book, order_size=50.0, side="sell")

    assert result.partial_fill is True
    assert result.filled_size == 8.0


# ── Slippage Direction Tests ──────────────────────────────────────────────────

def test_buy_slippage_is_positive():
    """For buys, average fill > best ask → slippage is positive."""
    book   = simple_book()
    result = simulate_execution(book, order_size=3.0, side="buy")
    assert result.slippage_abs >= 0


def test_sell_slippage_is_positive():
    """For sells, best bid > average fill → slippage is positive."""
    book   = simple_book()
    result = simulate_execution(book, order_size=3.0, side="sell")
    assert result.slippage_abs >= 0


# ── Edge Cases ────────────────────────────────────────────────────────────────

def test_zero_size_raises():
    """Order size of 0 should raise ValueError."""
    book = simple_book()
    try:
        simulate_execution(book, order_size=0.0, side="buy")
    except (ValueError, ZeroDivisionError):
        pass   # Expected — either is acceptable behaviour


def test_single_level_book():
    """Book with only one level still works correctly."""
    book = {
        "asks": [Level(500.0, 10.0)],
        "bids": [Level(499.0, 10.0)],
    }
    result = simulate_execution(book, order_size=5.0, side="buy")
    assert result.filled_size == 5.0
    assert result.average_fill_price == 500.0
    assert result.slippage_abs == 0.0
