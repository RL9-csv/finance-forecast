"""일별 데이터 수집 entry point.

매일 1회 실행 (GitHub Actions cron 또는 수동).
config/symbols.yaml의 카테고리 → yfinance → DuckDB(daily_ohlcv) UPSERT.

Usage:
    python scripts/ingest_daily.py
    python scripts/ingest_daily.py --category us_tech --period 5d
    python scripts/ingest_daily.py --symbols AAPL,MSFT
"""
from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

import yaml

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.db.connection import init_schema
from src.ingest.yfinance_loader import fetch_ohlcv, save_to_duckdb
from src.utils.logging_config import get_logger, setup_logging

logger = get_logger(__name__)

SYMBOLS_YAML = PROJECT_ROOT / "config" / "symbols.yaml"


def load_symbols(category: str | None = None) -> list[str]:
    """symbols.yaml에서 카테고리 종목 로딩.

    Args:
        category: 카테고리 키. None이면 us_tech + etf 통합 반환.
    """
    with SYMBOLS_YAML.open(encoding="utf-8") as f:
        catalog = yaml.safe_load(f)

    if category:
        if category not in catalog:
            raise ValueError(f"카테고리 없음: {category} (가능: {list(catalog)})")
        return list(catalog[category])

    return list(catalog.get("us_tech", [])) + list(catalog.get("etf", []))


def main() -> None:
    parser = argparse.ArgumentParser(description="일별 시장 데이터 수집")
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--symbols", type=str, help="콤마 구분 종목 (yaml 무시)")
    group.add_argument("--category", type=str, help="symbols.yaml 카테고리명")
    parser.add_argument(
        "--period",
        type=str,
        default="1mo",
        help="수집 기간 (1d·5d·1mo·1y·max, 기본 1mo)",
    )
    parser.add_argument(
        "--rate-limit-sec",
        type=float,
        default=1.0,
        help="종목 간 대기 (yfinance 1초 1회 권장)",
    )
    args = parser.parse_args()

    setup_logging()
    init_schema()

    if args.symbols:
        symbols = [s.strip() for s in args.symbols.split(",")]
    else:
        symbols = load_symbols(args.category)

    logger.info("ingest_start", symbol_count=len(symbols), period=args.period)

    success = 0
    failed: list[str] = []
    total_rows = 0
    started = time.time()

    for i, symbol in enumerate(symbols):
        df = fetch_ohlcv(symbol, period=args.period)
        if df is None or df.empty:
            failed.append(symbol)
            logger.warning("symbol_failed", symbol=symbol)
            continue
        rows = save_to_duckdb(symbol, df)
        total_rows += rows
        success += 1

        if i < len(symbols) - 1:
            time.sleep(args.rate_limit_sec)

    elapsed = round(time.time() - started, 2)
    logger.info(
        "ingest_complete",
        success=success,
        failed_count=len(failed),
        failed=failed,
        total_rows=total_rows,
        elapsed_sec=elapsed,
    )
    print(
        f"\n수집 완료: 성공 {success}/{len(symbols)} | 행 {total_rows} | {elapsed}s",
    )
    if failed:
        print(f"실패 종목: {failed}")

    if failed and success == 0:
        sys.exit(1)


if __name__ == "__main__":
    main()
