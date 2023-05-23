from bson import ObjectId
from pymongo import ReturnDocument
from pymongo.errors import ConnectionFailure

from celery_app import app
from database import MongoConnection, MONGODB_URL, MONGO_INITDB_DATABASE

from schemas import ApprovalProcessStatus
from tasks.utils import (
    change_approval_process_offers_status, validate_create_approval_process,
    convert_approval_process_objectid_fields_to_str, validate_get_approval_process_offers,
    validate_approval_process_exists, convert_offers_objectid_fields_to_str, get_offers_by_approval_process_offer_ids,
    update_approval_process_status,
)


@app.task(name='create_approval_process')
def create_approval_process_task(approval_process: dict) -> tuple[dict | None, dict | None]:
    """Добавление процесса согласования акционной продажи.

    Возвращает ApprovalProcess в виде словаря и словарь
    с кодом ошибки и описанием. При отсутствии один из элементов равен None.
    """
    try:
        with MongoConnection(MONGODB_URL, MONGO_INITDB_DATABASE) as mongo:
            error = validate_create_approval_process(mongo.db, approval_process)
            if error is not None:
                return None, error
            new_approval_process = mongo.db['approval_processes'].insert_one(approval_process)
            created_approval_process = mongo.db['approval_processes'].find_one(
                {'_id': new_approval_process.inserted_id}
            )
            convert_approval_process_objectid_fields_to_str(created_approval_process)
            return created_approval_process, None
    except ConnectionFailure as e:
        return None, {'status_code': 500, 'detail': f'{e}'}


@app.task(name='get_approval_process_status')
def get_approval_process_status_task(sale_id: int) -> tuple[dict | None, dict | None]:
    """Получение статуса процесса согласования акционной продажи по ID продажи.

    Возвращает ApprovalProcessStatus в виде словаря и словарь
    с кодом ошибки и описанием. При отсутствии один из элементов равен None.
    """
    try:
        with MongoConnection(MONGODB_URL, MONGO_INITDB_DATABASE) as mongo:
            approval_process = mongo.db['approval_processes'].find_one({'sale.id': sale_id})
            error = validate_approval_process_exists(approval_process)
            if error is not None:
                return None, error
            return {'status': approval_process['status']}, None
    except ConnectionFailure as e:
        return None, {'status_code': 500, 'detail': f'{e}'}


@app.task(name='get_approval_processes')
def get_approval_processes_task() -> tuple[list[dict] | None, dict | None]:
    """Получение списка процессов согласования акционных продаж, требующих решения.

    Возвращает список ApprovalProcess в виде словарей.
    """
    try:
        with MongoConnection(MONGODB_URL, MONGO_INITDB_DATABASE) as mongo:
            approval_processes = list(mongo.db['approval_processes'].find(
                {'status': ApprovalProcessStatus.PENDING.value})
            )
            for approval_process in approval_processes:
                convert_approval_process_objectid_fields_to_str(approval_process)
            return approval_processes, None
    except ConnectionFailure as e:
        return None, {'status_code': 500, 'detail': f'{e}'}


@app.task(name='change_approval_process_status')
def change_approval_process_status_task(
        sale_id: int,
        approval_process_status: str
) -> tuple[dict | None, dict | None]:
    """Изменение статуса процесса согласования акционной продажи по ID продажи.

    Возвращает обновленный ApprovalProcess в виде словаря и словарь
    с кодом ошибки и описанием. При отсутствии один из элементов равен None.
    """
    try:
        with MongoConnection(MONGODB_URL, MONGO_INITDB_DATABASE) as mongo:
            with mongo.client.start_session() as session:
                approval_process = mongo.db['approval_processes'].find_one({'sale.id': sale_id})
                error = validate_approval_process_exists(approval_process)
                if error is not None:
                    return None, error
                updated_approval_process = update_approval_process_status(
                    mongo.db, session, approval_process, approval_process_status
                )
                error = change_approval_process_offers_status(
                    mongo.db, session, approval_process, approval_process_status
                )
                if error is not None:
                    return None, error
                convert_approval_process_objectid_fields_to_str(updated_approval_process)
                return updated_approval_process, None
    except ConnectionFailure as e:
        return None, {'status_code': 500, 'detail': f'{e}'}


@app.task(name='get_approval_process_offers')
def get_approval_process_offers_task(
        sale_id: int,
        page_number: int,
        page_size: int
) -> tuple[list[dict] | None, dict | None]:
    """Получение списка применённых акций к товару (продажа зафиксирована)
    по ID продажи.

    Возвращает список Offer в виде словарей и словарь
    с кодом ошибки и описанием. При отсутствии один из элементов равен None.
    """
    try:
        with MongoConnection(MONGODB_URL, MONGO_INITDB_DATABASE) as mongo:
            approval_process = mongo.db['approval_processes'].find_one({'sale.id': sale_id})
            error = validate_get_approval_process_offers(approval_process)
            if error is not None:
                return None, error
            approval_process_offers = get_offers_by_approval_process_offer_ids(
                mongo.db,
                approval_process,
                page_number,
                page_size
            )
            convert_offers_objectid_fields_to_str(approval_process_offers)
            return approval_process_offers, None
    except ConnectionFailure as e:
        return None, {'status_code': 500, 'detail': f'{e}'}
