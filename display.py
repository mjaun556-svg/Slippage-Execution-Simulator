"""
display.py
----------
All terminal output lives here — keeps main.py clean.

Prints:
  1. The order book (bids and asks side by side)
  2. Step-by-step fill breakdown (which levels were consumed)
  3. Final execution summary with slippage analysis
"""

from src.execution_engine import ExecutionResult, Level


# ── ANSI colour helpers ────────────────────────────────────────────────────────
# (Works on macOS, Linux, and Windows 10+ terminals)

GREEN  = "\033[92m"
RED    = "\033[91m"
YELLOW = "\033[93m"
CYAN   = "\033[96m"
BOLD   = "\033[1m"
DIM    = "\033[2m"
RESET  = "\033[0m"

W = 62   # Line width for separator bars


def _sep(char="─"):
    print(char * W)


def print_order_book(book: dict, symbol: str, levels: int = 10):
    """
    Print the top N levels of the order book in a readable two-column table.

    Args:
        book   : dict with "bids" and "asks" lists of Level objects
        symbol : Trading pair label
        levels : How many levels to show
    """
    asks = book["asks"][:levels]
    bids = book["bids"][:levels]

    print(f"\n{BOLD}{'─'*W}{RESET}")
    print(f"{BOLD}  📖 ORDER BOOK SNAPSHOT — {symbol.upper()}{RESET}")
    print(f"{'─'*W}")
    print(f"  {BOLD}{'ASK PRICE':>14}  {'ASK QTY':>10}  {'BID PRICE':>14}  {'BID QTY':>10}{RESET}")
    print(f"{'─'*W}")

    max_rows = max(len(asks), len(bids))
    for i in range(max_rows):
        ask_str = bid_str = ""

        if i < len(asks):
            a = asks[i]
            # Mark the best ask (top of book)
            tag = " ← best ask" if i == 0 else ""
            ask_str = f"{RED}{a.price:>14,.2f}{RESET}  {a.quantity:>10.4f}{DIM}{tag}{RESET}"
        else:
            ask_str = " " * 30

        if i < len(bids):
            b = bids[i]
            tag = " ← best bid" if i == 0 else ""
            bid_str = f"{GREEN}{b.price:>14,.2f}{RESET}  {b.quantity:>10.4f}{DIM}{tag}{RESET}"

        print(f"  {ask_str}  {bid_str}")

    _sep()
    spread = asks[0].price - bids[0].price if asks and bids else 0
    print(f"  {DIM}Spread: {spread:,.2f}   "
          f"Best Ask: {asks[0].price:,.2f}   Best Bid: {bids[0].price:,.2f}{RESET}")
    print()


def print_fill_steps(result: ExecutionResult):
    """
    Print a step-by-step table showing how each order book level was consumed.
    This is the most educational part — shows exactly how liquidity gets eaten.
    """
    side_label = "ASK" if result.side == "BUY" else "BID"
    color      = RED   if result.side == "BUY" else GREEN

    print(f"\n{BOLD}  ⚡ EXECUTION WALKTHROUGH  ({result.side} order — consuming {side_label} side){RESET}")
    _sep()
    print(f"  {BOLD}{'Level':>6}  {'Price':>12}  {'Available':>10}  {'Filled':>10}  {'Cost (USDT)':>14}  {'Remaining':>10}{RESET}")
    _sep()

    remaining = result.order_size
    for step in result.fill_steps:
        remaining -= step.quantity_filled
        print(
            f"  {step.level_index:>6}  "
            f"{color}{step.price:>12,.2f}{RESET}  "
            f"{step.quantity_available:>10.4f}  "
            f"{YELLOW}{step.quantity_filled:>10.4f}{RESET}  "
            f"{step.cost:>14,.4f}  "
            f"{max(remaining, 0):>10.4f}"
        )

    _sep()

    if result.partial_fill:
        unfilled = result.order_size - result.filled_size
        print(f"\n  {YELLOW}⚠  Partial fill: {unfilled:.4f} units could not be filled "
              f"(not enough liquidity in the book){RESET}\n")


def print_summary(result: ExecutionResult):
    """
    Print the final execution summary: prices, costs, and slippage analysis.
    """
    color = RED if result.side == "BUY" else GREEN

    print(f"\n{BOLD}  📊 EXECUTION SUMMARY{RESET}")
    _sep("═")

    rows = [
        ("Side",               f"{color}{result.side}{RESET}"),
        ("Order Size",         f"{result.order_size:.4f} units"),
        ("Filled Size",        f"{result.filled_size:.4f} units"),
        ("Best Price (top of book)",  f"{result.best_price:>14,.4f} USDT"),
        ("Average Fill Price",        f"{result.average_fill_price:>14,.4f} USDT"),
        ("Total Cost / Proceeds",     f"{result.total_cost:>14,.4f} USDT"),
        ("Levels Consumed",    str(result.levels_consumed)),
    ]
    for label, value in rows:
        print(f"  {label:<30} {value}")

    _sep()

    # Slippage block — highlight bad slippage in yellow/red
    slip_color = YELLOW if result.slippage_pct < 0.5 else RED
    print(f"\n{BOLD}  💸 SLIPPAGE ANALYSIS{RESET}")
    print(f"  {'Absolute Slippage':<30} "
          f"{slip_color}{result.slippage_abs:>10,.4f} USDT per unit{RESET}")
    print(f"  {'Slippage %':<30} "
          f"{slip_color}{result.slippage_pct:>9,.4f}%{RESET}")

    # Plain-English verdict
    print()
    if result.slippage_pct < 0.05:
        verdict = f"{GREEN}✅  Excellent execution — minimal slippage.{RESET}"
    elif result.slippage_pct < 0.20:
        verdict = f"{YELLOW}🟡  Acceptable slippage — typical for mid-size orders.{RESET}"
    elif result.slippage_pct < 0.50:
        verdict = f"{YELLOW}⚠   Noticeable slippage — consider splitting into smaller orders.{RESET}"
    else:
        verdict = f"{RED}🔴  High slippage — this order is too large for current liquidity.{RESET}"

    print(f"  {verdict}")

    if result.partial_fill:
        print(f"\n  {RED}⚠  Note: Order was only PARTIALLY filled due to insufficient liquidity.{RESET}")

    _sep("═")
    print()


def print_banner():
    """Print the startup banner."""
    print(f"""
{BOLD}{CYAN}
  ╔══════════════════════════════════════════════╗
  ║   Slippage & Execution Simulator             ║
  ║   Real-world order book fill simulation      ║
  ╚══════════════════════════════════════════════╝
{RESET}""")
