# Finance Forecast System

> 금융 시계열 데이터를 시계열 딥러닝·LLM·추천 시스템으로 통합 분석하는 end-to-end 시스템

## 프로젝트 정체성

- **목적**: 고도화된 특성 공학과 시계열 딥러닝을 실사용 수준으로 통합한 end-to-end 금융 ML 시스템
- **3분야 통합**: 시계열 딥러닝 + LLM + 추천 시스템
- **end-to-end**: 데이터 수집 → 피처 → 모델 → 백테스팅 → 배포 → 모니터링

## 시스템 아키텍처

```
[데이터 소스] → [파이프라인] → [피처 엔지니어링] → [모델링]
    ↓             ↓              ↓                 ↓
yfinance      Prefect       기술지표·분수차분    Transformer·TFT
ccxt          DuckDB        FinBERT 감성         Chronos·Moirai
FRED          PostgreSQL    PCA·UMAP·HMM        HMM Regime
News                                              ↓
                                              [LLM 통합]
                                                  ↓
                                              [추천 시스템]
                                                  ↓
                                              [백테스팅]
                                                  ↓
                                              [페이퍼 트레이딩]
                                                  ↓
                                              [배포·서빙]
                                                  ↓
                                              [모니터링]
```

## 계산 환경

- **GPU**: RTX 5060 8GB VRAM (로컬 학습·추론)
- **클라우드 임대**: RunPod A100 ($1.19/시간, 7B+ fine-tuning 시만)
- **월 운영 비용**: $20~$60

## 기술 스택

| 영역 | 도구 |
|---|---|
| 언어 | Python 3.11+ |
| 데이터 | Pandas·Polars·DuckDB·PostgreSQL |
| 시계열 모델 | PyTorch·HuggingFace·Darts·Nixtla |
| LLM | OpenAI API·LangChain·LangGraph·Ollama·Groq |
| 백테스팅 | vectorbt·Backtrader·자체 구현 |
| 배포 | FastAPI·Docker·Fly.io |
| 프론트엔드 | Dash + Mantine·Plotly 3D·Gradio |
| 모니터링 | Sentry·Prometheus·Grafana·Evidently AI |

## 12개월 마일스톤

- M1: 데이터 파이프라인 v1 (GitHub Actions cron + DuckDB)
- M2: 피처 엔지니어링 v1 (TA-Lib·분수 차분)
- M3: Baseline 모델 + Sharpe 평가
- M4: Advanced 모델 (Transformer·TFT)
- M5: TLM 도입 (Chronos·Moirai)
- M6: 백테스팅 엔진 (Walk-Forward·Purged K-Fold)
- M7: LLM 통합 (FinBERT·GPT RAG)
- M8: Multi-Agent (LangGraph)
- M9: 추천 시스템 + Regime 분석 (PCA·UMAP·HMM)
- M10: 배포 + 3D 시각화 대시보드 (Dash + Mantine)
- M11: 모니터링·프로덕션

## Quick Start

```bash
# 가상환경 생성
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# 패키지 설치
pip install -r requirements.txt

# 환경 변수 설정
cp .env.example .env
# .env 파일 열고 API 키 입력

# 데이터 수집 (M1 단계)
python scripts/ingest_daily.py
```

## 폴더 구조

```
finance-forecast/
├── src/                # 메인 소스 코드
│   ├── ingest/         # 데이터 수집
│   ├── features/       # 피처 엔지니어링
│   ├── models/         # 모델링 (baseline·advanced·tlm·regime)
│   ├── llm/            # LLM 통합 (RAG·Agent·sentiment)
│   ├── recommendation/ # 추천 시스템
│   ├── backtesting/    # 백테스팅·리스크
│   ├── api/            # FastAPI 서빙
│   ├── dashboard/      # Dash 대시보드
│   ├── db/             # DB 연결·ORM
│   ├── utils/          # 공통 유틸 (decorators 등)
│   └── monitoring/     # 모니터링
├── tests/              # 단위·통합 테스트
├── notebooks/          # Jupyter 실험·EDA
├── scripts/            # 실행 스크립트
├── config/             # YAML 설정
├── data/               # 데이터 (Git ignore)
├── models_artifacts/   # 학습된 모델 (DVC 또는 W&B)
├── deployment/         # Dockerfile·docker-compose
└── docs/               # 문서·아키텍처·runbook
```

## Disclaimer

본 시스템은 정보 제공 목적이며, 투자 자문이 아닙니다. 페이퍼 트레이딩만 수행하며 실제 거래 자동화는 자본시장법 회피를 위해 구현하지 않습니다.

## License

MIT
