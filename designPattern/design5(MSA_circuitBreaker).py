import time
import requests

def notify_applications(message: str):
    """
    (예시) 다른 어플리케이션에 알림을 전송하는 함수.
    실제로는 Slack, Email, 메시지 큐, 모니터링 대시보드 등에 연동 가능.
    """
    print(f"[Notify] 모든 관련 서비스에 알림: {message}")

class CircuitBreaker:
    """
    간단한 서킷브레이커 클래스 예시

    Attributes:
        failure_threshold (int): 연속 실패 허용 횟수
        recovery_timeout (int): OPEN 상태에서 HALF_OPEN으로 전환하기 위한 최소 시간(초)
        expected_exception (Exception): 실패로 간주할 예외 타입
    """
    def __init__(
        self, 
        failure_threshold: int = 3, 
        recovery_timeout: int = 10, 
        expected_exception: Exception = Exception
    ):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.expected_exception = expected_exception

        self._failure_count = 0
        self._state = 'CLOSED'       # 'CLOSED', 'OPEN', 'HALF_OPEN'
        self._last_failure_time = None

    def _open_circuit(self):
        """Circuit OPEN"""
        self._state = 'OPEN'
        self._last_failure_time = time.time()
        print("회로 OPEN")

    def _close_circuit(self):
        """Circuit CLOSED"""
        self._failure_count = 0
        self._state = 'CLOSED'
        self._last_failure_time = None
        print("회로 CLOSED")

    def _half_open_circuit(self):
        """Circuit HALF_OPEN"""
        self._state = 'HALF_OPEN'
        print("회로 HALF_OPEN")

    def call(self, func, *args, **kwargs):
        """
        외부 함수를 서킷브레이커로 호출.
        
            response = circuit_breaker.call(requests.get, "http://example.com")
        
        """
        # 1) if OPEN: recovery_timeout check
        if self._state == 'OPEN':
            time_since_failure = time.time() - self._last_failure_time
            if time_since_failure > self.recovery_timeout:
                # 일정 시간이 지나면 HALF_OPEN으로 전환 후 시도
                self._half_open_circuit()
            else:
                # if self.recovery_timeout <= time_since_failure: 요청 차단
                raise RuntimeError("Circuit OPEN. Request block.")

        # 2) 함수 실제 호출 시도
        try:
            response = func(*args, **kwargs)
        except self.expected_exception as exc:
            # 실패한 경우 카운트 증가
            self._failure_count += 1
            print(f"함수 호출 실패. 현재 실패 횟수: {self._failure_count}")

            # 실패 횟수가 임계값 도달 시 OPEN 상태로
            if self._failure_count >= self.failure_threshold:
                self._open_circuit()

            raise exc  # 예외는 상위 호출자에게 다시 전달
        else:
            # 성공 시: 만약 HALF_OPEN 상태였다면 회복 성공으로 보고 CLOSED 전환
            if self._state == 'HALF_OPEN':
                self._close_circuit()
            # 카운트 리셋
            self._failure_count = 0
            return response

    def call_with_retry(
        self,
        func,
        *args,
        max_retries: int = 3,
        retry_delay: float = 1.0,  # 초 단위
        fallback_func=None,        # 최대 재시도 초과 시 대체 로직
        notify=False,              # 최대 재시도 초과 시 알림 전송 여부
        **kwargs
    ):
        """
        서킷브레이커로 보호된 함수 호출 시, 추가로 max_retries만큼 재시도하는 메서드.
        - max_retries를 넘기면 fallback_func 수행(있을 경우) 
        - notify=True 인 경우 모든 관련 어플리케이션에 알림 전송

            response = circuit_breaker.call_with_retry(
                requests.get,
                "http://example.com",
                max_retries=3,
                fallback_func=my_fallback,
                notify=True
            )
        """
        last_exception = None

        for attempt in range(1, max_retries + 1):
            try:
                return self.call(func, *args, **kwargs)

            except self.expected_exception as exc:
                print(f"[Retry] 재시도 {attempt}/{max_retries} 실패: {exc}")
                last_exception = exc

                # 마지막 retry 시
                if attempt == max_retries:
                    # if notify: 모든 관련 서비스에 알림.
                    if notify:
                        notify_applications(
                            f"서비스 호출 재시도({max_retries}회) 모두 실패."
                        )
                    
                    # if fallback_func: 대체 로직
                    if callable(fallback_func):
                        print("재시도 전략 : Fallback 함수로 대체 처리.")
                        return fallback_func()
                    
                    # fallback_func == None: 마지막 예외 re-raise
                    raise exc

                # 재시도 대기
                time.sleep(retry_delay)

        # for loop end == None: 마지막 예외 re-raise
        raise last_exception


circuit_breaker = CircuitBreaker(
    failure_threshold = 3,     # 조건 1. 3회 연속 실패시 open
    recovery_timeout = 5,      # 조건 2. 5초 후 half_open
    expected_exception = requests.exceptions.RequestException
)

# 2) fallback : 연관된 어플리케이션들에 관련 내용 전달
def fallback():
    return "fallback_response"

# 3) 외부 서비스 api
def external_service_call(url):
    return requests.get(url, timeout = 1)

test_url = "http://127.0.0.1/api/v1"  

# 4) 재시도 전략
try:
    # max_retries = 3번까지 재시도 후 실패 시 fallback_func 실행 + notify 옵션 켜기
    response = circuit_breaker.call_with_retry(
        external_service_call,
        url = test_url,
        max_retries = 3,
        retry_delay = 1.0,
        fallback_func = fallback,
        notify = True
    )

    print(f"status: {response}")

except Exception as e:
    # fallback_func도 없거나, fallback 후에도 문제가 있다면
    print("final error:", e)