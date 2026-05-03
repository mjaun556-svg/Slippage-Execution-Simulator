"""
main.py
-------
Slippage & Execution Simulator — Entry Point

Simulates how a market order (buy or sell) gets filled against a real
order book, showing:
  - Which price levels were consumed
  - The average fill price
  - Total slippage vs the best available price

Usage examples:
  # Interactive mode (prompts you for inputs)
  python main.py

  # Direct mode — buy 2 BTC using sample data
  python main.py --side buy --size 2.0

  # Sell 5 ETH using live Binance data
  python main.py --side sell --size 5.0 --symbol ETHUSDT --source live

  # Buy 10 BTC, skip CSV logging
  python main.py --side buy --size 10.0 --no-log

No API key required. Binance REST endpoint is public.
"""

import argparse
import sys
import os

# Make src/ importable when running from project root
sys.path.insert(0, os.path.dirname(__file__))

from src.execution_engine import simulate_execution
from src.order_book        import get_order_book
from src.display           import print_banner, print_order_book, print_fill_steps, print_summary
from src.logger            import init_logger, log_result


# ── CLI Argument Parser ────────────────────────────────────────────────────────

def parse_args():
    parser = argparse.ArgumentParser(
        description="Slippage & Execution Simulator — simulates market order fills"
    )
    parser.add_argument("--side",   type=str,   choices=["buy", "sell"],
                        help="Trade direction: buy or sell")
    parser.add_argument("--size",   type=float,
                        help="Order size in base currency units (e.g. 2.5 for 2.5 BTC)")
    parser.add_argument("--symbol", type=str,   default="BTCUSDT",
                        help="Trading pair (default: BTCUSDT)")
    parser.add_argument("--source", type=str,   default="sample",
                        choices=["sample", "live"],
                        help="Order book data source (default: sample)")
    parser.add_argument("--no-log", action="store_true",
                        help="Disable CSV logging")
    return parser.parse_args()


# ── Interactive Input ──────────────────────────────────────────────────────────

def prompt_inputs():
    """
    Ask the user for side and size interactively.
    Used when --side and --size are not provided as CLI args.
    """
    print("  Enter trade details (or press Ctrl+C to quit)\n")

    while True:
        side = input("  Side  [buy / sell]: ").strip().lower()
        if side in ("buy", "sell"):
            break
        print("  Please enter 'buy' or 'sell'.")

    while True:
        try:
            size = float(input("  Size  (e.g. 1.5 for 1.5 BTC): ").strip())
            if size > 0:
                break
            print("  Size must be a positive number.")
        except ValueError:
            print("  Please enter a valid number.")

    return side, size


# ── Main ───────────────────────────────────────────────────────────────────────

def main():
    args = parse_args()

    print_banner()

    # Determine side and size — from CLI args or interactive prompts
    if args.side and args.size:
        side = args.side
        size = args.size
    else:
        side, size = prompt_inputs()

    symbol = args.symbol.upper()
    source = args.source
    enable_log = not args.no_log

    print(f"\n  Simulating: {side.upper()} {size} {symbol[:3]}  |  "
          f"Book source: {source.upper()}\n")

    # ── Step 1: Get order book ─────────────────────────────────────────────────
    try:
        book = get_order_book(symbol=symbol, source=source)
    except (ValueError, RuntimeError) as e:
        print(f"\n  ❌ Error loading order book: {e}\n")
        sys.exit(1)

    # ── Step 2: Display the book ───────────────────────────────────────────────
    print_order_book(book, symbol, levels=10)

    # ── Step 3: Simulate execution ────────────────────────────────────────────
    try:
        result = simulate_execution(book, order_size=size, side=side)
    except ValueError as e:
        print(f"\n  ❌ Simulation error: {e}\n")
        sys.exit(1)

    # ── Step 4: Display fill walkthrough ──────────────────────────────────────
    print_fill_steps(result)

    # ── Step 5: Display summary ───────────────────────────────────────────────
    print_summary(result)

    # ── Step 6: Log to CSV ────────────────────────────────────────────────────
    if enable_log:
        init_logger()
        log_result(result, symbol=symbol, source=source)
        print(f"  📁 Result saved to logs/simulations.csv\n")

    # ── Step 7: Ask if user wants to run another simulation ───────────────────
    try:
        again = input("  Run another simulation? [y/n]: ").strip().lower()
        if again == "y":
            print()
            main()  # Simple recursive re-run (fine for CLI tool depth)
    except (KeyboardInterrupt, EOFError):
        print("\n  Goodbye.\n")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n  Interrupted. Goodbye.\n")
