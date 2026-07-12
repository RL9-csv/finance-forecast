"""M2 Group 2 — 기술 지표 (Technical Indicators).

pandas 순수 구현 (TA-Lib·pandas-ta 의존 X).
카테고리별 4함수 · 총 14 파생 컬럼:
  add_trend_indicators      (SMA·EMA·MACD)              5 col
  add_momentum_indicators   (ROC·Stochastic·RSI)        3 col
  add_volatility_indicators (Bollinger·ATR)             4 col
  add_volume_indicators     (OBV·MFI)                   2 col
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from src.utils.logging_config import get_logger

logger = get_logger(__name__)


def add_trend_indicators(df: pd.DataFrame) -> pd.DataFrame:
    """추세 지표: SMA·EMA·MACD."""
    df = df.copy()

    df["sma_20"] = df["close"].rolling(20).mean()
    df["sma_60"] = df["close"].rolling(60).mean()

    df["ema_12"] = df["close"].ewm(span=12).mean()
    df["ema_26"] = df["close"].ewm(span=26).mean()

    df["macd"] = df["ema_12"] - df["ema_26"]

    return df


def add_momentum_indicators(df: pd.DataFrame) -> pd.DataFrame:
    """모멘텀 지표: ROC·Stochastic %K·RSI."""
    df = df.copy()

    df["roc_10"] = df["close"].pct_change(10) * 100

    highest_high = df["high"].rolling(14).max()
    lowest_low = df["low"].rolling(14).min()
    df["stoch_k"] = (df["close"] - lowest_low) / (highest_high - lowest_low) * 100

    change = df["close"].diff()
    gain = change.where(change > 0, 0)
    loss = -change.where(change < 0, 0)
    avg_gain = gain.rolling(14).mean()
    avg_loss = loss.rolling(14).mean()
    df["rsi_14"] = 100 * avg_gain / (avg_gain + avg_loss)

    return df


def add_volatility_indicators(df: pd.DataFrame) -> pd.DataFrame:
    """변동성 지표: Bollinger Bands·ATR."""
    df = df.copy()

    sma_20 = df["close"].rolling(20).mean()
    std_20 = df["close"].rolling(20).std()

    df["bb_upper"] = sma_20 + 2 * std_20
    df["bb_lower"] = sma_20 - 2 * std_20
    df["bb_width"] = (df["bb_upper"] - df["bb_lower"]) / sma_20

    prev_close = df["close"].shift(1)
    true_range = pd.concat(
        [
            df["high"] - df["low"],
            (df["high"] - prev_close).abs(),
            (df["low"] - prev_close).abs(),
        ],
        axis=1,
    ).max(axis=1)
    df["atr_14"] = true_range.rolling(14).mean()

    return df


def add_volume_indicators(df: pd.DataFrame) -> pd.DataFrame:
    """거래량 지표: OBV·MFI."""
    df = df.copy()

    direction = np.sign(df["close"].diff())
    df["obv"] = (direction * df["volume"]).cumsum()

    typical_price = (df["high"] + df["low"] + df["close"]) / 3
    money_flow = typical_price * df["volume"]

    tp_diff = typical_price.diff()
    positive_flow = money_flow.where(tp_diff > 0, 0)
    negative_flow = money_flow.where(tp_diff < 0, 0)

    pos_sum_14 = positive_flow.rolling(14).sum()
    neg_sum_14 = negative_flow.rolling(14).sum()

    money_ratio = pos_sum_14 / neg_sum_14
    df["mfi_14"] = 100 - 100 / (1 + money_ratio)

    return df


if __name__ == "__main__":
    from src.db.queries import load_daily_ohlcv
    from src.features.base_features import (
        add_price_features,
        add_returns,
        add_volatility,
        add_volume_features,
    )
    from src.utils.logging_config import setup_logging

    setup_logging()

    df = load_daily_ohlcv("BTC/USDT", "2026-05-01", "2026-06-30")
    print(f"raw shape: {df.shape}")

    # Group 1
    df = add_returns(df)
    df = add_volatility(df)
    df = add_price_features(df)
    df = add_volume_features(df)

    # Group 2
    df = add_trend_indicators(df)
    df = add_momentum_indicators(df)
    df = add_volatility_indicators(df)
    df = add_volume_indicators(df)

    print(f"\nfeatured shape: {df.shape}")
    print(f"columns: {list(df.columns)}")
    print(df.tail())
