"""DuckDB 연결·스키마 관리.

M1 데이터 수집 결과를 저장하는 로컬 분석 DB(data/finance.duckdb).
스키마 정의는 `src/ingest/CLAUDE.md`의 표준을 따른다.
"""
from pathlib import Path

import duckdb

from src.utils.logging_config import get_logger
from src.utils.settings import settings

logger = get_logger(__name__)


# 테이블 DDL — IF NOT EXISTS로 멱등(idempotent).
DDL = """
CREATE TABLE IF NOT EXISTS securities (
    symbol VARCHAR PRIMARY KEY,
    name VARCHAR,
    market VARCHAR,
    sector VARCHAR,
    industry VARCHAR,
    currency VARCHAR
);

CREATE TABLE IF NOT EXISTS daily_ohlcv (
    symbol VARCHAR,
    date DATE,
    open DOUBLE,
    high DOUBLE,
    low DOUBLE,
    close DOUBLE,
    adj_close DOUBLE,
    volume BIGINT,
    PRIMARY KEY (symbol, date)
);

CREATE TABLE IF NOT EXISTS macro_indicators (
    indicator_code VARCHAR,
    date DATE,
    value DOUBLE,
    PRIMARY KEY (indicator_code, date)
);
"""


def get_connection(path: str | None = None) -> duckdb.DuckDBPyConnection:
    """DuckDB 커넥션 반환.

    Args:
        path: DB 파일 경로. None이면 settings.duckdb_path 사용.

    Returns:
        read_write 모드 커넥션.
    """
    db_path = Path(path or settings.duckdb_path)
    db_path.parent.mkdir(parents=True, exist_ok=True)
    return duckdb.connect(str(db_path))


def init_schema(con: duckdb.DuckDBPyConnection | None = None) -> None:
    """필수 테이블 생성 (없을 때만).

    Args:
        con: 기존 커넥션. None이면 새로 열고 종료 시 닫는다.
    """
    own_conn = con is None
    if own_conn:
        con = get_connection()
    try:
        con.execute(DDL)
        logger.info("schema_initialized", duckdb_path=settings.duckdb_path)
    finally:
        if own_conn:
            con.close()


if __name__ == "__main__":
    from src.utils.logging_config import setup_logging

    setup_logging()
    init_schema()
    con = get_connection()
    try:
        tables = con.execute("SHOW TABLES").fetchall()
        print(f"테이블 목록: {[t[0] for t in tables]}")
    finally:
        con.close()
