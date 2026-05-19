"""yfinance 데이터 수집기.

M1 데이터 파이프라인의 첫 모듈.
주식·ETF의 OHLCV 데이터를 yfinance로 수집하고 DuckDB(daily_ohlcv)에 UPSERT 저장.
"""
from __future__ import annotations

import pandas as pd
import yfinance as yf

from src.db.connection import get_connection
from src.utils.decorators import retry
from src.utils.logging_config import get_logger

logger = get_logger(__name__)

OHLCV_COLUMNS = ("open", "high", "low", "close", "adj_close", "volume")


@retry(max_retries=3)
def fetch_realtime_price(symbol: str) -> float | None:
    """실시간 가격 조회. retry 3회 후 실패 시 None."""
    ticker = yf.Ticker(symbol)
    info = ticker.info
    for key in ("regularMarketPrice", "currentPrice", "previousClose"):
        if key in info and info[key] is not None:
            return float(info[key])
    return None


@retry(max_retries=3)
def fetch_ohlcv(
    symbol: str,
    start: str | None = None,
    end: str | None = None,
    period: str = "1y",
    interval: str = "1d",
) -> pd.DataFrame:
    """OHLCV 시계열 조회.

    Args:
        symbol: 종목 코드 (예: "AAPL", "005930.KS")
        start·end: YYYY-MM-DD. 우선순위는 (start,end) > period.
        period: "1d"·"5d"·"1mo"·"1y"·"max" 등.
        interval: "1m"·"5m"·"1h"·"1d"·"1wk" 등.

    Returns:
        컬럼: open, high, low, close, adj_close, volume (DatetimeIndex, index.name="date").
        auto_adjust=False로 둬 Adj Close 컬럼 보존.
    """
    ticker = yf.Ticker(symbol)
    if start and end:
        df = ticker.history(start=start, end=end, interval=interval, auto_adjust=False)
    else:
        df = ticker.history(period=period, interval=interval, auto_adjust=False)

    df.columns = [c.lower().replace(" ", "_") for c in df.columns]
    df.index.name = "date"

    keep = [c for c in OHLCV_COLUMNS if c in df.columns]
    return df[keep]


def fetch_multiple_symbols(symbols: list[str], **kwargs) -> dict[str, pd.DataFrame]:
    """여러 종목 일괄 수집. 실패·빈 결과는 dict에서 빠짐(배치 끊김 방지)."""
    results: dict[str, pd.DataFrame] = {}
    for symbol in symbols:
        df = fetch_ohlcv(symbol, **kwargs)
        if df is None:
            logger.warning("ohlcv_fetch_failed", symbol=symbol)
            continue
        if df.empty:
            logger.warning("ohlcv_empty", symbol=symbol)
            continue
        results[symbol] = df
        logger.info("ohlcv_fetched", symbol=symbol, rows=len(df))
    return results


def save_to_duckdb(symbol: str, df: pd.DataFrame) -> int:
    """OHLCV DataFrame을 daily_ohlcv 테이블에 UPSERT.

    Args:
        symbol: 종목 코드
        df: fetch_ohlcv 반환 DataFrame

    Returns:
        저장 행 수 (df가 비었으면 0).
    """
    if df is None or df.empty:
        return 0

    df_to_save = df.reset_index().copy()
    df_to_save["symbol"] = symbol
    # adj_close 누락 시 close로 대체
    if "adj_close" not in df_to_save.columns:
        df_to_save["adj_close"] = df_to_save["close"]

    cols = ["symbol", "date", "open", "high", "low", "close", "adj_close", "volume"]
    df_to_save = df_to_save[cols]

    con = get_connection()
    try:
        con.register("_tmp_ohlcv", df_to_save)
        con.execute("""
            INSERT INTO daily_ohlcv (symbol, date, open, high, low, close, adj_close, volume)
            SELECT symbol, date, open, high, low, close, adj_close, volume
            FROM _tmp_ohlcv
            ON CONFLICT (symbol, date) DO UPDATE SET
                open = EXCLUDED.open,
                high = EXCLUDED.high,
                low = EXCLUDED.low,
                close = EXCLUDED.close,
                adj_close = EXCLUDED.adj_close,
                volume = EXCLUDED.volume
        """)
        logger.info("ohlcv_saved", symbol=symbol, rows=len(df_to_save))
    finally:
        con.unregister("_tmp_ohlcv")
        con.close()

    return len(df_to_save)


if __name__ == "__main__":
    from src.utils.logging_config import setup_logging

    setup_logging()
    price = fetch_realtime_price("AAPL")
    print(f"AAPL 현재가: ${price:.2f}" if price else "조회 실패")

    df = fetch_ohlcv("AAPL", period="1mo")
    print(f"\n최근 1개월 shape: {df.shape}")
    print(df.tail())

    rows = save_to_duckdb("AAPL", df)
    print(f"\nDuckDB 저장: {rows}행")
