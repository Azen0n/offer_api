from fastapi import FastAPI
from pymongo import MongoClient

from utils import get_environment_variable
from tasks import add as add_task
from routers import offer_router

app = FastAPI()
MONGODB_URL = get_environment_variable('MONGODB_URL')
MONGO_INITDB_DATABASE = get_environment_variable('MONGO_INITDB_DATABASE')

app.include_router(offer_router, tags=['offers'], prefix='/offers')


@app.on_event('startup')
def startup_db_client():
    app.mongodb_client = MongoClient(MONGODB_URL, uuidRepresentation='standard')
    app.database = app.mongodb_client[MONGO_INITDB_DATABASE]


@app.on_event('shutdown')
def shutdown_db_client():
    app.mongodb_client.close()


@app.get('/')
async def root():
    return {'message': 'Hello World'}


@app.get('/add')
async def add(x: int, y: int):
    result = add_task.delay(x, y)
    return result.get()
