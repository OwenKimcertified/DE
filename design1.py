# Constructor inject

class DatabaseService:
    def connect(self):
        print("Database connected.")

class UserService:
    def __init__(self, db_service: DatabaseService):
        self.db_service = db_service

    def get_user(self, user_id):
        self.db_service.connect()
        print(f"Getting user {user_id}")

db_service = DatabaseService() # 객체 생성
user_service = UserService(db_service) # 생성한 객체에 바로 다른 객체를 투입 (의존성 주입)
user_service.get_user(123) # DI 상태, DB 연결 후 사용자 생성  