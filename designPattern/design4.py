from injector import Injector, inject, Module, singleton

class DatabaseService:
    def connect(self):
        print("Database connected.")

class AppModule(Module):
    def configure(self, binder):
        binder.bind(DatabaseService, to = DatabaseService, scope = singleton)

class UserService:
    @inject
    def __init__(self, db_service: DatabaseService):
        self.db_service = db_service

    def get_user(self, user_id):
        self.db_service.connect()
        print(f"Getting user {user_id}")

injector = Injector([AppModule()]) # 객체 만든 놈
user_service = injector.get(UserService) # 만든 객체 쓰는 놈
user_service.get_user(123) # 만든 객체 쓰는 놈
