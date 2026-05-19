# 자주 쓰는 명령 한 번에.
# Usage: make <target>

.PHONY: help install test lint format clean ingest

help:
	@echo "사용 가능한 명령:"
	@echo "  make install   - 패키지 설치"
	@echo "  make test      - 테스트 실행"
	@echo "  make lint      - 코드 린트 검사 (ruff)"
	@echo "  make format    - 코드 포맷팅 (black + ruff)"
	@echo "  make clean     - 캐시 정리"
	@echo "  make ingest    - 데이터 수집 1회 실행"

install:
	pip install --upgrade pip
	pip install -r requirements.txt

test:
	pytest tests/ -v --cov=src

lint:
	ruff check src/ tests/

format:
	black src/ tests/ scripts/
	ruff check --fix src/ tests/

clean:
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type d -name .pytest_cache -exec rm -rf {} +
	find . -type d -name .ruff_cache -exec rm -rf {} +
	find . -type d -name .mypy_cache -exec rm -rf {} +

ingest:
	python scripts/ingest_daily.py
