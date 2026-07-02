"""M2 Group 1 — 기본 가격·거래량 변환.

Raw OHLCV → 파생 12 피처:
  - Returns (4): 1d·5d·20d pct + log return
  - Volatility (2): 20d rolling std·60d HV (연율화)
  - Price (3): gap·close_position·intraday_range
  - Volume (3): dollar_volume·log_volume·volume_change

각 함수는 df.copy() → 새 컬럼 추가 → 반환 (원본 훼손 X).
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from src.utils.logging_config import get_logger

logger = get_logger(__name__)


def add_returns(df: pd.DataFrame) -> pd.DataFrame:
    """close 기반 수익률 4개 컬럼 추가."""
    df = df.copy()

    df["ret_1d"] = df["close"].pct_change(1)
    df["ret_5d"] = df["close"].pct_change(5)
    df["ret_20d"] = df["close"].pct_change(20)
    df["log_ret_1d"] = np.log(df["close"] / df["close"].shift(1))

    return df


def add_volatility(df: pd.DataFrame) -> pd.DataFrame:
    """log_ret_1d 기반 rolling 변동성 (연율화)."""
    df = df.copy()

    df["vol_20d"] = df["log_ret_1d"].rolling(20).std() * np.sqrt(252)
    df["hv_60d"] = df["log_ret_1d"].rolling(60).std() * np.sqrt(252)

    return df


def add_price_features(df: pd.DataFrame) -> pd.DataFrame:
    """OHLC 관계 파생 — intraday 정보 복원."""
    df = df.copy()

    df["gap"] = df["open"] - df["close"].shift(1)
    df["close_position"] = (df["close"] - df["low"]) / (df["high"] - df["low"])
    df["intraday_range"] = df["high"] - df["low"]

    return df


def add_volume_features(df: pd.DataFrame) -> pd.DataFrame:
    """거래량 파생."""
    df = df.copy()

    df["dollar_volume"] = df["close"] * df["volume"]
    df["log_volume"] = np.log(df["volume"])
    df["volume_change"] = df["volume"].pct_change(1)

    return df


if __name__ == "__main__":
    from src.db.queries import load_daily_ohlcv
    from src.utils.logging_config import setup_logging

    setup_logging()

    df = load_daily_ohlcv("BTC/USDT", "2026-05-01", "2026-06-30")
    print(f"raw shape: {df.shape}")
    print(f"raw columns: {list(df.columns)}")

    df = add_returns(df)
    df = add_volatility(df)
    df = add_price_features(df)
    df = add_volume_features(df)

    print(f"\nfeatured shape: {df.shape}")
    print(f"featured columns: {list(df.columns)}")
    print(df.tail())
