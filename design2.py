# Setter inject

from design1 import *

class UserService:
    def set_db_service(self, db_service):
        self.db_service = db_service

    def get_user(self, user_id):
        self.db_service.connect()
        print(f"Getting user {user_id}")

user_service = UserService() # 유저 서비스 객체 생성
db_service = DatabaseService() # 데이터 베이스 객체 생성
user_service.set_db_service(db_service) # 생성자에서 만든 객체에 바로 주입하지 않고 기존 객체의 메서드를 통해 주입 
user_service.get_user(123) # 유저 생성