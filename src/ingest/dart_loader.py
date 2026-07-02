"""DART 데이터 수집기.

M1 데이터 파이프라인의 네 번째 모듈.
OpenDART API(금감원)에서 한국 기업 재무제표를 수집해
DuckDB(fundamentals)에 UPSERT 저장.

M9에서 본격 활용 (Fama-French 5요인·Quality factor input).
"""

from __future__ import annotations

import pandas as pd
import OpenDartReader

from src.db.connection import get_connection
from src.utils.decorators import retry
from src.utils.logging_config import get_logger
from src.utils.settings import settings

logger = get_logger(__name__)

# 모듈 레벨 OpenDartReader (singleton)
_dart = OpenDartReader(api_key=settings.dart_api_key)


@retry(max_retries=3)
def fetch_financials(corp_code: str, year: int) -> pd.DataFrame:
    """단일 회사·단일 연도 재무제표 조회 (DART)."""
    return _dart.finstate(corp_code, year)


def fetch_multiple_financials(
    corp_codes: list[str],
    **kwargs,
) -> dict[str, pd.DataFrame]:
    """여러 회사 재무제표 일괄 수집. 실패·빈 결과는 dict에서 빠짐."""
    results: dict[str, pd.DataFrame] = {}
    for corp_code in corp_codes:
        df = fetch_financials(corp_code, **kwargs)
        if df is None:
            continue
        if df.empty:
            continue
        results[corp_code] = df
    return results


def save_financials_to_duckdb(corp_code: str, df: pd.DataFrame) -> int:
    """재무제표 DataFrame을 fundamentals 테이블에 UPSERT."""
    if df is None:
        return 0
    if df.empty:
        return 0

    df["corp_code"] = corp_code
    df["report_date"] = pd.to_datetime(df["report_date"]).dt.strftime("%Y-%m-%d")

    cols = ["corp_code", "report_date", "account_id", "account_nm", "thstrm_amount"]
    df = df[cols]

    con = get_connection()
    try:
        con.register("_tmp_fundamentals", df)
        con.execute("""
            INSERT OR REPLACE INTO fundamentals
                (corp_code, report_date, account_id, account_nm, thstrm_amount)
            SELECT corp_code, report_date, account_id, account_nm, thstrm_amount
            FROM _tmp_fundamentals
        """)
        logger.info("fundamentals_saved", corp_code=corp_code, rows=len(df))
    finally:
        con.unregister("_tmp_fundamentals")
        con.close()

    return len(df)


if __name__ == "__main__":
    from src.utils.logging_config import setup_logging

    setup_logging()

    # 단일 시연 (삼성전자)
    df = fetch_financials("005930", 2025)
    print(f"삼성전자 2025 shape: {df.shape}")
    print(df.head())

    # 다중 + 저장 (삼성·SK하이닉스·NAVER)
    corp_codes = ["005930", "000660", "035420"]
    results = fetch_multiple_financials(corp_codes, year=2025)
    for corp_code, df in results.items():
        rows = save_financials_to_duckdb(corp_code, df)
        print(f"{corp_code}: {rows}행 저장")
