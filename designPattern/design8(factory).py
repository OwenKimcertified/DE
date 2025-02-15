from abc import ABC, abstractmethod
from dotenv import load_dotenv
import importlib, os

load_dotenv()

class DBComponent(ABC):
    __status = None
    __DB_DRIVERS = {
        "mysql": "pymysql",
        "postgresql": "psycopg2",
        "sqlite": "sqlite3"
    }
    __slots__ = ["conn", "args"]

    def __init__(self, *args):
        self.conn = None
        self.args = args

    @abstractmethod
    def dbConnect(self):
        pass

    @classmethod
    def create(cls, DBMS, *args):
        if DBMS not in cls.__DB_DRIVERS:
            raise ValueError(f"not support DBMS: {DBMS}")

        module_name = cls.__DB_DRIVERS[DBMS]
        db_module = importlib.import_module(module_name)
        
        class ConcreteDBComponent(cls):
            def dbConnect(self):
                if self.conn is None:
                    self.conn = db_module.connect(*self.args)
                return self.conn
        
        return ConcreteDBComponent(*args)
    
    @classmethod
    def getStatus(cls):
        return cls.__status
    
class mysql(DBComponent):
    def dbConnect(self, *args):
        self.dbConnect(*args)
        
###############

from abc import ABC, abstractmethod
from typing import Optional, Dict, Any
from dotenv import load_dotenv
import importlib, os

load_dotenv()

class DBConnection(ABC):
    _DRIVERS = {
        'mysql': ('pymysql', 'connect'),
        'postgresql': ('psycopg2', 'connect'),
        'sqlite': ('sqlite3', 'connect')
    }
    
    def __init__(self, **config):
        self.config = config
        self._connection = None
        self._module = None
        self._connect_func = None
    
    def _load_driver(self):
        if self._module is None:
            driver_info = self._DRIVERS.get(self.db_type)
            if driver_info is None:
                raise ValueError(f"Unsupported database type: {self.db_type}")
                
            module_name, connect_func_name = driver_info
            try:
                self._module = importlib.import_module(module_name)
                self._connect_func = getattr(self._module, connect_func_name)
            except ImportError as e:
                raise ImportError(f"Failed to import {module_name}: {e}")
    
    def connect(self) -> Any:
        if not self._connection:
            self._load_driver()
            self._connection = self._connect_func(**self.config)
        return self._connection
    
    def disconnect(self) -> None:
        if self._connection:
            self._connection.close()
            self._connection = None
            
    @property
    @abstractmethod
    def db_type(self) -> str:
        pass

class MySQLConnection(DBConnection):
    @property
    def db_type(self) -> str:
        return 'mysql'

class PostgreSQLConnection(DBConnection):
    @property
    def db_type(self) -> str:
        return 'postgresql'

class SQLiteConnection(DBConnection):
    @property
    def db_type(self) -> str:
        return 'sqlite'

class DBConnectionFactory:
    _connections: Dict[str, type] = {
        'mysql': MySQLConnection,
        'postgresql': PostgreSQLConnection,
        'sqlite': SQLiteConnection
    }
    
    @classmethod
    def register_connection(cls, name: str, connection_class: type) -> None:
        if not issubclass(connection_class, DBConnection):
            raise TypeError("e")
        cls._connections[name] = connection_class
    
    @classmethod
    def register_driver(cls, db_type: str, module_name: str, connect_func_name: str = 'connect') -> None:
        DBConnection._DRIVERS[db_type] = (module_name, connect_func_name)
    
    @classmethod
    def create(cls, db_type: str, **config) -> DBConnection:
        if db_type not in cls._connections:
            raise ValueError(f"지원x db타입: {db_type}")
            
        connection_class = cls._connections[db_type]
        return connection_class(**config)
    
