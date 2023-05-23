from bson import ObjectId
from pymongo import ReturnDocument
from pymongo.errors import ConnectionFailure
from starlette.status import HTTP_404_NOT_FOUND, HTTP_422_UNPROCESSABLE_ENTITY

from celery_app import app
from database import MongoConnection, MONGODB_URL, MONGO_INITDB_DATABASE

from schemas import ApprovalProcessStatus
from tasks.utils import (
    product_exists, sale_exists, offers_exists,
    change_approval_process_offers_status
)


@app.task(name='create_approval_process')
def create_approval_process_task(approval_process: dict) -> tuple[dict | None, dict | None]:
    """Добавление процесса согласования акционной продажи.

    Возвращает ApprovalProcess в виде словаря и словарь
    с кодом ошибки и описанием. При отсутствии один из элементов равен None.
    """
    try:
        with MongoConnection(MONGODB_URL, MONGO_INITDB_DATABASE) as mongo:
            if not product_exists(mongo.db, approval_process['product']['id']):
                return None, {'status_code': HTTP_422_UNPROCESSABLE_ENTITY,
                              'detail': 'Товар не найден'}
            if not sale_exists(mongo.db, approval_process['sale']['id']):
                return None, {'status_code': HTTP_422_UNPROCESSABLE_ENTITY,
                              'detail': 'Продажа не найдена'}
            for offer in approval_process['offers']:
                offer['_id'] = ObjectId(offer['_id'])
            offer_ids = [offer['_id'] for offer in approval_process['offers']]
            if not offers_exists(mongo.db, offer_ids):
                return None, {'status_code': HTTP_422_UNPROCESSABLE_ENTITY,
                              'detail': 'Одна или более акции не существуют'}
            existing_approval_process = mongo.db['approval_processes'].find_one(
                {'sale.id': approval_process['sale']['id']}
            )
            if existing_approval_process is not None:
                return None, {'status_code': HTTP_422_UNPROCESSABLE_ENTITY,
                              'detail': 'Процесс согласования продажи уже существует'}
            new_approval_process = mongo.db['approval_processes'].insert_one(approval_process)
            created_approval_process = mongo.db['approval_processes'].find_one(
                {'_id': new_approval_process.inserted_id}
            )
            created_approval_process['_id'] = str(created_approval_process['_id'])
            for offer in created_approval_process['offers']:
                offer['_id'] = str(offer['_id'])
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
            if approval_process is None:
                return None, {'status_code': HTTP_404_NOT_FOUND,
                              'detail': 'Процесс согласования не найден'}
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
                approval_process['_id'] = str(approval_process['_id'])
                for offer in approval_process['offers']:
                    offer['_id'] = str(offer['_id'])
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
                approval_process = mongo.db['approval_processes'].find_one({
                    'sale.id': sale_id}
                )
                if approval_process is None:
                    return None, {'status_code': HTTP_404_NOT_FOUND,
                                  'detail': 'Процесс согласования не найден'}
                updated_approval_process = mongo.db['approval_processes'].find_one_and_update(
                    {'_id': ObjectId(approval_process['_id'])},
                    {'$set': {'status': approval_process_status}},
                    return_document=ReturnDocument.AFTER,
                    session=session
                )
                error = change_approval_process_offers_status(
                    mongo.db,
                    session,
                    approval_process,
                    approval_process_status
                )
                if error is not None:
                    return None, error
                updated_approval_process['_id'] = str(updated_approval_process['_id'])
                for offer in updated_approval_process['offers']:
                    offer['_id'] = str(offer['_id'])
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
    skip_value = (page_number - 1) * page_size
    try:
        with MongoConnection(MONGODB_URL, MONGO_INITDB_DATABASE) as mongo:
            approval_process = mongo.db['approval_processes'].find_one({'sale.id': sale_id})
            if approval_process is None:
                return None, {'status_code': HTTP_404_NOT_FOUND,
                              'detail': 'Процесс согласования не найден'}
            if approval_process['status'] != ApprovalProcessStatus.APPROVED.value:
                return None, {'status_code': HTTP_422_UNPROCESSABLE_ENTITY,
                              'detail': 'Продажа товара не зафиксирована'}
            offer_ids = [ObjectId(offer['_id']) for offer in approval_process['offers']]
            approval_process_offers = list(mongo.db['offers'].find(
                {'_id': {'$in': offer_ids}},
                {'compatible_products': {'$slice': [skip_value, page_size]}}
            ))
            for offer in approval_process_offers:
                offer['_id'] = str(offer['_id'])
            return approval_process_offers, None
    except ConnectionFailure as e:
        return None, {'status_code': 500, 'detail': f'{e}'}
