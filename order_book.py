"""
order_book.py
-------------
Provides order book data for the simulator.

Two modes:
  1. SAMPLE  — a hardcoded realistic BTC/USDT order book (no internet needed)
  2. LIVE    — fetches the real order book from Binance REST API (no key needed)

The live fetch uses Binance's public endpoint:
  GET https://api.binance.com/api/v3/depth?symbol=BTCUSDT&limit=20

Both modes return the same structure so the execution engine doesn't care
which source was used.
"""

import json
import urllib.request
import urllib.error
from src.execution_engine import Level


# ── Binance REST Fetch (no API key required) ───────────────────────────────────

BINANCE_DEPTH_URL = "https://api.binance.com/api/v3/depth"


def fetch_live_order_book(symbol: str = "BTCUSDT", limit: int = 20) -> dict:
    """
    Fetch a real order book snapshot from Binance REST API.

    Args:
        symbol : Trading pair, e.g. "BTCUSDT", "ETHUSDT"
        limit  : Number of levels to fetch (5, 10, 20, 50, 100, 500, 1000)

    Returns:
        dict with "asks" and "bids" as lists of Level objects.

    Raises:
        RuntimeError if the request fails (e.g. no internet, rate limit).
    """
    url = f"{BINANCE_DEPTH_URL}?symbol={symbol.upper()}&limit={limit}"

    try:
        with urllib.request.urlopen(url, timeout=5) as response:
            raw = json.loads(response.read().decode())
    except urllib.error.URLError as e:
        raise RuntimeError(
            f"Could not reach Binance API: {e}\n"
            "Try running with --source sample instead."
        )

    # Binance returns: { "bids": [["price", "qty"], ...], "asks": [...] }
    # Bids are already sorted highest-first; asks are lowest-first.
    return {
        "bids": [Level(float(p), float(q)) for p, q in raw["bids"]],
        "asks": [Level(float(p), float(q)) for p, q in raw["asks"]],
    }


# ── Sample Order Book (offline / demo mode) ────────────────────────────────────

def get_sample_order_book(symbol: str = "BTCUSDT") -> dict:
    """
    Return a realistic hardcoded order book for demo/offline use.

    Prices and sizes reflect a typical BTC/USDT book snapshot.
    The spread is intentionally tight (as it would be on a liquid exchange).

    Returns:
        dict with "asks" and "bids" as lists of Level objects.
    """
    if symbol.upper() == "BTCUSDT":
        # Best ask at top (lowest price a seller will accept)
        asks = [
            Level(67_450.00, 0.121),
            Level(67_451.50, 0.340),
            Level(67_453.00, 0.875),
            Level(67_455.00, 1.200),
            Level(67_458.00, 2.540),
            Level(67_460.00, 1.800),
            Level(67_463.00, 3.100),
            Level(67_467.00, 4.500),
            Level(67_470.00, 2.200),
            Level(67_475.00, 5.000),
            Level(67_480.00, 7.300),
            Level(67_490.00, 8.100),
            Level(67_500.00, 10.000),
            Level(67_510.00, 6.500),
            Level(67_520.00, 12.000),
        ]

        # Best bid at top (highest price a buyer will pay)
        bids = [
            Level(67_449.00, 0.095),
            Level(67_447.50, 0.210),
            Level(67_446.00, 0.580),
            Level(67_444.00, 1.100),
            Level(67_442.00, 2.300),
            Level(67_440.00, 1.650),
            Level(67_437.00, 2.900),
            Level(67_433.00, 4.200),
            Level(67_430.00, 1.980),
            Level(67_425.00, 4.700),
            Level(67_420.00, 6.800),
            Level(67_410.00, 7.500),
            Level(67_400.00, 9.200),
            Level(67_390.00, 5.800),
            Level(67_380.00, 11.000),
        ]

    elif symbol.upper() == "ETHUSDT":
        asks = [
            Level(3_520.00, 1.50),
            Level(3_520.50, 3.20),
            Level(3_521.00, 5.80),
            Level(3_522.00, 8.40),
            Level(3_523.50, 12.10),
            Level(3_525.00, 15.60),
            Level(3_527.00, 20.30),
            Level(3_530.00, 25.00),
        ]
        bids = [
            Level(3_519.50, 1.10),
            Level(3_519.00, 2.80),
            Level(3_518.00, 5.20),
            Level(3_516.50, 7.90),
            Level(3_515.00, 11.40),
            Level(3_513.00, 14.80),
            Level(3_510.00, 18.60),
            Level(3_507.00, 22.00),
        ]

    else:
        raise ValueError(
            f"No sample data for symbol '{symbol}'. "
            "Use BTCUSDT, ETHUSDT, or run with --source live."
        )

    return {"asks": asks, "bids": bids}


def get_order_book(symbol: str = "BTCUSDT", source: str = "sample") -> dict:
    """
    Unified entry point — picks sample or live based on the source argument.

    Args:
        symbol : Trading pair string
        source : "sample" (default) or "live"

    Returns:
        dict with "asks" and "bids" lists of Level objects.
    """
    if source == "live":
        print(f"  [+] Fetching live order book from Binance ({symbol})...")
        book = fetch_live_order_book(symbol)
        print(f"  [+] Got {len(book['bids'])} bid levels, {len(book['asks'])} ask levels.\n")
        return book
    else:
        return get_sample_order_book(symbol)
