import os
from dotenv import load_dotenv
from pydantic import BaseSettings

load_env = load_dotenv()

class Settings(BaseSettings):
    # MySQL 설정
    mysql_host: str = os.getenv('MYSQL_HOST')
    mysql_port: int = int(os.getenv('MYSQL_PORT'))
    mysql_user: str = os.getenv('MYSQL_USER')
    mysql_password: str = os.getenv('MYSQL_PASSWORD')
    mysql_server_id: int = int(os.getenv('MYSQL_SERVER_ID'))
    mysql_log_file: str = os.getenv('MYSQL_LOG_FILE')
    mysql_log_pos: int = int(os.getenv('MYSQL_LOG_POS'))

    # PostgreSQL 설정
    postgres_username: str = os.getenv('POSTGRES_USERNAME')
    postgres_password: str = os.getenv('POSTGRES_PASSWORD')
    postgres_host: str = os.getenv('POSTGRES_HOST')
    postgres_port: int = int(os.getenv('POSTGRES_PORT'))
    postgres_database: str = os.getenv('POSTGRES_DATABASE')

    # FastAPI 설정
    fastapi_host: str = os.getenv('FASTAPI_HOST')
    fastapi_port: int = int(os.getenv('FASTAPI_PORT'))

class Config:
    env_file = ".env"

settings = Settings()