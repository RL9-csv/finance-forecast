"""FRED 데이터 수집기.

M1 데이터 파이프라인의 세 번째 모듈.
FRED API(미국 연준)에서 매크로 경제 지표(금리·VIX·환율·실업률·CPI)를 수집해
DuckDB(macro_indicators)에 UPSERT 저장.
"""

from __future__ import annotations

import pandas as pd
from fredapi import Fred

from src.db.connection import get_connection
from src.utils.decorators import retry
from src.utils.logging_config import get_logger
from src.utils.settings import settings

logger = get_logger(__name__)

# 모듈 레벨 FRED 클라이언트 (singleton) — 모든 함수가 재사용
_fred = Fred(api_key=settings.fred_api_key)


@retry(max_retries=3)
def fetch_series_indicator(
    code: str,
    start: str | None = None,
    end: str | None = None,
) -> pd.Series:
    """단일 매크로 지표 시계열 조회 (FRED)."""
    return _fred.get_series(code, observation_start=start, observation_end=end)


def fetch_multiple_indicators(codes: list[str], **kwargs) -> dict[str, pd.Series]:
    """여러 매크로 지표 일괄 수집. 실패·빈 결과는 dict에서 빠짐."""
    results: dict[str, pd.Series] = {}
    for code in codes:
        series = fetch_series_indicator(code, **kwargs)
        if series is None:
            continue
        if series.empty:
            continue
        results[code] = series
    return results


def save_macro_to_duckdb(code: str, series: pd.Series) -> int:
    """매크로 시계열을 macro_indicators 테이블에 UPSERT.

    Args:
        code: 지표 코드 (예: "DGS10")
        series: fetch_series_indicator 반환 Series

    Returns:
        저장 행 수 (series가 비었으면 0).
    """
    if series is None:
        return 0
    if series.empty:
        return 0

    df = series.reset_index()
    df.columns = ["date", "value"]
    df["indicator_code"] = code
    df["date"] = pd.to_datetime(df["date"]).dt.strftime("%Y-%m-%d")

    cols = ["indicator_code", "date", "value"]
    df = df[cols]

    con = get_connection()
    try:
        con.register("_tmp_macro", df)
        con.execute("""
            INSERT OR REPLACE INTO macro_indicators
                (indicator_code, date, value)
            SELECT indicator_code, date, value
            FROM _tmp_macro
        """)
        logger.info("macro_saved", code=code, rows=len(df))
    finally:
        con.unregister("_tmp_macro")
        con.close()

    return len(df)


if __name__ == "__main__":
    from src.utils.logging_config import setup_logging

    setup_logging()

    series = fetch_series_indicator("DGS10", start="2020-01-01", end=None)
    print(f"DGS10 latest: {series.iloc[-1]}")

    codes = ["DGS10", "DGS2", "VIXCLS", "DEXKOUS", "UNRATE", "CPIAUCSL"]
    results = fetch_multiple_indicators(codes, start="2020-01-01")
    for code, series in results.items():
        rows = save_macro_to_duckdb(code, series)
        print(f"{code}: {rows}행 저장")
