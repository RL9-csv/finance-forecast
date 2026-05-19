"""ingest 모듈 단위 테스트.

pytest로 실행:
    pytest tests/test_ingest.py -v
"""
import pytest
from src.ingest.yfinance_loader import fetch_realtime_price, fetch_ohlcv


def test_fetch_realtime_price_apple():
    """AAPL 실시간 가격 조회 — 양수 float 반환"""
    price = fetch_realtime_price("AAPL")
    assert price is not None
    assert isinstance(price, float)
    assert price > 0


def test_fetch_realtime_price_invalid_symbol():
    """잘못된 종목 — None 반환 (에러 X)"""
    price = fetch_realtime_price("INVALID_SYMBOL_XYZ_999")
    # retry 3번 후 None 반환 (raise 안 함)
    assert price is None


def test_fetch_ohlcv_shape():
    """1개월 OHLCV 데이터 shape 검증"""
    df = fetch_ohlcv("AAPL", period="1mo")
    assert df is not None
    assert len(df) > 15  # 영업일 ~20일
    assert len(df) < 25
    assert "close" in df.columns
    assert "volume" in df.columns


def test_fetch_ohlcv_columns():
    """필수 컬럼 존재 확인"""
    df = fetch_ohlcv("AAPL", period="5d")
    required = {"open", "high", "low", "close", "volume"}
    assert required.issubset(set(df.columns))


def test_fetch_ohlcv_data_integrity():
    """OHLC 정합성 — high >= low, high >= open, close 등"""
    df = fetch_ohlcv("AAPL", period="5d")
    assert (df["high"] >= df["low"]).all()
    assert (df["high"] >= df["open"]).all()
    assert (df["high"] >= df["close"]).all()
    assert (df["volume"] > 0).all()
