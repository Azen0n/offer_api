from pymongo import ReturnDocument
from starlette.status import HTTP_404_NOT_FOUND, HTTP_422_UNPROCESSABLE_ENTITY

from celery_app import app

from database import db
from schemas import ApprovalProcessStatus


@app.task
def create_approval_process_task(approval_process: dict) -> dict:
    """Добавление процесса согласования акционной продажи.

    Возвращает ApprovalProcess в виде словаря.
    """
    new_approval_process = db['approval_processes'].insert_one(approval_process)
    created_approval_process = db['approval_processes'].find_one(
        {'_id': new_approval_process.inserted_id}
    )
    return created_approval_process


@app.task
def get_approval_process_status_task(sale_id: int) -> dict | int:
    """Получение статуса процесса согласования акционной продажи по ID продажи.

    Возвращает ApprovalProcessStatus в виде словаря или код состояния 404,
    если процесс согласования не найден.
    """
    approval_process = db['approval_processes'].find_one({'sale._id': sale_id})
    if approval_process is None:
        return HTTP_404_NOT_FOUND
    return {'status': approval_process['status']}


@app.task
def get_approval_processes_task() -> list[dict]:
    """Получение списка процессов согласования акционных продаж, требующих решения.

    Возвращает список ApprovalProcess в виде словарей.
    """
    approval_processes = list(db['approval_processes'].find(
        {'status': ApprovalProcessStatus.PENDING.value})
    )
    return approval_processes


@app.task
def change_approval_process_status_task(
        sale_id: int,
        approval_process_status: str
) -> dict | int:
    """Изменение статуса процесса согласования акционной продажи по ID продажи.

    Возвращает обновленный ApprovalProcess в виде словаря или код состояния 404,
    если процесс согласования не найден.
    """
    approval_process = db['approval_processes'].find_one({'sale._id': sale_id})
    if approval_process is None:
        return HTTP_404_NOT_FOUND
    updated_approval_process = db['approval_processes'].find_one_and_update(
        {'_id': approval_process['_id']},
        {'$set': {'status': approval_process_status}},
        return_document=ReturnDocument.AFTER
    )
    return updated_approval_process


@app.task
def get_approval_process_offers_task(sale_id: int) -> list[dict] | int:
    """Получение списка применённых акций к товару (продажа зафиксирована)
    по ID продажи.

    Возвращает список Offer в виде словарей или код состояния:
    - 404, если процесс согласования не найден;
    - 422, если продажа не зафиксирована.
    """
    approval_process = db['approval_processes'].find_one({'sale._id': sale_id})
    if approval_process is None:
        return HTTP_404_NOT_FOUND
    if approval_process['status'] != ApprovalProcessStatus.APPROVED.value:
        return HTTP_422_UNPROCESSABLE_ENTITY
    offer_ids = [offer['_id'] for offer in approval_process['offers']]
    approval_process_offers = list(db['offers'].find({'_id': {'$in': offer_ids}}))
    return approval_process_offers
