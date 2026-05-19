# src/ingest/ — 데이터 수집 폴더 Context

## 담당 agent

이 폴더 작업은 **data-ingest agent**가 전담합니다 (M1 마일스톤).

## 폴더 목적

금융 데이터를 외부 API에서 자동 수집해서 DuckDB에 저장.

## 5개 모듈 (M1 완료 시점 목표)

| 파일 | 담당 | API |
|---|---|---|
| `yfinance_loader.py` | 주식·ETF | yfinance |
| `ccxt_loader.py` | 가상화폐 | ccxt (Binance·Upbit 등) |
| `fred_loader.py` | 매크로 (금리·VIX·환율) | FRED |
| `news_loader.py` | 뉴스 (M7 활성, M1엔 스켈레톤만) | NewsAPI·RSS |
| `dart_loader.py` | 한국 재무 (M9 활성, M1엔 스켈레톤만) | OpenDART |

## 공통 규칙

### 모든 함수에 retry 적용

```python
from src.utils.decorators import retry

@retry(max_retries=3)
def fetch_xxx(symbol: str) -> pd.DataFrame:
    ...
```

### 환경 변수는 settings 통해

```python
from src.utils.settings import settings
api_key = settings.fred_api_key
```

### Logging은 structlog

```python
from src.utils.logging_config import get_logger
logger = get_logger(__name__)
logger.info("ohlcv_fetched", symbol=symbol, rows=len(df))
```

### Rate Limit 회피

각 API별 제한:
- yfinance: 1초 1회 권장
- ccxt: 거래소별 (binance 1200/min)
- FRED: 120/min
- NewsAPI: 100/day (free tier)

→ `time.sleep` + 배치 분할 + ThreadPoolExecutor 병렬 (rate limit 준수 하에)

## 출력 표준

### 모든 fetch 함수의 반환 타입

| 함수 종류 | 반환 |
|---|---|
| 단일 가격 조회 | `float \| None` |
| OHLCV 시계열 | `pd.DataFrame` (DatetimeIndex, columns: open·high·low·close·volume) |
| 다중 종목 | `dict[str, pd.DataFrame]` |
| 매크로 지표 | `pd.Series` (DatetimeIndex) |
| 뉴스 | `list[dict]` (each: title·content·published_at·url·symbols) |

→ 다른 agent (feature-engineer)가 받아쓸 표준.

## 저장 대상

`data/finance.duckdb`에 다음 테이블:

```sql
-- 종목 마스터
CREATE TABLE securities (
    symbol VARCHAR PRIMARY KEY,
    name VARCHAR,
    market VARCHAR,
    sector VARCHAR,
    industry VARCHAR,
    currency VARCHAR
);

-- 일봉 OHLCV
CREATE TABLE daily_ohlcv (
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

-- 매크로 지표
CREATE TABLE macro_indicators (
    indicator_code VARCHAR,
    date DATE,
    value DOUBLE,
    PRIMARY KEY (indicator_code, date)
);

-- 뉴스 (M7)
CREATE TABLE news_articles (
    id BIGINT PRIMARY KEY,
    source VARCHAR,
    title TEXT,
    content TEXT,
    url TEXT UNIQUE,
    published_at TIMESTAMP,
    symbols TEXT[],
    sentiment_score DOUBLE
);
```

## 다음 마일스톤 (M2 — feature-engineer agent) 인터페이스

M2 agent는 이 폴더의 결과만 사용. M1 agent가 다음 함수를 안정적으로 제공해야 함:

```python
def load_daily_ohlcv(symbol: str, start: str, end: str) -> pd.DataFrame:
    """DuckDB에서 OHLCV 조회"""
    ...

def load_multiple_symbols(symbols: list[str], start: str, end: str) -> dict[str, pd.DataFrame]:
    """여러 종목 일괄 조회"""
    ...

def load_macro(indicators: list[str], start: str, end: str) -> pd.DataFrame:
    """매크로 지표 조회"""
    ...
```

## 금지

- ingest 외 폴더 코드 수정 (feature·model·api 등)
- 동기 1개씩 순차 처리 (느림 — 병렬화 필수)
- 결측 자동 보간 (silent failure 위험)
- 시계열 정렬 안 한 데이터 저장
- API 응답 검증 없이 저장
