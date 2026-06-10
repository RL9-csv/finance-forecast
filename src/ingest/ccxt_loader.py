"""ccxt 데이터 수집기.

M1 데이터 파이프라인의 두 번째 모듈.
가상화폐 OHLCV 데이터를 ccxt(공개 거래소 API)로 수집하고 DuckDB(daily_ohlcv)에 UPSERT 저장.
"""

from __future__ import annotations

import pandas as pd
import ccxt

from src.db.connection import get_connection
from src.utils.decorators import retry
from src.utils.logging_config import get_logger

logger = get_logger(__name__)

OHLCV_COLUMNS = ("open", "high", "low", "close", "adj_close", "volume")

# 모듈 레벨 거래소 객체 (singleton) — 모든 함수가 재사용
_exchange = ccxt.binance()


@retry(max_retries=3)
def fetch_realtime_price(symbol: str) -> float | None:
    """실시간 가격 조회. retry 3회 후 실패 시 None."""
    ticker = _exchange.fetch_ticker(symbol)
    if ticker.get("last") is not None:
        return float(ticker["last"])
    return None


@retry(max_retries=3)
def fetch_ohlcv(symbol: str, timeframe: str = "1d", limit: int = 30) -> pd.DataFrame:
    """OHLCV 시계열 조회 (ccxt).

    Args:
        symbol: 거래 페어 (예: "BTC/USDT").
        timeframe: 캔들 단위 ("1m"·"1h"·"1d"·"1w" 등).
        limit: 캔들 개수 (최근 N개).

    Returns:
        컬럼: open, high, low, close, volume (date 인덱스).
        ccxt는 adj_close 없음 → save_to_duckdb에서 close로 채움.
    """
    ohlcv = _exchange.fetch_ohlcv(symbol, timeframe, limit=limit)
    df = pd.DataFrame(ohlcv, columns=["ts_ms", "open", "high", "low", "close", "volume"])
    df["date"] = pd.to_datetime(df["ts_ms"], unit="ms").dt.strftime("%Y-%m-%d")
    df = df.drop(columns=["ts_ms"]).set_index("date")
    return df


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

    # yfinance가 timezone-aware Timestamp를 반환 → DuckDB DATE 컬럼과 충돌하므로
    # ISO 문자열(YYYY-MM-DD)로 정규화. tz-aware든 naive든 일관된 결과 보장.
    df_to_save["date"] = pd.to_datetime(df_to_save["date"]).dt.strftime("%Y-%m-%d")

    cols = ["symbol", "date", "open", "high", "low", "close", "adj_close", "volume"]
    df_to_save = df_to_save[cols]

    con = get_connection()
    try:
        con.register("_tmp_ohlcv", df_to_save)
        con.execute("""
            INSERT OR REPLACE INTO daily_ohlcv
                (symbol, date, open, high, low, close, adj_close, volume)
            SELECT symbol, date, open, high, low, close, adj_close, volume
            FROM _tmp_ohlcv
        """)
        logger.info("ohlcv_saved", symbol=symbol, rows=len(df_to_save))
    finally:
        con.unregister("_tmp_ohlcv")
        con.close()

    return len(df_to_save)


if __name__ == "__main__":
    from src.utils.logging_config import setup_logging

    setup_logging()

    price = fetch_realtime_price("BTC/USDT")
    print(f"BTC/USDT 현재가: ${price:,.2f}" if price else "조회 실패")

    df = fetch_ohlcv("BTC/USDT", timeframe="1d", limit=30)
    print(f"\n최근 30일 shape: {df.shape}")
    print(df.tail())

    symbols = ["BTC/USDT", "ETH/USDT", "SOL/USDT"]
    results = fetch_multiple_symbols(symbols, timeframe="1d", limit=30)
    for symbol, df in results.items():
        rows = save_to_duckdb(symbol, df)
        print(f"{symbol}: {rows}행 저장")
