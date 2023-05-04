from fastapi import APIRouter, Body, Depends, HTTPException
from fastapi.encoders import jsonable_encoder
from starlette.status import (
    HTTP_201_CREATED, HTTP_200_OK, HTTP_404_NOT_FOUND,
    HTTP_422_UNPROCESSABLE_ENTITY
)

from auth import get_api_key
from schemas import ApprovalProcess, ApprovalProcessStatus, Offer
from tasks.approval_process_tasks import (
    create_approval_process_task, get_approval_process_status_task,
    get_approval_processes_task, change_approval_process_status_task,
    get_approval_process_offers_task,
)

router = APIRouter(
    tags=['approval_processes'],
    prefix='/approval_processes',
    dependencies=[Depends(get_api_key)]
)


@router.post(
    '/',
    status_code=HTTP_201_CREATED,
    response_model=ApprovalProcess
)
async def create_approval_process(
        approval_process: ApprovalProcess = Body(...)
):
    """Добавление процесса согласования акционной продажи."""
    approval_process = jsonable_encoder(approval_process)
    task = create_approval_process_task.delay(approval_process)
    return task.get()


@router.get(
    '/{sale_id}/status',
    status_code=HTTP_200_OK
)
async def get_approval_process_status(
        sale_id: str
):
    """Получение статуса процесса согласования акционной продажи по ID продажи."""
    task = get_approval_process_status_task.delay(sale_id)
    approval_process = task.get()
    if approval_process == HTTP_404_NOT_FOUND:
        raise HTTPException(
            status_code=HTTP_404_NOT_FOUND,
            detail='Процесс согласования не найден'
        )
    return approval_process


@router.get(
    '/',
    status_code=HTTP_200_OK,
    response_model=list[ApprovalProcess]
)
async def get_approval_processes():
    """Получение списка процессов согласования акционных продаж, требующих решения."""
    task = get_approval_processes_task.delay()
    return task.get()


@router.patch(
    '/{sale_id}/status',
    status_code=HTTP_200_OK,
    response_model=ApprovalProcess
)
async def change_approval_process_status(
        sale_id: str,
        approval_process_status: ApprovalProcessStatus = Body(...),
):
    """Изменение статуса процесса согласования акционной продажи по ID продажи."""
    task = change_approval_process_status_task.delay(sale_id, approval_process_status)
    updated_approval_process = task.get()
    if updated_approval_process == HTTP_404_NOT_FOUND:
        raise HTTPException(
            status_code=HTTP_404_NOT_FOUND,
            detail='Процесс согласования не найден'
        )
    return updated_approval_process


@router.get(
    '/{sale_id}/offers',
    status_code=HTTP_200_OK,
    response_model=list[Offer]
)
async def get_approval_process_offers(
        sale_id: str
):
    """Получение списка применённых акций к товару (продажа зафиксирована)."""
    task = get_approval_process_offers_task.delay(sale_id)
    approval_process_offers = task.get()
    if approval_process_offers == HTTP_404_NOT_FOUND:
        raise HTTPException(
            status_code=HTTP_404_NOT_FOUND,
            detail='Процесс согласования не найден'
        )
    if approval_process_offers == HTTP_422_UNPROCESSABLE_ENTITY:
        raise HTTPException(
            status_code=HTTP_422_UNPROCESSABLE_ENTITY,
            detail='Продажа товара не зафиксирована'
        )
    return approval_process_offers
