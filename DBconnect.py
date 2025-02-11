import importlib

# dot env 권장
# repl_user, repl_pass

class DatabaseConnector:
    DB_DRIVERS = {
        "mysql": "pymysql",
        "..." : "..."
    }
    
    def __init__(self, DBMS, **connectParams):
        self.connectParams = connectParams
        self.DBMS = importlib.import_module(self.DB_DRIVERS[DBMS])
        self.conn = None
        
    def connect(self):
        if self.conn is not None:
            return self.conn
        else:
            
            self.conn = self.DBMS.connect(**self.connectParams)

    def close(self):
        if self.conn is not None:
            self.conn.close()
            self.conn = None
            
mc = DatabaseConnector('mysql', host = 'localhost', port = 3308, user = 'repl_user', password = 'repl_pass')
mc.connect()