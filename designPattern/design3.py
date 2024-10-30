from abc import ABC, abstractmethod

class DatabaseService(ABC):
    @abstractmethod
    def connect(self):
        pass

class MySQLService(DatabaseService):
    def connect(self):
        print("MySQL connected.")

class UserService:
    def __init__(self, db_service: DatabaseService):
        self.db_service = db_service

    def get_user(self, user_id):
        self.db_service.connect()
        print(f"Getting user {user_id}")

# 사용 예시
mysql_service = MySQLService()
user_service = UserService(mysql_service) # 인터페이스로 추상 클래스에 대한 적절한 구현하기.
user_service.get_user(123)