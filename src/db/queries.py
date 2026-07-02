"""M2 handoff — DuckDB 조회 인터페이스.

M2 feature-engineer agent가 이 함수들로 DuckDB에서 데이터를 꺼내 씀.
M1 → M2 계승 표준 인터페이스.
"""

from __future__ import annotations

import pandas as pd

from src.db.connection import get_connection
from src.utils.logging_config import get_logger

logger = get_logger(__name__)


def load_daily_ohlcv(symbol: str, start: str, end: str) -> pd.DataFrame:
    """DuckDB에서 단일 종목 OHLCV 시계열 조회."""
    con = get_connection()
    try:
        df = con.execute(
            """
            SELECT date, open, high, low, close, adj_close, volume
            FROM daily_ohlcv
            WHERE symbol = ? AND date BETWEEN ? AND ?
            ORDER BY date
            """,
            [symbol, start, end],
        ).fetchdf()
        return df.set_index("date")
    finally:
        con.close()


def load_multiple_symbols(
    symbols: list[str],
    start: str,
    end: str,
) -> dict[str, pd.DataFrame]:
    """DuckDB에서 여러 종목 OHLCV 일괄 조회."""
    results: dict[str, pd.DataFrame] = {}
    for symbol in symbols:
        df = load_daily_ohlcv(symbol, start, end)
        if df.empty:
            continue
        results[symbol] = df
    return results


def load_macro(
    indicators: list[str],
    start: str,
    end: str,
) -> pd.DataFrame:
    """DuckDB에서 매크로 지표 일괄 조회 (wide format)."""
    con = get_connection()
    try:
        placeholders = ", ".join(["?"] * len(indicators))
        df = con.execute(
            f"""
            SELECT date, indicator_code, value
            FROM macro_indicators
            WHERE indicator_code IN ({placeholders}) AND date BETWEEN ? AND ?
            ORDER BY date
            """,
            [*indicators, start, end],
        ).fetchdf()
        return df.pivot(index="date", columns="indicator_code", values="value")
    finally:
        con.close()


if __name__ == "__main__":
    from src.utils.logging_config import setup_logging

    setup_logging()

    df = load_daily_ohlcv("BTC/USDT", "2026-05-01", "2026-06-30")
    print(f"BTC/USDT: {df.shape}")
    print(df.tail())

    results = load_multiple_symbols(
        ["BTC/USDT", "ETH/USDT", "SOL/USDT"], "2026-05-01", "2026-06-30"
    )
    for sym, sub_df in results.items():
        print(f"{sym}: {sub_df.shape}")

    macro = load_macro(["DGS10", "VIXCLS"], "2020-01-01", "2026-06-30")
    print(f"매크로 wide: {macro.shape}")
    print(macro.tail())
