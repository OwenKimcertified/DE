import threading
import logging

from fastapi import FastAPI, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime

from DBMS import DenormalizedData, SessionLocal
from binlog_reader import start_binlog_stream
from schemas_dto import DenormalizedDataSchema  

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

app = FastAPI(title="CQRS CDC Pipeline")

# Binlog Reader를 백그라운드 스레드로 실행
def start_binlog_thread():
    binlog_thread = threading.Thread(target=start_binlog_stream, daemon=True)
    binlog_thread.start()

@app.lifespan("startup")
def lifespans():
    start_binlog_thread()
    logger.info("Binlog Reader started.")

@app.get("/data", response_model=List[DenormalizedDataSchema])
def get_data(user_id: Optional[int] = None):
    session: Session = SessionLocal()
    try:
        query = session.query(DenormalizedData)
        if user_id is not None:
            query = query.filter_by(user_id=user_id)
        results = query.all()
        return results
    except Exception as e:
        logger.error(f"Query Error: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")
    finally:
        session.close()