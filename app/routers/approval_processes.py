from fastapi import APIRouter, Body, Request, status, Depends, HTTPException
from fastapi.encoders import jsonable_encoder
from fastapi.openapi.models import APIKey
from starlette.status import HTTP_404_NOT_FOUND, HTTP_422_UNPROCESSABLE_ENTITY

from auth import get_api_key
from schemas import ApprovalProcess, ApprovalProcessStatus, Offer
from tasks.approval_process_tasks import (
    create_approval_process_task, get_approval_process_status_task,
    get_approval_processes_task, change_approval_process_status_task,
    get_approval_process_offers_task,
)

router = APIRouter()


@router.post(
    '/',
    status_code=status.HTTP_201_CREATED,
    response_model=ApprovalProcess
)
def create_approval_process(
        request: Request,
        approval_process: ApprovalProcess = Body(...),
        api_key: APIKey = Depends(get_api_key)
):
    """Добавление процесса согласования акционной продажи."""
    approval_process = jsonable_encoder(approval_process)
    task = create_approval_process_task.delay(approval_process)
    return task.get()


@router.get(
    '/{sale_id}/status',
    status_code=status.HTTP_200_OK,
)
def get_approval_process_status(
        request: Request,
        sale_id: str,
        api_key: APIKey = Depends(get_api_key)
):
    """Получение статуса процесса согласования акционной продажи по ID продажи."""
    task = get_approval_process_status_task.delay(sale_id)
    approval_process = task.get()
    if approval_process == HTTP_404_NOT_FOUND:
        raise HTTPException(status_code=HTTP_404_NOT_FOUND, detail='Процесс согласования не найден')
    return approval_process


@router.get(
    '/',
    status_code=status.HTTP_200_OK,
    response_model=list[ApprovalProcess]
)
def get_approval_processes(
        request: Request,
        api_key: APIKey = Depends(get_api_key)
):
    """Получение списка процессов согласования акционных продаж, требующих решения."""
    task = get_approval_processes_task.delay()
    return task.get()


@router.patch(
    '/{sale_id}/status',
    status_code=status.HTTP_200_OK,
    response_model=ApprovalProcess
)
def change_approval_process_status(
        request: Request,
        sale_id: str,
        approval_process_status: ApprovalProcessStatus = Body(...),
        api_key: APIKey = Depends(get_api_key)
):
    """Изменение статуса процесса согласования акционной продажи по ID продажи."""
    task = change_approval_process_status_task.delay(sale_id, approval_process_status)
    updated_approval_process = task.get()
    if updated_approval_process == HTTP_404_NOT_FOUND:
        raise HTTPException(status_code=HTTP_404_NOT_FOUND, detail='Процесс согласования не найден')
    return updated_approval_process


@router.get(
    '/{sale_id}/offers',
    status_code=status.HTTP_200_OK,
    response_model=list[Offer]
)
def get_approval_process_offers(
        request: Request,
        sale_id: str,
        api_key: APIKey = Depends(get_api_key)
):
    """Получение списка применённых акций к товару (продажа зафиксирована)."""
    task = get_approval_process_offers_task.delay(sale_id)
    approval_process_offers = task.get()
    if approval_process_offers == HTTP_404_NOT_FOUND:
        raise HTTPException(status_code=HTTP_404_NOT_FOUND, detail='Процесс согласования не найден')
    if approval_process_offers == HTTP_422_UNPROCESSABLE_ENTITY:
        raise HTTPException(status_code=HTTP_422_UNPROCESSABLE_ENTITY, detail='Продажа товара не зафиксирована')
    return approval_process_offers
