from pymongo import MongoClient
from pymongo.database import Database
from pymongo.errors import ConnectionFailure

from utils import get_environment_variable

MONGODB_URL = get_environment_variable('MONGODB_URL')
MONGO_INITDB_DATABASE = get_environment_variable('MONGO_INITDB_DATABASE')


class MongoConnection:

    def __init__(self, url: str, database_name: str):
        self.url = url
        self.database_name = database_name
        self.client: MongoClient | None = None
        self.db: Database | None = None

    def __enter__(self):
        try:
            self.client = MongoClient(self.url)
        except ConnectionFailure:
            raise ConnectionFailure(f'Не удалось подключиться к базе данных')
        self.db = self.client[self.database_name]
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        try:
            self.client.close()
        except ConnectionFailure:
            raise ConnectionFailure('Не удалось закрыть подключение к базе данных')
