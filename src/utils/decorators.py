"""공통 decorator 모음.

학습 단계별로 점진적 강화:
    Level A — retry: 기본 재시도 (현재)
    Level B — + time.sleep
    Level C — + exponential backoff
    Level D — + raise 최종 실패
    Level E — + logging 통합
    Level F — + @functools.wraps

지금 단계: Level A (학습용 단순 버전)
"""
import time


def retry(max_retries: int = 3):
    """간단한 재시도 decorator factory.

    Args:
        max_retries: 최대 재시도 횟수 (기본 3)

    Usage:
        @retry(max_retries=3)
        def fetch_price(symbol):
            ...

    Returns:
        성공 시 함수 결과, 모든 시도 실패 시 None
    """
    def decorator(func):
        def wrapper(*args, **kwargs):
            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    print(f"실패 {attempt + 1}/{max_retries}: {e}")
            return None
        return wrapper
    return decorator


# Level B 이상은 학습 진행하면서 추가
# def retry_with_backoff(max_retries=3, backoff=2): ...
