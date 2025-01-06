from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

# 허용할 도메인 리스트
origins = [
    "http://localhost",
    "http://localhost:8000",
    "http://yourdomain.com",
    # DNS추가
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,          # 출처
    allow_credentials=True,         # 쿠키, 인증
    allow_methods=["*"],            # CRUD
    allow_headers=["*"],            # HTTP header
)

@app.get("/")
def idnex():
    return {"message": "CORS"}


# CORS 설정 x -> 다른 DNS에서 접근 시
# front : http://localhost:3000에서 app rund
# back : http://localhost:8000에서 FastAPI app 실행 (CORS 설정 없음).
# request: front에서 fetch('http://localhost:8000/') 
# result : 브라우저가 CORS 정책으로 요청 차단.