from fastapi import APIRouter, Body, Request, status, Depends, HTTPException
from fastapi.encoders import jsonable_encoder
from fastapi.openapi.models import APIKey
from pymongo import ReturnDocument
from starlette.status import HTTP_404_NOT_FOUND

from auth import get_api_key
from schemas import ApprovalProcess, ApprovalProcessStatus, Offer

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
    new_approval_process = request.app.database['approval_processes'].insert_one(approval_process)
    created_approval_process = request.app.database['approval_processes'].find_one(
        {'_id': new_approval_process.inserted_id}
    )
    return created_approval_process


@router.get('/{sale_id}/status')
def get_approval_process_status(
        request: Request,
        sale_id: str,
        api_key: APIKey = Depends(get_api_key)
):
    """Получение статуса процесса согласования акционной продажи по ID продажи."""
    approval_process = request.app.database['approval_processes'].find_one({'sale._id': sale_id})
    if approval_process:
        return {'status': approval_process['status']}
    raise HTTPException(status_code=HTTP_404_NOT_FOUND)


@router.get(
    '/',
    response_model=list[ApprovalProcess]
)
def get_approval_processes(
        request: Request,
        api_key: APIKey = Depends(get_api_key)
):
    """Получение списка процессов согласования акционных продаж, требующих решения."""
    approval_processes = list(request.app.database['approval_processes'].find(
        {'status': ApprovalProcessStatus.PENDING.value})
    )
    return approval_processes


@router.patch(
    '/{sale_id}/status',
    response_model=ApprovalProcess
)
def change_approval_process_status(
        request: Request,
        sale_id: str,
        approval_process_status: ApprovalProcessStatus = Body(...),
        api_key: APIKey = Depends(get_api_key)
):
    """Изменение статуса процесса согласования акционной продажи по ID продажи."""
    approval_process = request.app.database['approval_processes'].find_one({'sale._id': sale_id})
    if not approval_process:
        raise HTTPException(status_code=HTTP_404_NOT_FOUND)
    updated_approval_process = request.app.database['approval_processes'].find_one_and_update(
        {'_id': approval_process['_id']},
        {'$set': {'status': approval_process_status.value}},
        return_document=ReturnDocument.AFTER
    )
    return updated_approval_process


@router.get(
    '/{sale_id}/offers',
    response_model=list[Offer]
)
def get_approval_process_offers(
        request: Request,
        sale_id: str,
        api_key: APIKey = Depends(get_api_key)
):
    """Получение списка применённых акций к товару (продажа зафиксирована)."""
    approval_process = request.app.database['approval_processes'].find_one({'sale._id': sale_id})
    if approval_process['status'] != ApprovalProcessStatus.APPROVED.value:
        raise HTTPException(status_code=HTTP_404_NOT_FOUND, detail='Продажа товара не зафиксирована')
    return approval_process['offers']
