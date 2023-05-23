import logging
from typing import Annotated

from fastapi import APIRouter, Body, HTTPException, Query
from fastapi.encoders import jsonable_encoder
from starlette.status import HTTP_201_CREATED, HTTP_200_OK

from routers.utils import get_task_result_or_timeout
from schemas import ApprovalProcess, ApprovalProcessStatus
from schemas.approval_process import CreateApprovalProcess
from schemas.offer import Offer
from tasks.approval_process_tasks import (
    create_approval_process_task, get_approval_process_status_task,
    get_approval_processes_task, change_approval_process_status_task,
    get_approval_process_offers_task,
)
from utils import get_environment_variable

logger = logging.getLogger(__name__)
router = APIRouter()

DEFAULT_PAGE_SIZE = int(get_environment_variable('DEFAULT_PAGE_SIZE'))


@router.post(
    '/',
    status_code=HTTP_201_CREATED,
    response_model=ApprovalProcess
)
async def create_approval_process(
        approval_process: CreateApprovalProcess = Body(...)
):
    """Добавление процесса согласования акционной продажи."""
    logger.info(f'Поступил запрос на {create_approval_process.__name__},'
                f' {approval_process=}')
    approval_process = jsonable_encoder(approval_process)
    task = create_approval_process_task.delay(approval_process)
    approval_process, error = task.get()
    if approval_process is None:
        logger.error(f'Ошибка: {error["detail"]}')
        raise HTTPException(**error)
    return approval_process


@router.get(
    '/{sale_id}/status',
    status_code=HTTP_200_OK
)
async def get_approval_process_status(
        sale_id: int
):
    """Получение статуса процесса согласования акционной продажи
    по ID продажи.
    """
    logger.info(f'Поступил запрос на {get_approval_process_status.__name__},'
                f' {sale_id=}')
    approval_process, error = get_task_result_or_timeout(
        get_approval_process_status_task,
        sale_id
    )
    if approval_process is None:
        logger.error(f'Ошибка: {error["detail"]}')
        raise HTTPException(**error)
    return approval_process


@router.get(
    '/',
    status_code=HTTP_200_OK,
    response_model=list[ApprovalProcess]
)
async def get_approval_processes():
    """Получение списка процессов согласования акционных продаж,
    требующих решения.
    """
    logger.info(f'Поступил запрос на {get_approval_processes.__name__}')
    approval_processes, error = get_task_result_or_timeout(
        get_approval_processes_task
    )
    if approval_processes is None:
        logger.error(f'Ошибка: {error["detail"]}')
        raise HTTPException(**error)
    return approval_processes


@router.patch(
    '/{sale_id}/status',
    status_code=HTTP_200_OK,
    response_model=ApprovalProcess
)
async def change_approval_process_status(
        sale_id: int,
        approval_process_status: ApprovalProcessStatus = Body(...),
):
    """Изменение статуса процесса согласования акционной продажи
    по ID продажи.
    """
    logger.info(f'Поступил запрос на {change_approval_process_status.__name__},'
                f' {sale_id=}, {approval_process_status=}')
    updated_approval_process, error = get_task_result_or_timeout(
        change_approval_process_status_task,
        sale_id,
        approval_process_status
    )
    if updated_approval_process is None:
        logger.error(f'Ошибка: {error["detail"]}')
        raise HTTPException(**error)
    return updated_approval_process


@router.get(
    '/{sale_id}/offers',
    status_code=HTTP_200_OK,
    response_model=list[Offer]
)
async def get_approval_process_offers(
        sale_id: int,
        products_page_number: Annotated[int, Query(
            description='Страница списка подходящих товаров',
            gt=0
        )] = 1,
        products_page_size: Annotated[int, Query(
            description='Количество товаров на странице в списке подходящих товаров',
            gt=0
        )] = DEFAULT_PAGE_SIZE
):
    """Получение списка применённых акций к товару (продажа зафиксирована)."""
    logger.info(f'Поступил запрос на {get_approval_process_offers.__name__},'
                f' {sale_id=}, {products_page_number=}, {products_page_size}')
    approval_process_offers, error = get_task_result_or_timeout(
        get_approval_process_offers_task,
        sale_id,
        products_page_number,
        products_page_size
    )
    if approval_process_offers is None:
        logger.error(f'Ошибка: {error["detail"]}')
        raise HTTPException(**error)
    return approval_process_offers
