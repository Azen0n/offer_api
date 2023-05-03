from pymongo import MongoClient

from utils import get_environment_variable

MONGODB_URL = get_environment_variable('MONGODB_URL')
MONGO_INITDB_DATABASE = get_environment_variable('MONGO_INITDB_DATABASE')

client = MongoClient(MONGODB_URL, uuidRepresentation='standard')
db = client[MONGO_INITDB_DATABASE]
