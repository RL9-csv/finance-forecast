"""구조화 로깅 설정.

structlog를 사용해 JSON 형식 로그 생성 → Sentry·Loki 통합 용이.
"""
import logging
import structlog

from src.utils.settings import settings


def setup_logging():
    """전역 로깅 설정 초기화.

    호출 위치: 프로그램 시작 시 1회 (main.py·api/main.py)
    """
    logging.basicConfig(
        format="%(message)s",
        level=getattr(logging, settings.log_level),
    )

    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.processors.add_log_level,
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.JSONRenderer(),
        ],
        wrapper_class=structlog.make_filtering_bound_logger(
            getattr(logging, settings.log_level)
        ),
    )


def get_logger(name: str):
    """모듈별 logger 반환.

    Usage:
        from src.utils.logging_config import get_logger
        logger = get_logger(__name__)
        logger.info("price_fetched", symbol="AAPL", price=178.32)
    """
    return structlog.get_logger(name)
