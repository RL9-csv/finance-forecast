"""DuckDB 스키마 초기화 (1회 실행).

최초 셋업 또는 새 환경에서 DuckDB 파일·테이블 생성.
Usage:
    python scripts/init_db.py
"""
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.db.connection import get_connection, init_schema
from src.utils.logging_config import setup_logging
from src.utils.settings import settings


def main() -> None:
    setup_logging()
    init_schema()

    con = get_connection()
    try:
        tables = [row[0] for row in con.execute("SHOW TABLES").fetchall()]
        print(f"DuckDB 경로: {settings.duckdb_path}")
        print(f"테이블 목록: {tables}")
    finally:
        con.close()


if __name__ == "__main__":
    main()
