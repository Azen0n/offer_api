from fastapi import FastAPI
from tasks import add as add_task

app = FastAPI()


@app.get('/')
async def root():
    return {'message': 'Hello World'}


@app.get('/add')
async def add(x: int, y: int):
    result = add_task.delay(x, y)
    return result.get()
