from fastapi import APIRouter, Body, HTTPException
from fastapi.encoders import jsonable_encoder
from starlette.status import HTTP_201_CREATED, HTTP_200_OK

from schemas import ApprovalProcess, ApprovalProcessStatus
from schemas.approval_process import CreateApprovalProcess
from schemas.offer import Offer
from tasks.approval_process_tasks import (
    create_approval_process_task, get_approval_process_status_task,
    get_approval_processes_task, change_approval_process_status_task,
    get_approval_process_offers_task,
)

router = APIRouter()


@router.post(
    '/',
    status_code=HTTP_201_CREATED,
    response_model=ApprovalProcess
)
async def create_approval_process(
        approval_process: CreateApprovalProcess = Body(...)
):
    """Добавление процесса согласования акционной продажи."""
    approval_process = jsonable_encoder(approval_process)
    task = create_approval_process_task.delay(approval_process)
    approval_process, error = task.get()
    if approval_process is None:
        raise HTTPException(**error)
    return approval_process


@router.get(
    '/{sale_id}/status',
    status_code=HTTP_200_OK
)
async def get_approval_process_status(
        sale_id: int
):
    """Получение статуса процесса согласования акционной продажи по ID продажи."""
    task = get_approval_process_status_task.delay(sale_id)
    approval_process, error = task.get()
    if approval_process is None:
        raise HTTPException(**error)
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
        sale_id: int,
        approval_process_status: ApprovalProcessStatus = Body(...),
):
    """Изменение статуса процесса согласования акционной продажи по ID продажи."""
    task = change_approval_process_status_task.delay(sale_id, approval_process_status)
    updated_approval_process, error = task.get()
    if updated_approval_process is None:
        raise HTTPException(**error)
    return updated_approval_process


@router.get(
    '/{sale_id}/offers',
    status_code=HTTP_200_OK,
    response_model=list[Offer]
)
async def get_approval_process_offers(
        sale_id: int
):
    """Получение списка применённых акций к товару (продажа зафиксирована)."""
    task = get_approval_process_offers_task.delay(sale_id)
    approval_process_offers, error = task.get()
    if approval_process_offers is None:
        raise HTTPException(**error)
    return approval_process_offers
