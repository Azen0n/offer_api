from fastapi import FastAPI, Depends

from auth import get_api_key
from routers import offer_router, approval_process_router

app = FastAPI()

app.include_router(
    offer_router,
    tags=['offers'],
    prefix='/offers',
    dependencies=[Depends(get_api_key)]
)

app.include_router(
    approval_process_router,
    tags=['approval_processes'],
    prefix='/approval_processes',
    dependencies=[Depends(get_api_key)]
)
