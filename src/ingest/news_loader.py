"""뉴스 데이터 수집기 (M1 스켈레톤).

M1에서는 스켈레톤만 정의. 본격 구현은 M7(LLM 통합)에서:
  - NewsAPI / RSS 피드 / Reddit·X
  - FinBERT로 감성 점수 → 추천 Context Feature 입력 (M9 흡수)
  - news_articles 테이블 적재
"""

from __future__ import annotations

import pandas as pd

from src.db.connection import get_connection
from src.utils.decorators import retry
from src.utils.logging_config import get_logger

logger = get_logger(__name__)


@retry(max_retries=3)
def fetch_news_for_symbol(
    symbol: str,
    start: str | None = None,
    end: str | None = None,
) -> list[dict]:
    """종목별 뉴스 수집 (M7 활성).

    Returns:
        list[dict]: 각 dict는 {title, content, url, published_at, source, symbols}
    """
    raise NotImplementedError("M7 LLM 통합 단계에서 구현 — NewsAPI·RSS·FinBERT 결합")


def fetch_multiple_symbols_news(
    symbols: list[str],
    **kwargs,
) -> dict[str, list[dict]]:
    """여러 종목 뉴스 일괄 수집 (M7 활성)."""
    raise NotImplementedError("M7에서 구현 — 단일/배치 추상화 패턴")


def save_news_to_duckdb(articles: list[dict]) -> int:
    """뉴스 → news_articles 테이블 UPSERT (M7 활성).

    스키마: id·source·title·content·url·published_at·symbols·sentiment_score
    """
    raise NotImplementedError("M7에서 구현 — FinBERT sentiment_score 포함")


if __name__ == "__main__":
    print("news_loader.py — M1 스켈레톤. M7 LLM 통합 단계에서 본격 구현 예정.")
