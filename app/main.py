import logging

from fastapi import FastAPI, Depends

from middleware.auth import check_api_key
from routers import offer_router, approval_process_router

logging.basicConfig(level=logging.INFO, filename='logs.log', filemode='a',
                    format='%(asctime)s %(levelname)s %(message)s')
logger = logging.getLogger(__name__)
logger.info('Запуск приложения FastAPI')

app = FastAPI()

app.include_router(
    offer_router,
    tags=['offers'],
    prefix='/offers',
    dependencies=[Depends(check_api_key)]
)

app.include_router(
    approval_process_router,
    tags=['approval_processes'],
    prefix='/approval_processes',
    dependencies=[Depends(check_api_key)]
)
