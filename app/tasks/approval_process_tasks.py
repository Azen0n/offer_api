from pymongo import ReturnDocument
from starlette.status import HTTP_404_NOT_FOUND, HTTP_422_UNPROCESSABLE_ENTITY

from celery_app import app

from database import db
from schemas import ApprovalProcessStatus
from tasks.utils import product_exists, sale_exists, offers_exists


@app.task
def create_approval_process_task(approval_process: dict) -> tuple[dict | None, dict | None]:
    """Добавление процесса согласования акционной продажи.

    Возвращает ApprovalProcess в виде словаря и словарь
    с кодом ошибки и описанием. При отсутствии один из элементов равен None.
    """
    if not product_exists(approval_process['product']['_id']):
        return None, {'status_code': HTTP_422_UNPROCESSABLE_ENTITY,
                      'detail': 'Товар не найден'}
    if not sale_exists(approval_process['sale']['_id']):
        return None, {'status_code': HTTP_422_UNPROCESSABLE_ENTITY,
                      'detail': 'Продажа не найдена'}
    offer_ids = [offer['_id'] for offer in approval_process['offers']]
    if not offers_exists(offer_ids):
        return None, {'status_code': HTTP_422_UNPROCESSABLE_ENTITY,
                      'detail': 'Одна или более акции не существуют'}
    new_approval_process = db['approval_processes'].insert_one(approval_process)
    created_approval_process = db['approval_processes'].find_one(
        {'_id': new_approval_process.inserted_id}
    )
    return created_approval_process, None


@app.task
def get_approval_process_status_task(sale_id: int) -> tuple[dict | None, dict | None]:
    """Получение статуса процесса согласования акционной продажи по ID продажи.

    Возвращает ApprovalProcessStatus в виде словаря и словарь
    с кодом ошибки и описанием. При отсутствии один из элементов равен None.
    """
    approval_process = db['approval_processes'].find_one({'sale._id': sale_id})
    if approval_process is None:
        return None, {'status_code': HTTP_404_NOT_FOUND,
                      'detail': 'Процесс согласования не найден'}
    return {'status': approval_process['status']}, None


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
) -> tuple[dict | None, dict | None]:
    """Изменение статуса процесса согласования акционной продажи по ID продажи.

    Возвращает обновленный ApprovalProcess в виде словаря и словарь
    с кодом ошибки и описанием. При отсутствии один из элементов равен None.
    """
    approval_process = db['approval_processes'].find_one({'sale._id': sale_id})
    if approval_process is None:
        return None, {'status_code': HTTP_404_NOT_FOUND,
                      'detail': 'Процесс согласования не найден'}
    updated_approval_process = db['approval_processes'].find_one_and_update(
        {'_id': approval_process['_id']},
        {'$set': {'status': approval_process_status}},
        return_document=ReturnDocument.AFTER
    )
    return updated_approval_process, None


@app.task
def get_approval_process_offers_task(sale_id: int) -> tuple[list[dict] | None, dict | None]:
    """Получение списка применённых акций к товару (продажа зафиксирована)
    по ID продажи.

    Возвращает список Offer в виде словарей и словарь
    с кодом ошибки и описанием. При отсутствии один из элементов равен None.
    """
    approval_process = db['approval_processes'].find_one({'sale._id': sale_id})
    if approval_process is None:
        return None, {'status_code': HTTP_404_NOT_FOUND,
                      'detail': 'Процесс согласования не найден'}
    if approval_process['status'] != ApprovalProcessStatus.APPROVED.value:
        return None, {'status_code': HTTP_422_UNPROCESSABLE_ENTITY,
                      'detail': 'Продажа товара не зафиксирована'}
    offer_ids = [offer['_id'] for offer in approval_process['offers']]
    approval_process_offers = list(db['offers'].find({'_id': {'$in': offer_ids}}))
    return approval_process_offers, None
