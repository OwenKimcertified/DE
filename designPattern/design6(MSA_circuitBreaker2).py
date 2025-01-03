import os
import httpx
from tenacity import retry, stop_after_attempt, wait_exponential
import pybreaker
import logging
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException

# .env 설정하기
# load_dotenv()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 서킷 브레이커 설정
circuit_breaker = pybreaker.CircuitBreaker(fail_max = 5, reset_timeout = 60)

# OS env -> api gateway url, jwt token information
API_GATEWAY_URL = os.getenv("API_GATEWAY_URL", "https://api-gateway.example.com/service-b/api/data")
AUTH_TOKEN = os.getenv("AUTH_TOKEN", "your_default_jwt_token_here")

@circuit_breaker
@retry(stop = stop_after_attempt(3), wait = wait_exponential(multiplier = 1, min = 4, max = 10)) # 10회 초과 시 open
async def call_service_b():
    headers = {}
    if AUTH_TOKEN:
        headers["Authorization"] = f"Bearer {AUTH_TOKEN}"
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(API_GATEWAY_URL, headers=headers, timeout=5.0)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error occurred: {e.response.status_code} - {e.response.text}")
            raise
        except httpx.RequestError as e:
            logger.error(f"Request error occurred: {e}")
            raise

app = FastAPI()

@app.get("/fetch-data")
async def fetch_data():
    try:
        data = await call_service_b()
        # b 서비스 로직을 기다린다
        return data
    except pybreaker.CircuitBreakerError:
        # B 서비스 max retry 실패 시
        logger.error("Service B is unavailable (circuit breaker open).")
        raise HTTPException(status_code = 503, detail = "Service B is unavailable.")
    except httpx.HTTPStatusError as e:
        # 응답 코드가 기대했던 것과 다르면
        logger.error(f"Service B returned an error: {e.response.status_code} - {e.response.text}")
        raise HTTPException(status_code = e.response.status_code, detail = "Service B error.")
    except httpx.RequestError as e:
        # 요청에 실패하면
        logger.error(f"Failed to call Service B: {e}")
        raise HTTPException(status_code = 500, detail = "Internal Server Error.")